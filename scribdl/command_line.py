import argparse

from .downloader import Downloader
from . import authorize


def get_arguments():
    """
    Parses arguments off the command-line.
    """
    parser = argparse.ArgumentParser(
        description="Download documents and books from scribd.com"
    )

    parser.add_argument("url", metavar="URL", type=str, help="scribd url to download")
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
        help="path to file containing your Scribd premium credentials",
    )

    return parser


def _command_line():
    """
    This function that gets executed when called via command-line.
    """
    parser = get_arguments()
    args = parser.parse_args()
    url = args.url
    pdf = args.pdf
    images = args.images

    if args.credentials_file:
        credentials_file = args.credentials_file
        authorize.set_credentials(credentials_file)

    scribd_link = Downloader(url)
    downloaded_content = scribd_link.download(is_image_document=images)
    if pdf:
        print("\nConverting to {}..".format(downloaded_content.pdf_path))
        downloaded_content.to_pdf()


if __name__ == "__main__":
    _command_line()
