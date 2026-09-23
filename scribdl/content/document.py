from bs4 import BeautifulSoup
import requests
import re

import os

from abc import abstractmethod
from .base import ScribdBase
from .. import internals

# Matches the 'window.page<N>_callback(["' wrapper, whatever the page number
JSONP_CALLBACK_PREFIX = re.compile(r'^\s*window\.page\d+_callback\(\["')


class ScribdDocument(ScribdBase):
    """
    A base class for downloading documents off Scribd.

    Parameters
    ----------
    url : `str`
        A string containing Scribd document URL.
    """

    def __init__(self, document_url, soup=None):
        super().__init__(document_url, soup)
        self._jsonp_urls = None

    @property
    def jsonp_urls(self):
        """
        Extracts all URLs ending with '.jsonp' by scanning script tags
        and data attributes in the page HTML.
        """
        if not self._jsonp_urls:
            found = []

            # Search all script tag contents (any type)
            for script in self._soup.find_all("script"):
                text = script.string or ""
                found.extend(re.findall(r'https?://[^\s"\'\\]+\.jsonp', text))

            # Search data-* attributes on any element (Scribd embeds asset
            # manifests in data-bookinfo, data-page, etc.)
            for tag in self._soup.find_all(True):
                for attr_val in tag.attrs.values():
                    if isinstance(attr_val, str):
                        found.extend(re.findall(r'https?://[^\s"\'\\]+\.jsonp', attr_val))

            # Deduplicate while preserving order
            seen = set()
            jsonp_urls = []
            for url in found:
                if url not in seen:
                    seen.add(url)
                    jsonp_urls.append(url)

            self._jsonp_urls = jsonp_urls
        return self._jsonp_urls

    @abstractmethod
    def download(self):
        """
        An abstract method which will fetch the actual content
        found in the '.jsonp' URLs.
        """
        pass


class ScribdTextualDocument(ScribdDocument):
    """
    A class for downloading textual documents off Scribd.

    Parameters
    ----------
    document_url : `str`
        A string containing Scribd document URL.
    """

    @property
    def filename(self):
        return self.sanitized_title + ".md"

    def download(self, filename=None):
        """
        Generates the filename and processes the text extraction
        to this file.
        """
        if not filename:
            filename = self.filename

        print("Extracting text to", self.sanitized_title, "\n")
        # Start from an empty file so re-runs don't duplicate content
        open(filename, "w", encoding="utf-8").close()
        self._text_extractor(filename)
        return filename

    def _text_extractor(self, filename):
        """
        Saves text from every '.jsonp' URL.
        """
        for jsonp_url in self.jsonp_urls:
            self._save_text(jsonp_url, filename)

    def _save_text(self, jsonp, filename):
        """
        Makes a GET request to the '.jsonp' URL and saves
        the text to the passed file.
        """
        response = requests.get(jsonp, timeout=internals.REQUEST_TIMEOUT).text

        response_head = (
            JSONP_CALLBACK_PREFIX.sub("", response, count=1)
            .replace("\\n", "")
            .replace("\\", "")
            .replace('"]);', "")
        )
        soup_content = BeautifulSoup(response_head, "html.parser")

        for x in soup_content.find_all("span", {"class": "a"}):
            xtext = x.get_text()
            print(xtext)

            extraction = xtext + "\n\n"
            with open(filename, "a", encoding="utf-8") as feed:
                feed.write(extraction)


class ScribdImageDocument(ScribdDocument):
    """
    A class for downloading image documents off Scribd.

    Parameters
    ----------
    document_url : `str`
        A string containing Scribd document URL.
    """

    def __init__(self, document_url, soup=None):
        super().__init__(document_url, soup)
        self._image_download_counter = 1

    def download(self, initial_filename=None):
        """
        Function for downloading images off '.jsonp' URLs to
        filenames.
        """
        if not initial_filename:
            initial_filename = self.sanitized_title

        downloaded_html_images = self._html_image_extractor(initial_filename)
        downloaded_jsonp_images = self._jsonp_image_extractor(initial_filename)
        return downloaded_html_images + downloaded_jsonp_images

    def _jsonp_image_extractor(self, initial_filename):
        """
        Extract images from extracted .jsonp URLs.
        """
        downloaded_images = []
        found = self._image_download_counter > 1
        for jsonp_url in self.jsonp_urls:
            filename = "{}_{}.jpg".format(initial_filename, self._image_download_counter)
            img_url = self._convert_jsonp_url_to_image_url(jsonp_url, found=found)
            self._save_image(img_url, filename)
            downloaded_images.append(filename)
            self._image_download_counter += 1
        return downloaded_images

    def _html_image_extractor(self, initial_filename):
        """
        Extracts images that are directly embedded in the original
        HTML page.
        """
        downloaded_images = []
        absimg = self._soup.find_all("img", {"class": "absimg"}, src=True)
        for img in absimg:
            filename = "{}_{}.jpg".format(initial_filename, self._image_download_counter)
            self._save_image(img["src"], filename)
            downloaded_images.append(filename)
            self._image_download_counter += 1
        return downloaded_images

    def _convert_jsonp_url_to_image_url(self, jsonp_url, found):
        """
        Gets the image URL corresponding to the '.jsonp' URL.
        """
        if jsonp_url.endswith(".jsonp"):
            replacement = jsonp_url.replace("/pages/", "/images/")
            if found:
                replacement = replacement.replace(".jsonp", "/000.jpg")
            else:
                replacement = replacement.replace(".jsonp", ".jpg")
        else:
            replacement = jsonp_url
        return replacement

    def _save_image(self, url, imagename):
        """
        Skips downloading if the image is already downloaded,
        otherwise downloads it locally.
        """
        print("Downloading", imagename)
        already_present = os.listdir(".")
        if imagename in already_present:
            return
        internals.download_stream(url, imagename)
