# Scribd-Downloader

**Repository is unsupported**

**You could make changes via PR**

> ⚠️ **Status (September 2026):** downloading Scribd **documents** (text and image) works.
> **Books and audiobooks** have moved from Scribd to Everand and are downloaded from there (Scribd or
> Everand URLs both work): ebooks as PDF through your Chrome browser, audiobooks through
> [audiobook-dl](https://github.com/jo1gi/audiobook-dl). See [Everand books and audiobooks](#everand-books-and-audiobooks).

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/liakhovetsh)

---

(I also found an online service https://dlscrib.com/ created by [Erik Fong](mailto:dlscrib@gmail.com). It doesn't
use this script as some people seem to think!).

Current features:

| Type       | Downloaded from | Needs an account                                  |
|------------|-----------------|---------------------------------------------------|
| Documents  | Scribd          | No                                                |
| Books      | Everand         | Yes, with a subscription and access to the book   |
| Audiobooks | Everand         | Yes, with a subscription and access to the book   |

**Some information about Scribd documents:**

There are two types of documents on Scribd:

- Documents made up using a collection of images and
- Actual documents where the text can be selected, copied etc.

This script takes a different approach to both of them:

- Documents consisting of a collection of images is straightforward and
  this script will simply download the individual images which can
  be combined to `.pdf` by passing `--pdf` option to the tool. Simple.

- Actual documents where the text can be selected are hard to tackle.
  If we feed such a document to this tool, only the text present in
  document will be downloaded. Scribd seems to use javascript to somehow
  combine text and images. So far, I haven't been able to combine them
  with Python in a way they look like the original document.

## Installation

Make sure you're using Python 3 (Python 2 is not supported by a few dependencies).
Then run these commands:

**macOS prerequisites for md2pdf / cairo**

```
brew install cairo
brew install pango
brew install libmagic
brew install gtk+
```

Make sure your Python Pillow is up to date > 6

```
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade Pillow
pip install git+https://github.com/Phoenix124/scribd-downloader.git
```

The package is not published on PyPI, so `pip install scribd-downloader` won't find it.

The system libraries above (cairo, pango) are only needed for the `--pdf` option.

For Everand books install the optional dependencies and have Google Chrome installed:

```
pip install "scribd-downloader[everand] @ git+https://github.com/Phoenix124/scribd-downloader.git"
```

For Everand audiobooks install [audiobook-dl](https://github.com/jo1gi/audiobook-dl): `pip install audiobook-dl`.

If the `scribdl` command is not found after installing (e.g. `'scribdl' is not recognized` on Windows),
the Python `Scripts` directory is not on your `PATH`. You can run the tool as a module instead:

```
python -m scribdl https://www.scribd.com/document/55949937/33-Strategies-of-War
```

## Usage

```
usage: scribdl [-h] [-i] [-p] [-c CREDENTIALS_FILE] [--epub] [--max-pages N] [--proxy PROXY] URL

Download documents from scribd.com and books and audiobooks from everand.com

positional arguments:
  URL           scribd or everand url to download

optional arguments:
  -h, --help    show this help message and exit
  -i, --images  download url made up of images
  -p, --pdf     convert to pdf (*Nix: imagemagick)
  -c CREDENTIALS_FILE, --credentials-file CREDENTIALS_FILE
                        path to file containing your Everand
                        credentials, used for Everand audiobooks
  --epub        save Everand books as EPUB instead of PDF
  --max-pages N download only the first N pages of an Everand book,
                        e.g. for a quick test
  --proxy PROXY         proxy URL to use for all requests, e.g.
                        http://127.0.0.1:8080
```

Instead of `--proxy` you can also set the standard `HTTPS_PROXY` / `HTTP_PROXY` environment variables.

## Examples

### Scribd Documents

Downloading text from document containing selectable text:

```
scribdl https://www.scribd.com/document/55949937/33-Strategies-of-War
```

(Text will be saved side by side in a `.md` file in the current working directory)

Download document containing images; use the `--images` option (the tool cannot figure out this on its own):

```
scribdl -i https://scribd.com/doc/17142797/Case-in-Point
```

(Images will be saved in the current working directory)

## Everand books and audiobooks

Scribd has moved books and audiobooks to Everand. Their Scribd URLs (`/book/`, `/read/`, `/audiobook/`,
`/listen/`) are downloaded from Everand automatically, so both kinds of URLs work.

You need an Everand account with access to the title. Use it for personal, offline reading only and
respect Everand's Terms of Service.

### Everand ebooks

```
scribdl https://www.everand.com/read/813249861/Sleep-Change-the-way-you-sleep-with-this-90-minute-read
```

1. A Google Chrome window opens. On the first run log in to Everand there and pass any captcha;
   the session is kept in `~/.scribdl/everand-chrome-profile`, so later runs don't ask again.
   Delete that folder to switch accounts.
2. The tool turns the reader's pages one by one (don't use the window meanwhile) and captures them.
3. The pages are rendered into `<title>.pdf` in the current directory, with selectable text.

Options:

- `--epub` saves a fixed-layout EPUB (`<title>.epub`) instead of the PDF. Its pages look exactly like
  the PDF ones; the text can't be reflowed, because Everand's reader positions every line itself.
- `--max-pages N` stops after the first N pages. Handy for a quick first try:

  ```
  scribdl --max-pages 5 https://www.everand.com/book/813249861/Sleep-Change-the-way-you-sleep-with-this-90-minute-read
  ```

Everand's reader is behind Cloudflare, so this drives your real browser instead of plain requests.
If Everand changes its reader, the page selectors in `scribdl/everand/capture.py` may need updating.

### Everand audiobooks

```
scribdl -c everand_credentials.txt https://www.everand.com/audiobook/237606860/100-Ways-to-Motivate-Yourself-Change-Your-Life-Forever
```

The download is handed over to [audiobook-dl](https://github.com/jo1gi/audiobook-dl). The optional
credentials file holds your Everand email and password on two lines:

```
user@mail.com
password
```

### Troubleshooting

- if problem with weasyprint
  ```
  export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH
  ```
- If the text of a document comes out as gibberish (e.g. ``Xrmhfkmrc Diaf`sf`` instead of `Trademark License`),
  Scribd has scrambled the characters of that document's font on purpose. Download the page images
  with `-i` instead: they show the text correctly.
- If you have troubles with cropped images in pdf use command:

  ```
  cd dir_with_all_image_files && img2pdf $(ls -tr *.jpg) -o path_to_pdf_output_file.pdf
  ```

## Disclaimer

Downloading books from Scribd for free maybe prohibited. This tool is
meant for educational purposes only. Please support the authors by buying
their titles.

## License

`The MIT License`

- [Mitmproxy](https://github.com/mitmproxy/mitmproxy)
- [Erik Fong](mailto:dlscrib@gmail.com)
- [BookURL](https://www.scribd.com/read/189087235/Confessions-of-a-Casting-Director-Help-Actors-Land-Any-Role-with-Secrets-from-Inside-the-Audition-Room)
