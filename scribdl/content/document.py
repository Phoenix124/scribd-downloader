from bs4 import BeautifulSoup
import requests
import re

import os

from abc import abstractmethod
from .base import ScribdBase
from .. import internals

# Matches the 'window.page<N>_callback(["' wrapper, whatever the page number
JSONP_CALLBACK_PREFIX = re.compile(r'^\s*window\.page\d+_callback\(\["')

# Page image URL of an <img class="absimg" orig="..."> tag, escaped or not
ORIG_IMAGE_URL = re.compile(r'orig=\\?"(https?://[^"\\]+)')


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
        Saves text of the pages embedded in the HTML page (short
        documents have all their pages there) and from every
        '.jsonp' URL.
        """
        self._write_spans(self._soup, filename)
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
        self._write_spans(soup_content, filename)

    def _write_spans(self, soup, filename):
        """
        Appends the text of every page text span to the passed file.
        """
        for x in soup.find_all("span", {"class": "a"}):
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

    def download(self, initial_filename=None):
        """
        Function for downloading page images to filenames.
        """
        if not initial_filename:
            initial_filename = self.sanitized_title

        image_urls = self._html_image_urls()
        for jsonp_url in self.jsonp_urls:
            image_urls.extend(self._jsonp_image_urls(jsonp_url))

        downloaded_images = []
        seen = set()
        for url in image_urls:
            if url in seen:
                continue
            seen.add(url)
            extension = os.path.splitext(url)[1] or ".jpg"
            filename = "{}_{}{}".format(initial_filename, len(downloaded_images) + 1, extension)
            self._save_image(url, filename)
            downloaded_images.append(filename)
        return downloaded_images

    def _html_image_urls(self):
        """
        Image URLs of the pages embedded in the HTML page.
        """
        urls = []
        for img in self._soup.find_all("img", {"class": "absimg"}):
            url = img.get("orig") or img.get("src")
            if url:
                urls.append(self._secure_url(url))
        return urls

    def _jsonp_image_urls(self, jsonp_url):
        """
        Image URLs referenced by the '.jsonp' page. Falls back to
        guessing the URL from the '.jsonp' one.
        """
        response = requests.get(jsonp_url, timeout=internals.REQUEST_TIMEOUT).text
        urls = [self._secure_url(url) for url in ORIG_IMAGE_URL.findall(response)]
        if not urls:
            urls = [jsonp_url.replace("/pages/", "/images/").replace(".jsonp", ".jpg")]
        return urls

    @staticmethod
    def _secure_url(url):
        if url.startswith("http://"):
            url = "https://" + url[len("http://"):]
        return url

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
