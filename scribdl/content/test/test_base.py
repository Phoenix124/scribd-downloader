from .. import base

import pytest


def test_abstract_class():
    with pytest.raises(TypeError):
        x = base.ScribdBase()


class ScribdBaseTop(base.ScribdBase):
    def download(self):
        pass


class TestScribdBase:
    @pytest.fixture(scope="class")
    def scribd_base(self):
        return ScribdBaseTop(
            "https://www.scribd.com/document/55949937/33-Strategies-of-War")

    def test_title(self, scribd_base):
        assert scribd_base.title == "33 Strategies of War Overview"

    def test_sanitized_title(self, scribd_base):
        assert scribd_base.sanitized_title == "33_Strategies_of_War_Overview"
