"""
Writes rendered Everand pages into a fixed-layout EPUB 3.

Every page keeps the look of the PDF: the reader positions each text line
absolutely, so the text can't be reflowed. Fonts and images embedded as
data URIs are moved into files of their own and shared between pages.
"""

import base64
import hashlib
import re
import time
import uuid
import zipfile
from xml.sax.saxutils import escape

_DATA_URI = re.compile(r"data:([\w/+.-]+);base64,([A-Za-z0-9+/=]+)")

_EXTENSIONS = {
    "font/ttf": "ttf",
    "font/otf": "otf",
    "font/woff": "woff",
    "font/woff2": "woff2",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/svg+xml": "svg",
}

_CONTAINER = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

_PAGE = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width={width}, height={height}"/>
<title>{title}</title>
<link rel="stylesheet" type="text/css" href="../style.css"/>
<style>html,body{{width:{width}px;height:{height}px;margin:0;padding:0;overflow:hidden}}</style>
</head>
{body}
</html>
"""

_NAV = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><meta charset="utf-8"/><title>{title}</title></head>
<body>
<nav epub:type="toc"><ol><li><a href="pages/page00001.xhtml">{title}</a></li></ol></nav>
</body>
</html>
"""

_PACKAGE = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">urn:uuid:{identifier}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:language>und</dc:language>
    <meta property="dcterms:modified">{modified}</meta>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:spread">none</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="style" href="style.css" media-type="text/css"/>
{items}
  </manifest>
  <spine>
{itemrefs}
  </spine>
</package>
"""


class _Resources:
    """
    Collects the files extracted from data URIs, named by content hash.
    """

    def __init__(self):
        self.files = {}

    def extract(self, text, prefix):
        """
        Replaces the data URIs in `text` with `prefix` + the path of their file.
        """
        def replace(match):
            media_type = match.group(1)
            data = base64.b64decode(match.group(2))
            folder = "fonts" if media_type.startswith("font/") else "images"
            path = "{}/{}.{}".format(folder, hashlib.md5(data).hexdigest(), _EXTENSIONS.get(media_type, "bin"))
            self.files[path] = (media_type, data)
            return prefix + path
        return _DATA_URI.sub(replace, text)


def write_epub(pages, css, title, output_path):
    """
    Writes `pages`, a list of (xhtml body, width, height) tuples, and the
    shared `css` into a fixed-layout EPUB at `output_path`.
    """
    resources = _Resources()
    css = resources.extract(css, "")
    documents = []
    for number, (body, width, height) in enumerate(pages, 1):
        body = resources.extract(body, "../")
        documents.append(("pages/page{:05d}.xhtml".format(number),
                          _PAGE.format(width=width, height=height, title=escape(title), body=body)))

    items = ['    <item id="page{0}" href="{1}" media-type="application/xhtml+xml"/>'.format(number, path)
             for number, (path, _) in enumerate(documents, 1)]
    items += ['    <item id="res{0}" href="{1}" media-type="{2}"/>'.format(number, path, media_type)
              for number, (path, (media_type, _)) in enumerate(sorted(resources.files.items()), 1)]
    itemrefs = ['    <itemref idref="page{}"/>'.format(number) for number in range(1, len(documents) + 1)]
    package = _PACKAGE.format(
        identifier=uuid.uuid4(),
        title=escape(title),
        modified=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        items="\n".join(items),
        itemrefs="\n".join(itemrefs),
    )

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as epub:
        # The mimetype must come first and stay uncompressed
        epub.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        epub.writestr("META-INF/container.xml", _CONTAINER)
        epub.writestr("OEBPS/content.opf", package)
        epub.writestr("OEBPS/nav.xhtml", _NAV.format(title=escape(title)))
        epub.writestr("OEBPS/style.css", css)
        for path, document in documents:
            epub.writestr("OEBPS/" + path, document)
        for path, (_, data) in resources.files.items():
            epub.writestr("OEBPS/" + path, data)
