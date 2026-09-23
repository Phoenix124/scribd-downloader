from ..downloader import Downloader
import os

import pytest


@pytest.fixture
def cwd_to_tmpdir(tmpdir):
    os.chdir(str(tmpdir))


def test_text_document_download(cwd_to_tmpdir):
    text_doc_url = "https://www.scribd.com/document/96882378/Trademark-License-Agreement"
    text_downloader = Downloader(text_doc_url)
    md_doc = text_downloader.download(is_image_document=False)
    # Short documents have all their pages embedded in the HTML page
    assert os.path.getsize(md_doc.input_content) in range(7000, 9000)
    md_doc.to_pdf()
    assert os.path.getsize(md_doc.pdf_path) in range(20000, 40000)


def test_img_document_download(cwd_to_tmpdir):
    img_doc_url = "https://www.scribd.com/doc/136711944/Signature-Scanning-and-Verification-in-Finacle"
    img_downloader = Downloader(img_doc_url)
    imgs = img_downloader.download(is_image_document=True)
    assert len(imgs.input_content) == 5
    imgs.to_pdf()
    assert os.path.getsize(imgs.pdf_path) in range(350000, 450000)
