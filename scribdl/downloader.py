from .content.document import ScribdTextualDocument
from .content.document import ScribdImageDocument
from .content import everand

from .pdf_converter import ConvertToPDF


class Downloader:
    """
    A helper class for downloading Scribd documents and Everand
    books and audiobooks.

    Parameters
    ----------
    url : `str`
        A string containing a Scribd or Everand URL. Scribd book and
        audiobook URLs are downloaded from Everand, where they have moved.
    credentials_file : `str`
        Optional path to a file with Everand credentials, used for
        Everand audiobooks
    """

    def __init__(self, url, credentials_file=None):
        self.url = url
        self.credentials_file = credentials_file
        self.everand_url = everand.to_everand_url(url)

    def download(self, is_image_document=None, max_pages=0, epub=False):
        """
        Downloads documents from Scribd and books and audiobooks from Everand.
        Returns an object of `ConvertToPDF` class (None for audiobooks).

        `max_pages` and `epub` apply to Everand books: stop after that many
        pages (0 = all) and save as EPUB instead of PDF.
        """
        if self.everand_url is not None:
            return self._download_everand(max_pages, epub)

        if is_image_document is None:
            raise TypeError(
                "The input URL points to a document. You must specify "
                "whether it is an image document or a textual document "
                "in the `image_document` parameter."
            )
        return self._download_document(is_image_document)

    def _download_everand(self, max_pages, epub):
        """
        Downloads Everand books as PDF or EPUB (returns an object of
        `ConvertToPDF` class) and Everand audiobooks (returns None).
        """
        kind, _, _ = everand.parse_everand_url(self.everand_url)
        if kind in everand.AUDIOBOOK_KINDS:
            everand.EverandAudioBook(self.everand_url, self.credentials_file).download()
            return None
        path = everand.EverandBook(self.everand_url).download(max_pages=max_pages, epub=epub)
        return ConvertToPDF(path, path)

    def _download_document(self, image_document):
        """
        Downloads textual and image documents off Scribd.
        Returns an object of `ConvertToPDF` class.
        """
        if image_document:
            document = ScribdImageDocument(self.url)
        else:
            document = ScribdTextualDocument(self.url)

        content_path = document.download()
        pdf_path = "{}.pdf".format(document.sanitized_title)
        return ConvertToPDF(content_path, pdf_path)
