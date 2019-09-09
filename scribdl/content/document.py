from bs4 import BeautifulSoup
import requests

import os

from abc import abstractmethod
from .base import ScribdBase
from .. import internals


class ScribdDocument(ScribdBase):
    """
    A base class for downloading documents off Scribd.

    Parameters
    ----------
    url : `str`
        A string containing Scribd document URL.
    """

    def __init__(self, document_url):
        super().__init__(document_url)
        self.url = document_url
        self._jsonp_urls = None
        self._hidden_soup = None

    @property
    def jsonp_urls(self):
        """
        Extracts all URLs ending with '.jsonp' by parsing the
        HTML code.
        """
        if not self._jsonp_urls:
            js_text = self._soup.find_all("script", type="text/javascript")
            jsonp_urls = []
            for opening in js_text:
                for inner_opening in opening:
                    jsonp = self._extract_jsonp_url(inner_opening)
                    if jsonp:
                        jsonp_urls.append(jsonp)
            self._jsonp_urls = jsonp_urls
        return self._jsonp_urls

    def _extract_jsonp_url(self, inner_opening):
        """
        Extracts URLs ending with '.jsonp'. These URLs contain the
        raw document text.
        """
        portion1 = inner_opening.find("https://")

        if portion1 == -1:
            jsonp = None
        else:
            portion2 = inner_opening.find(".jsonp")
            jsonp = inner_opening[portion1 : portion2 + 6]

        return jsonp

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

    def __init__(self, document_url):
        super().__init__(document_url)
        self.filename = self.sanitized_title + ".md"

    def download(self, filename=None):
        """
        Generates the filename and processes the text extraction
        to this file.
        """
        if not filename:
            filename = self.filename

        print("Extracting text to", self.sanitized_title, "\n")
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
        response = requests.get(jsonp).text
        page_no = response[11:12]

        response_head = (
            (response)
            .replace("window.page" + page_no + '_callback(["', "")
            .replace("\\n", "")
            .replace("\\", "")
            .replace('"]);', "")
        )
        soup_content = BeautifulSoup(response_head, "html.parser")

        for x in soup_content.find_all("span", {"class": "a"}):
            xtext = internals.fix_encoding(x.get_text())
            print(xtext)

            extraction = xtext + "\n\n"
            with open(filename, "a") as feed:
                feed.write(extraction)


class ScribdImageDocument(ScribdDocument):
    """
    A class for downloading image documents off Scribd.

    Parameters
    ----------
    document_url : `str`
        A string containing Scribd document URL.
    """

    def __init__(self, document_url):
        super().__init__(document_url)
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
