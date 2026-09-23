from .. import everand
from ... import exceptions
from ...downloader import Downloader
from ...everand.capture import parse_counter

import pytest


BOOK_URL = "https://www.everand.com/read/813249861/Sleep-Change-the-way-you-sleep-with-this-90-minute-read"
AUDIOBOOK_URL = "https://www.everand.com/audiobook/237606860/100-Ways-to-Motivate-Yourself-Change-Your-Life-Forever"


class TestParseEverandUrl:
    def test_read(self):
        assert everand.parse_everand_url(BOOK_URL) == (
            "read", 813249861, "Sleep-Change-the-way-you-sleep-with-this-90-minute-read")

    def test_without_slug(self):
        assert everand.parse_everand_url("https://everand.com/book/813249861") == ("book", 813249861, None)

    def test_scribd(self):
        assert everand.parse_everand_url("https://www.scribd.com/read/813249861/Sleep") is None


class TestEverandBook:
    def test_title(self):
        book = everand.EverandBook(BOOK_URL)
        assert book.title == "Sleep Change the way you sleep with this 90 minute read"
        assert book.filename == "Sleep_Change_the_way_you_sleep_with_this_90_minute_read.pdf"

    def test_encoded_title(self):
        book = everand.EverandBook("https://www.everand.com/book/1/Caf%C3%A9-Stories")
        assert book.title == "Café Stories"

    def test_title_without_slug(self):
        assert everand.EverandBook("https://www.everand.com/book/813249861").title == "813249861"

    def test_reader_url(self):
        book = everand.EverandBook("https://www.everand.com/book/813249861/Sleep")
        assert book.reader_url == "https://www.everand.com/read/813249861/Sleep"

    def test_rejects_audiobook(self):
        with pytest.raises(exceptions.ScribdFetchError, match="Unsupported"):
            everand.EverandBook(AUDIOBOOK_URL)


class TestEverandAudioBook:
    def test_command(self):
        audiobook = everand.EverandAudioBook(AUDIOBOOK_URL)
        assert audiobook.command() == ["audiobook-dl", "https://www.everand.com/listen/237606860"]

    def test_command_with_credentials(self, tmpdir):
        credentials = tmpdir.join("credentials.txt")
        credentials.write("user@mail.com\npassword\n")
        audiobook = everand.EverandAudioBook(AUDIOBOOK_URL, str(credentials))
        assert audiobook.command() == [
            "audiobook-dl", "--username", "user@mail.com", "--password", "password",
            "https://www.everand.com/listen/237606860"]

    def test_missing_audiobook_dl(self, monkeypatch):
        monkeypatch.setattr(everand.shutil, "which", lambda name: None)
        with pytest.raises(exceptions.ScribdFetchError, match="audiobook-dl"):
            everand.EverandAudioBook(AUDIOBOOK_URL).download()


class TestDownloaderRouting:
    def test_book(self, monkeypatch):
        monkeypatch.setattr(everand.EverandBook, "download", lambda self: "Sleep.pdf")
        content = Downloader(BOOK_URL).download()
        assert content.input_content == content.pdf_path == "Sleep.pdf"
        # Already a PDF, nothing to convert
        content.to_pdf()

    def test_audiobook(self, monkeypatch):
        calls = []
        monkeypatch.setattr(everand.EverandAudioBook, "download", lambda self: calls.append(self.listen_url))
        assert Downloader(AUDIOBOOK_URL).download() is None
        assert calls == ["https://www.everand.com/listen/237606860"]


def test_parse_counter():
    assert parse_counter("PAGE 103 OF 243") == (103, 243)
    assert parse_counter("page 1 of 2") == (1, 2)
    assert parse_counter("") == (None, None)
