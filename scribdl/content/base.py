from bs4 import BeautifulSoup
import requests
from abc import ABCMeta, abstractmethod
import six

from .. import internals


@six.add_metaclass(ABCMeta)
class ScribdBase:
    """
    A base class for Scribd books, documents and audiobooks.

    Parameters
    ----------
    url : `str`
        A string containing Scribd URL.
    """

    def __init__(self, url):
        self.url = url
        self._title = None
        self._sanitized_title = None
        self._hidden_soup = None

    @property
    def title(self):
        """
        Scrapes the title of the Scribd document.
        """
        if not self._title:
            title = self._soup.find("h1").get_text()
            # this unneed prefix may happen on textual books
            unneeded_prefix = "Currently Reading: "
            if title.startswith(unneeded_prefix):
                title = title[len(unneeded_prefix):]
            self._title = title
        return self._title

    @property
    def sanitized_title(self):
        """
        Remove special characters from title to make
        it suitable for filenames.
        """
        if not self._sanitized_title:
            self._sanitized_title = internals.sanitize_title(self.title)
        return self._sanitized_title

    @abstractmethod
    def download(self):
        """
        An abstract method for fetching content off Scribd book or document.
        """
        pass

    @property
    def _soup(self):
        """
        Parse HTML.
        """
        if not self._hidden_soup:
            response = requests.get(self.url)
            self._hidden_soup = BeautifulSoup(response.text, "html.parser")
        return self._hidden_soup
