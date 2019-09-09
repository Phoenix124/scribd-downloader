from .. import internals

import pytest


SANITIZE_TITLE_TEST_TABLE = [
    ("good_title", "good_title"),
    ("*bla", "_bla"),
    ("**free_as_in_<freedom>**", "__free_as_in__freedom___"),
    ("troller*\"/\<>:|(haha)jojo", "troller_________haha_jojo"),
]

@pytest.mark.parametrize("input_str, expected_str", SANITIZE_TITLE_TEST_TABLE)
def test_sanitize_title(input_str, expected_str):
    assert internals.sanitize_title(input_str) == expected_str
