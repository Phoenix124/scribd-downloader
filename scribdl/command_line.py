import argparse
import os
import sys

from .downloader import Downloader


def get_arguments():
    """
    Parses arguments off the command-line.
    """
    parser = argparse.ArgumentParser(
        prog="scribdl",
        description="Download documents from scribd.com and books and audiobooks from everand.com"
    )

    parser.add_argument("url", metavar="URL", type=str, help="scribd or everand url to download")
    parser.add_argument(
        "-i",
        "--images",
        help="download url made up of images",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-p",
        "--pdf",
        help="convert to pdf (*Nix: imagemagick)",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-c",
        "--credentials-file",
        help="path to file containing your Everand credentials, used for Everand audiobooks",
    )
    parser.add_argument(
        "--proxy",
        help="proxy URL to use for all requests, e.g. http://127.0.0.1:8080",
    )

    return parser


def _command_line():
    """
    This function that gets executed when called via command-line.
    """
    # Windows consoles can't encode every character found in Scribd texts
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    parser = get_arguments()
    args = parser.parse_args()
    url = args.url
    pdf = args.pdf
    images = args.images

    if args.proxy:
        # requests picks proxies up from the environment
        os.environ["HTTP_PROXY"] = args.proxy
        os.environ["HTTPS_PROXY"] = args.proxy

    scribd_link = Downloader(url, credentials_file=args.credentials_file)
    downloaded_content = scribd_link.download(is_image_document=images)
    if pdf and downloaded_content is not None:
        print("\nConverting to {}..".format(downloaded_content.pdf_path))
        downloaded_content.to_pdf()


if __name__ == "__main__":
    _command_line()
