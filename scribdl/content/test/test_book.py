from .. import book

import pytest


@pytest.fixture(scope="module")
def scribd_book():
    return book.ScribdBook(
        "https://www.scribd.com/read/189087235/Confessions-of-a-Casting-Director-Help-Actors-Land-Any-Role-with-Secrets-from-Inside-the-Audition-Room")


class TestScribdBook:
    def test_title(self, scribd_book):
        assert scribd_book.title == "Confessions of a Casting Director: Help Actors Land Any Role with Secrets from Inside the Audition Room"

    def test_sanitized_title(self, scribd_book):
        assert scribd_book.sanitized_title == "Confessions_of_a_Casting_Director__Help_Actors_Land_Any_Role_with_Secrets_from_Inside_the_Audition_Room"

    def test_filename(self, scribd_book):
        assert scribd_book.filename == "Confessions_of_a_Casting_Director__Help_Actors_Land_Any_Role_with_Secrets_from_Inside_the_Audition_Room.md"

    def test_book_id(self, scribd_book):
        assert scribd_book.book_id == 189087235

    def test_url(self, scribd_book):
        assert scribd_book.url == "https://www.scribd.com/read/189087235/Confessions-of-a-Casting-Director-Help-Actors-Land-Any-Role-with-Secrets-from-Inside-the-Audition-Room"
