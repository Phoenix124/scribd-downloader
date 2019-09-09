from .. import audiobook
from ... import exceptions

import pytest


@pytest.fixture(scope="module")
def scribd_audiobook():
    return audiobook.ScribdAudioBook(
        "https://www.scribd.com/audiobook/237606860/100-Ways-to-Motivate-Yourself-Change-Your-Life-Forever")


class TestScribdAudioBook:
    def test_title(self, scribd_audiobook):
        assert scribd_audiobook.title == "100 Ways to Motivate Yourself: Change Your Life Forever"

    def test_sanitized_title(self, scribd_audiobook):
        assert scribd_audiobook.sanitized_title == "100_Ways_to_Motivate_Yourself__Change_Your_Life_Forever"

    def test_preview_url(self, scribd_audiobook):
        assert scribd_audiobook.preview_url == "https://samples.findawayworld.com/19991/19991_sample.mp3"

    def test_scribd_id(self, scribd_audiobook):
        assert scribd_audiobook.scribd_id == "237606860"

    def test_authenticate_url(self, scribd_audiobook):
        assert scribd_audiobook.authenticate_url == "https://www.scribd.com/listen/237606860"

    def test_author_id(self, scribd_audiobook):
        assert scribd_audiobook.author_id == None

    def test_book_id(self, scribd_audiobook):
        assert scribd_audiobook.book_id == "19991"

    def test_playlist_url(self, scribd_audiobook):
        assert scribd_audiobook.playlist_url == "https://api.findawayworld.com/v4/audiobooks/19991/playlists"

    def test_premium_cokies(self, scribd_audiobook):
        assert scribd_audiobook.premium_cookies == False

    def test_license_url(self, scribd_audiobook):
        assert scribd_audiobook.license_url == "https://api.findawayworld.com/v4/accounts/scribd-None/audiobooks/19991"

    def test_license_id(self, scribd_audiobook):
        assert scribd_audiobook.license_id == None


class TestPlaylist:
    def test_playlist_instance(self, scribd_audiobook):
        assert isinstance(scribd_audiobook.playlist, audiobook.Playlist)

    def test_playlist_title(self, scribd_audiobook):
        assert scribd_audiobook.playlist.title == "100 Ways to Motivate Yourself: Change Your Life Forever"

    def test_playlist_sanitized_title(self, scribd_audiobook):
        assert scribd_audiobook.playlist.sanitized_title == "100_Ways_to_Motivate_Yourself__Change_Your_Life_Forever"

    def test_playlist_raw_content(self, scribd_audiobook):
        raw_content = {'expires': None,
                       'playlist': [{'chapter_number': 'preview',
                                     'part_number': 'preview',
                                     'url': 'https://samples.findawayworld.com/19991/19991_sample.mp3'}],
                       'playlist_token': None}
        assert scribd_audiobook.playlist._playlist == raw_content


class TestTrack:
    def test_track_instance(self, scribd_audiobook):
        assert isinstance(scribd_audiobook.playlist.tracks[0], audiobook.Track)

    def test_track_count(self, scribd_audiobook):
        assert len(scribd_audiobook.playlist.tracks) == 1

    def test_track_url(self, scribd_audiobook):
        assert scribd_audiobook.playlist.tracks[0].url == "https://samples.findawayworld.com/19991/19991_sample.mp3"

    def test_track_part_number(self, scribd_audiobook):
        assert scribd_audiobook.playlist.tracks[0].part_number == "preview"

    def test_track_chapter_number(self, scribd_audiobook):
        assert scribd_audiobook.playlist.tracks[0].chapter_number == "preview"

    def test_track_raw_content(self, scribd_audiobook):
        raw_content = {'chapter_number': 'preview',
                       'part_number': 'preview',
                       'url': 'https://samples.findawayworld.com/19991/19991_sample.mp3'}
        assert scribd_audiobook.playlist.tracks[0]._track == raw_content
