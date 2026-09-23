import requests
import shutil

GITHUB_URL_BASE = "https://github.com/ritiek/scribd-downloader"

# Seconds to wait for Scribd before giving up on a request
REQUEST_TIMEOUT = 30


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
