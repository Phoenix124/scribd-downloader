# Scribd-Downloader

**Repository is unsupported**

**You could make changes via PR**

> ⚠️ **Status (September 2026):** downloading Scribd **documents** (text and image) works.
> **Books and audiobooks** have moved from Scribd to Everand. Pass their **Everand** URL instead:
> ebooks are downloaded as PDF through your Chrome browser, audiobooks through
> [audiobook-dl](https://github.com/jo1gi/audiobook-dl). See [Everand books and audiobooks](#everand-books-and-audiobooks).

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/liakhovetsh)

---

(I also found an online service https://dlscrib.com/ created by [Erik Fong](mailto:dlscrib@gmail.com). It doesn't
use this script as some people seem to think!).

Current features:

| Type       | Downloadable without Scribd premium | Requires Scribd premium for full download |
|------------|-------------------------------------|-------------------------------------------|
| Documents  | Yes                                 | No                                        |
| Books      | No (Everand, needs an account)      | Yes                                       |
| Audiobooks | No (Everand, needs an account)      | Yes                                       |

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
usage: scribdl [-h] [-i] [-p] [-c CREDENTIALS_FILE] [--cookies COOKIES] [--proxy PROXY] URL

Download documents from scribd.com and books and audiobooks from everand.com

positional arguments:
  URL           scribd or everand url to download

optional arguments:
  -h, --help    show this help message and exit
  -i, --images  download url made up of images
  -p, --pdf     convert to pdf (*Nix: imagemagick)
  -c CREDENTIALS_FILE, --credentials-file CREDENTIALS_FILE
                        path to file containing your Scribd premium
                        credentials (Everand credentials for Everand
                        audiobooks)
  --cookies COOKIES     path to file with Scribd premium cookies, one
                        name=value per line
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

Scribd has moved books and audiobooks to Everand: their Scribd URLs (`/book/`, `/read/`, `/audiobook/`)
now redirect there and the endpoints this tool used are gone. For these URLs the tool stops with
`Scribd redirected to Everand` and prints the Everand URL to use instead.

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

Everand's reader is behind Cloudflare, so this drives your real browser instead of plain requests.
If Everand changes its reader, the page selectors in `scribdl/everand/capture.py` may need updating.

### Everand audiobooks

```
scribdl -c everand_credentials.txt https://www.everand.com/audiobook/237606860/100-Ways-to-Motivate-Yourself-Change-Your-Life-Forever
```

The download is handed over to [audiobook-dl](https://github.com/jo1gi/audiobook-dl). The optional
credentials file holds your Everand email and password on two lines, like the Scribd one below.

The old Scribd code and the premium options (`-c`, `--cookies`) are kept in case this changes.
The old instructions:

<details>
<summary>Legacy usage for Scribd books and audiobooks</summary>

### Scribd Books

The below command will generate a `.md` file of the book in the current working directory
(both `/read/<id>/...` and `/book/<id>/...` URLs work):

```
scribdl https://www.scribd.com/read/189087235/Confessions-of-a-Casting-Director-Help-Actors-Land-Any-Role-with-Secrets-from-Inside-the-Audition-Room
```

Pass `--pdf` option to convert the generated output to a PDF.

This will only download the book content available without owning a premium account on Scribd.
See the below section for downloading full books if you own a premium Scribd account.

### Scribd Audiobooks

This will download `.mp3` of the audiobook:

```
scribdl https://www.scribd.com/audiobook/237606860/100-Ways-to-Motivate-Yourself-Change-Your-Life-Forever
```

This will only download the preview version of the audiobook. See the below section for
downloading complete audiobooks if you own a premium Scribd account.

### Downloading complete textual books and audiobooks

If you have a premium Scribd account, you can also download the full version of
textual books and audiobooks.

Create a text file containing your Scribd credentials, such that the contents of the file look like below:

```
user@mail.com
password
```

Now pass the file path to the `-c` option, for example:

```
scribdl -c scribd_credentials.txt https://www.scribd.com/audiobook/359295794/Principles-Life-and-Work
```

It should then download all the audiobook chapters as mp3. Similarly, you could also download complete
contents of a Scribd book by replacing the URL with the URL of your choice.

If logging in with credentials fails (e.g. `Login error: An error occurred please try again`),
or you're not willing to place your account credentials in a file, copy the cookie values
for `_scribd_session` and `_scribd_expire` from your web-browser while logged into your premium
Scribd account and put them in a file:

```
_scribd_session=<value>
_scribd_expire=<value>
```

Then pass it with `--cookies`:

```
scribdl --cookies scribd_cookies.txt https://www.scribd.com/read/189087235/Confessions-of-a-Casting-Director-Help-Actors-Land-Any-Role-with-Secrets-from-Inside-the-Audition-Room
```

You should then be able to automatically download full version of both textual books and audiobooks
from Scribd using the tool by running the commands as usual.

</details>

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
