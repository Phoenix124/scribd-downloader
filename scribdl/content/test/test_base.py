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
            "https://www.scribd.com/audiobook/367877343/Intelligence-in-Nature-An-Inquiry-into-Knowledge")

    def test_title(self, scribd_base):
        assert scribd_base.title == "Intelligence in Nature: An Inquiry into Knowledge"

    def test_sanitized_title(self, scribd_base):
        assert scribd_base.sanitized_title == "Intelligence_in_Nature__An_Inquiry_into_Knowledge"
