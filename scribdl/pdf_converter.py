from md2pdf.core import md2pdf
import img2pdf
import os


class ConvertToPDF:
    """
    A class for converting downloading books and documents to PDF.

    Parameters
    ----------
    input_content : `str`, `list`
        A string containing path to a single markdown file
        or a list containing paths to many images.
    output_content : `str`
        Output path of the generated PDF.
    """

    def __init__(self, input_content, output_path):
        self.input_content = input_content
        self.pdf_path = output_path

    def to_pdf(self):
        """
        Converts to PDF depending upon the type of content,
        i.e. images or markdown.
        """
        if isinstance(self.input_content, list):
            self._images_to_pdf()
        else:
            self._markdown_to_pdf()

    def _markdown_to_pdf(self):
        """
        Converts markdown to PDF.
        """
        md2pdf(self.pdf_path,
               md_file_path=self.input_content,
               base_url=os.getcwd())

    def _images_to_pdf(self):
        """
        Converts images to PDF.
        """
        with open(self.pdf_path, "wb") as f:
            open_images = [open(img, "rb") for img in self.input_content]
            pdf_images = img2pdf.convert(open_images)
            f.write(pdf_images)
