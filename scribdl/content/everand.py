import os
import re
import shutil
import subprocess
import tempfile
from urllib.parse import unquote

from .. import internals
from .. import exceptions

EVERAND_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?everand\.com/(?P<kind>[a-z]+)/(?P<id>\d+)(?:/(?P<slug>[^/?#]+))?"
)

# Scribd moved books and audiobooks to Everand, keeping their paths
SCRIBD_MOVED_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?scribd\.com/(?=(?:book|read|audiobook|listen)/\d+)"
)

BOOK_KINDS = ("book", "read")
AUDIOBOOK_KINDS = ("audiobook", "listen")

# Keeps the Everand login and Cloudflare clearance between runs
PROFILE_DIR = os.path.join(os.path.expanduser("~"), ".scribdl", "everand-chrome-profile")


def parse_everand_url(url):
    """
    Splits an Everand URL into (kind, id, slug), e.g.
    ("read", 813249861, "Sleep-Change-the-way-you-sleep").
    Returns None if it isn't an Everand content URL.
    """
    match = EVERAND_URL_PATTERN.match(url)
    if not match:
        return None
    return match.group("kind"), int(match.group("id")), match.group("slug")


def is_everand_url(url):
    return parse_everand_url(url) is not None


def to_everand_url(url):
    """
    Returns the Everand URL to download `url` from: Everand URLs as they
    are, Scribd book and audiobook URLs moved to everand.com. Returns None
    for anything else (e.g. Scribd documents).
    """
    url = SCRIBD_MOVED_URL_PATTERN.sub("https://www.everand.com/", url)
    return url if is_everand_url(url) else None


def _require_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise exceptions.ScribdFetchError(
            "Downloading Everand books needs Playwright. Install it with: "
            "pip install \"scribd-downloader[everand]\" (or: pip install playwright pypdf)"
        )
    return sync_playwright


class EverandContent:
    """
    A base class for Everand books and audiobooks.

    Parameters
    ----------
    url : `str`
        A string containing Everand URL.
    """

    kinds = ()

    def __init__(self, url):
        parsed = parse_everand_url(url)
        if parsed is None or parsed[0] not in self.kinds:
            raise exceptions.ScribdFetchError("Unsupported Everand URL: {}".format(url))
        self.url = url
        _, self.content_id, self._slug = parsed

    @property
    def title(self):
        """
        Everand pages are behind Cloudflare, so the title is taken from the URL.
        """
        if self._slug:
            return unquote(self._slug).replace("-", " ")
        return str(self.content_id)

    @property
    def sanitized_title(self):
        return internals.sanitize_title(self.title)


class EverandBook(EverandContent):
    """
    A class for downloading Everand ebooks as PDF or EPUB.

    Everand's reader is protected by Cloudflare, so this drives a visible
    Google Chrome window: log in once there and the session is kept in
    `PROFILE_DIR` for the next runs. Every page shown by the reader is
    captured and rendered into a PDF with selectable text.
    """

    kinds = BOOK_KINDS

    @property
    def filename(self):
        return self.sanitized_title + ".pdf"

    @property
    def epub_filename(self):
        return self.sanitized_title + ".epub"

    @property
    def reader_url(self):
        return "https://www.everand.com/read/{}/{}".format(self.content_id, self._slug or "")

    def download(self, filename=None, max_pages=0, epub=False):
        """
        Downloads the book to a PDF (or a fixed-layout EPUB with `epub`)
        and returns its path. `max_pages` stops early after that many page
        columns (0 = all).
        """
        from ..everand import render
        from ..everand import epub as epub_writer

        if not filename:
            filename = self.epub_filename if epub else self.filename
        sync_playwright = _require_playwright()

        with sync_playwright() as playwright:
            fontfaces, columns = self._capture(playwright, max_pages)
            if not columns:
                raise exceptions.ScribdFetchError(
                    "No pages captured, the Everand reader may have changed: {}".format(self.url))

            print("Rendering {} pages to {}..".format(len(columns), "EPUB" if epub else "PDF"))
            browser = playwright.chromium.launch(channel="chrome", headless=True)
            try:
                if epub:
                    pages = render.render_xhtml_pages(browser, columns, fontfaces)
                    epub_writer.write_epub(pages, render.BASE_CSS + fontfaces, self.title, filename)
                else:
                    with tempfile.TemporaryDirectory() as directory:
                        paths = render.render_pages(browser, columns, fontfaces, directory)
                        render.merge_pdfs(paths, filename)
            finally:
                browser.close()

        print("Saved {}".format(filename))
        return filename

    def _capture(self, playwright, max_pages):
        from ..everand import capture

        context = playwright.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            # A landscape window makes the reader lay columns out like book pages
            viewport={"width": 1600, "height": 1080},
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://www.everand.com", wait_until="domcontentloaded")
            print("Waiting for the Everand login. Log in (and pass any captcha) in the "
                  "Chrome window; this is only needed on the first run.")
            page.locator("div.user_row").wait_for(state="attached", timeout=0)

            print("Opening the reader..")
            page.goto(self.reader_url, wait_until="domcontentloaded")
            if "Browser limit exceeded" in page.content():
                raise exceptions.ScribdFetchError(
                    "Everand says \"Browser limit exceeded\": too many devices were used "
                    "recently, try again within 24 hours")
            # Without access Everand sends the reader back to the book page
            if "/read/" not in page.url:
                raise exceptions.ScribdFetchError(
                    "Everand didn't open the reader for this book. Check that your account "
                    "has an active subscription and the book is available in your country: "
                    "{}".format(page.url))

            # The cookie banner may cover the page buttons
            try:
                page.locator("button.osano-cm-accept-all").click(timeout=3000)
            except Exception:
                pass

            page.locator("#fontfaces").wait_for(state="attached", timeout=60000)
            fontfaces = capture.inline_fonts(context, page.locator("#fontfaces").inner_html())
            columns = capture.capture_book(page, max_pages=max_pages)
        finally:
            context.close()
        return fontfaces, columns


class EverandAudioBook(EverandContent):
    """
    A class for downloading Everand audiobooks.

    The download itself is done by audiobook-dl
    (https://github.com/jo1gi/audiobook-dl), which has to be installed.

    Parameters
    ----------
    url : `str`
        A string containing Everand audiobook URL.
    credentials_file : `str`
        Optional path to a file with the Everand username and password.
    """

    kinds = AUDIOBOOK_KINDS

    def __init__(self, url, credentials_file=None):
        super().__init__(url)
        self.credentials_file = credentials_file

    @property
    def listen_url(self):
        return "https://www.everand.com/listen/{}".format(self.content_id)

    def command(self, executable="audiobook-dl"):
        """
        Builds the audiobook-dl command line.
        """
        command = [executable]
        if self.credentials_file:
            with open(self.credentials_file, "r") as in_file:
                username, password = in_file.read().split()
            command += ["--username", username, "--password", password]
        command.append(self.listen_url)
        return command

    def download(self):
        """
        Downloads the audiobook into the current directory.
        """
        executable = shutil.which("audiobook-dl")
        if executable is None:
            raise exceptions.ScribdFetchError(
                "Downloading Everand audiobooks needs audiobook-dl. Install it with: "
                "pip install audiobook-dl")
        result = subprocess.run(self.command(executable))
        if result.returncode != 0:
            raise exceptions.ScribdFetchError(
                "audiobook-dl failed with exit code {} for {}".format(result.returncode, self.listen_url))
