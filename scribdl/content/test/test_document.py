from .. import document

import pytest 


@pytest.fixture(scope="module")
def scribd_textual_document():
    return document.ScribdTextualDocument(
        "https://www.scribd.com/document/55949937/33-Strategies-of-War")


@pytest.fixture(scope="module")
def scribd_image_document():
    return document.ScribdImageDocument(
        "https://scribd.com/doc/17142797/Case-in-Point")


class TestScribdTextualDocument:
    def test_title(self, scribd_textual_document):
        assert scribd_textual_document.title == "33 Strategies of War"

    def test_sanitized_title(self, scribd_textual_document):
        assert scribd_textual_document.sanitized_title == "33_Strategies_of_War"

    def test_url(self, scribd_textual_document):
        assert scribd_textual_document.url == "https://www.scribd.com/document/55949937/33-Strategies-of-War"

    def test_jsonp_urls(self, scribd_textual_document):
        assert len(scribd_textual_document.jsonp_urls) == 19


class TestScribdImageDocument:
    def test_title(self, scribd_image_document):
        assert scribd_image_document.title == "Case in Point"

    def test_sanitized_title(self, scribd_image_document):
        assert scribd_image_document.sanitized_title == "Case_in_Point"

    def test_url(self, scribd_image_document):
        assert scribd_image_document.url == "https://scribd.com/doc/17142797/Case-in-Point"

    def test_jsonp_urls(self, scribd_image_document):
        assert len(scribd_image_document.jsonp_urls) == 182
