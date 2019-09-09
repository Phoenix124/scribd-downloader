from ..downloader import Downloader
import os

import pytest


@pytest.fixture
def cwd_to_tmpdir(tmpdir):
    os.chdir(str(tmpdir))


def test_audiobook_download(cwd_to_tmpdir, monkeypatch):
    audiobook_url = "https://www.scribd.com/audiobook/237606860/100-Ways-to-Motivate-Yourself-Change-Your-Life-Forever"
    audiobook_downloader = Downloader(audiobook_url)
    audio = audiobook_downloader.download()
    assert audio[0] == "100_Ways_to_Motivate_Yourself__Change_Your_Life_Forever_preview.mp3"
    assert os.path.getsize(audio[0]) == 2127830


def test_text_document_download(cwd_to_tmpdir):
    text_doc_url = "https://www.scribd.com/document/96882378/Trademark-License-Agreement"
    text_downloader = Downloader(text_doc_url)
    md_doc = text_downloader.download(is_image_document=False)
    assert os.path.getsize(md_doc.input_content) in range(1000, 2000)
    md_doc.to_pdf()
    assert os.path.getsize(md_doc.pdf_path) in range(20000, 31000)


def test_img_document_download(cwd_to_tmpdir):
    img_doc_url = "https://www.scribd.com/doc/136711944/Signature-Scanning-and-Verification-in-Finacle"
    img_downloader = Downloader(img_doc_url)
    imgs = img_downloader.download(is_image_document=True)
    assert len(imgs.input_content) == 2
    imgs.to_pdf()
    assert os.path.getsize(imgs.pdf_path) in range(140000, 150000)


def test_book_download(cwd_to_tmpdir, monkeypatch):
    book_url = "https://www.scribd.com/read/262694921/Acting-The-First-Six-Lessons"
    book_downloader = Downloader(book_url)
    # We don't want to clutter stdout with book contents if this test fails
    monkeypatch.setattr("builtins.print", lambda x: None)
    md_book = book_downloader.download()
    assert os.path.getsize(md_book.input_content) in range(10000, 20000)
    md_book.to_pdf()
    assert os.path.getsize(md_book.pdf_path) in range(200000, 2500000)

