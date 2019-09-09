import requests
import json
import os

from .base import ScribdBase
from .. import internals
from .. import const


class ScribdBook(ScribdBase):
    """
    A class for downloading books off Scribd.

    Parameters
    ----------
    url : `str`
        A string containing Scribd book URL.
    """

    def __init__(self, book_url):
        super().__init__(book_url)
        self.filename = self.sanitized_title + ".md"
        self.url = book_url
        self._book_id = None
        self._csrf_token = None

    @property
    def book_id(self):
        """
        Extracts the book ID.
        """
        if not self._book_id:
            splits = self.url.split("/")
            for split in splits:
                try:
                    book_id = int(split)
                except ValueError:
                    continue
            self._book_id = book_id
        return self._book_id

    @property
    def csrf_token_header(self):
        """
        CSRF-Token is used to gain access to premium content
        in textual books premium content of audiobooks can still
        be downloaded without it though.
        """
        if not self._csrf_token:
            csrf_token_url = "https://scribd.com/csrf_token"
            response = requests.get(csrf_token_url, cookies=const.premium_cookies)
            json_dict = json.loads(response.text)
            self._csrf_token = {"X-CSRF-Token": json_dict["csrf_token"]}
        return self._csrf_token

    def download(self, filename=None):
        """
        Processing text and image extraction.
        """
        if not filename:
            filename = self.filename

        token = self._get_token()
        chapter = 1

        while True:
            response = self.fetch_response(chapter, token)

            if response.status_code == 403:
                token = self._get_token()
                response = self.fetch_response(chapter, token)

                if response.status_code == 403:
                    print("No more content being exposed by Scribd!")
                    break

            try:
                json_response = json.loads(response.text)
            except ValueError:
                print("Completed downloading book!")
                break

            self._extract_text_blocks(json_response, chapter, token, filename)

            chapter += 1

        return filename

    def _extract_text(self, content, chapter, token):
        """
        Extracts text given a block of raw html.
        """
        words = []
        for word in content["words"]:
            if word.get("break_map", None):
                words.append(word["break_map"]["text"])
            elif word.get("text", None):
                words.append(word["text"])
            elif word.get("type", None) == "image":
                image_url = self._format_image_url(chapter, word["src"], token)
                string_text = self._process_image_text(word, image_url)
                words.append(string_text)
            else:
                words += self._extract_text(word, chapter, token)
        return words

    def fetch_response(self, chapter, token):
        url = self._format_content_url(chapter, token)
        response = requests.get(url)
        return response

    def _extract_text_blocks(self, response_dict, chapter, token, filename):
        """
        Extracts small blocks of raw book text and image
        URLs and writes them to a file.
        """
        for block in response_dict["blocks"]:
            if block["type"] == "text":
                string_text = (
                    " ".join(self._extract_text(block, chapter, token)) + "\n\n"
                )
            elif block["type"] == "image":
                image_url = self._format_image_url(chapter, block["src"], token)
                string_text = self._process_image_text(block, image_url)

            if block["type"] in ("text", "image"):
                print(string_text)
                self.save_text(string_text, filename)

    def _process_image_text(self, block, image_url):
        image_name = block["src"].replace("images/", "")
        image_path = os.path.join(self.sanitized_title, image_name)
        self._download_image(image_url, image_path)
        string_text = "![{}]({})\n\n".format(image_name, image_path)
        return string_text

    def _download_image(self, url, path):
        try:
            os.makedirs(os.path.dirname(path))
        except OSError:
            pass
        internals.download_stream(url, path)

    def _extract_image_path_from_url(self, url):
        image_name = url.split("/")[-1].split("?token=")[0]
        return os.path.join(self.book_id, image_name)

    def _format_content_url(self, chapter, token):
        """
        Generates a string which points to a URL containing
        the raw book text.
        """
        unformatted_url = (
            "https://www.scribd.com/scepub/{}/chapters/{}/contents.json?token={}"
        )
        return unformatted_url.format(self.book_id, chapter, token)

    def _format_image_url(self, chapter, image, token):
        """
        Generates a string which points to an image URL.
        """
        unformatted_url = "https://www.scribd.com/scepub/{}/chapters/{}/{}?token={}"
        return unformatted_url.format(self.book_id, chapter, image, token)

    def _get_token(self):
        """
        Fetches a uniquely generated token for the current
        session.
        """
        # data can take take any value but it must take some value
        # otherwise Scribd will reject the request
        data = "data"

        token_url = "https://www.scribd.com/read2/{}/access_token".format(self.book_id)
        token = requests.post(token_url,
                              headers=self.csrf_token_header,
                              cookies=const.premium_cookies,
                              data=data)
        return json.loads(token.text)["response"]

    def save_text(self, string_text, filename):
        """
        Appends text to the passed file.
        """
        with open(filename, "a") as f:
            f.write(string_text)
