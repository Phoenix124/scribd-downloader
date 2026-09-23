import base64
import zipfile
from xml.etree import ElementTree

from .. import epub

FONT = base64.b64encode(b"font bytes").decode("ascii")
IMAGE = base64.b64encode(b"image bytes").decode("ascii")

CSS = "@font-face{font-family:'Book';src:url('data:font/ttf;base64,%s')}" % FONT
PAGES = [
    ('<body xmlns="http://www.w3.org/1999/xhtml"><img src="data:image/jpeg;base64,%s"/></body>' % IMAGE, 600, 900),
    ('<body xmlns="http://www.w3.org/1999/xhtml"><span class="text_line">Text &amp; more</span>'
     '<img src="data:image/jpeg;base64,%s"/></body>' % IMAGE, 500, 800),
]


def _write(tmpdir):
    path = str(tmpdir.join("book.epub"))
    epub.write_epub(PAGES, CSS, "Sleep & Rest", path)
    return zipfile.ZipFile(path)


def test_layout(tmpdir):
    with _write(tmpdir) as book:
        names = book.namelist()
        assert names[0] == "mimetype"
        assert book.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        assert book.read("mimetype") == b"application/epub+zip"
        assert "OEBPS/pages/page00001.xhtml" in names
        assert "OEBPS/pages/page00002.xhtml" in names


def test_resources_extracted_once(tmpdir):
    with _write(tmpdir) as book:
        fonts = [n for n in book.namelist() if n.startswith("OEBPS/fonts/")]
        images = [n for n in book.namelist() if n.startswith("OEBPS/images/")]
        assert len(fonts) == 1 and book.read(fonts[0]) == b"font bytes"
        assert len(images) == 1 and book.read(images[0]) == b"image bytes"
        assert "data:" not in book.read("OEBPS/style.css").decode()
        assert "url('fonts/" in book.read("OEBPS/style.css").decode()
        assert 'src="../images/' in book.read("OEBPS/pages/page00002.xhtml").decode()


def test_well_formed(tmpdir):
    with _write(tmpdir) as book:
        for name in book.namelist():
            if name.endswith((".xhtml", ".opf", ".xml")):
                ElementTree.fromstring(book.read(name))


def test_package(tmpdir):
    with _write(tmpdir) as book:
        package = book.read("OEBPS/content.opf").decode()
        assert "<dc:title>Sleep &amp; Rest</dc:title>" in package
        assert '<meta property="rendition:layout">pre-paginated</meta>' in package
        assert package.count("<itemref ") == 2
        page = book.read("OEBPS/pages/page00001.xhtml").decode()
        assert 'content="width=600, height=900"' in page
