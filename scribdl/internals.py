import requests
import shutil

from . import exceptions

# Seconds to wait for Scribd before giving up on a request
REQUEST_TIMEOUT = 30


def check_bot_challenge(response):
    """
    Raises a clear error when Scribd answers with its JavaScript
    "Client Challenge" page instead of the requested content.
    """
    if "<title>Client Challenge</title>" in response.text:
        raise exceptions.ScribdFetchError(
            "Scribd blocked the automated request with a browser check "
            "(\"Client Challenge\" page). Downloading does not currently work "
            "with Scribd: {}".format(response.url)
        )


def check_page_response(response):
    """
    Raises a clear error when a Scribd page can't be used: a browser
    check, a redirect to Everand (where Scribd moved books and
    audiobooks) or an HTTP error.
    """
    check_bot_challenge(response)
    if "everand.com" in response.url:
        raise exceptions.ScribdFetchError(
            "Scribd redirected to Everand, where books and audiobooks have moved. "
            "Download it from Everand instead: scribdl {}".format(response.url)
        )
    if response.status_code >= 400:
        raise exceptions.ScribdFetchError(
            "Scribd returned HTTP {} for {}".format(response.status_code, response.url)
        )


def sanitize_title(title):
    """
    Remove forbidden characters from title that will prevent Windows
    from creating directory.

    Also change ' ' to '_' to preserve previous behavior.
    """
    forbidden_chars = ' *"/\\<>:|(),'
    replace_char = "_"

    for ch in forbidden_chars:
        title = title.replace(ch, replace_char)

    return title


def download_stream(url, filepath):
    """
    Stream stuff from the Internet to a local file.
    """
    response = requests.get(url, stream=True, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    response.raw.decode_content = True
    with open(filepath, "wb") as out_file:
        shutil.copyfileobj(response.raw, out_file)
