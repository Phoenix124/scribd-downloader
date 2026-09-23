from .. import command_line
import sys

import pytest


class TestCommandLine:
    def test_empty(self):
        args = []
        parser = command_line.get_arguments()
        with pytest.raises(SystemExit):
            parser.parse_args(args)

    def test_image_no_url(self):
        args = []
        args.append("-i")
        parser = command_line.get_arguments()
        with pytest.raises(SystemExit):
            parser.parse_args(args)

    def test_image_url(self):
        args = []
        args.append("-i")
        args.append("https://example.com/")
        parser = command_line.get_arguments()
        parsed_args = parser.parse_args(args)
        assert parsed_args.images and not parsed_args.pdf

    def test_pdf_url(self):
        args = []
        args.append("-p")
        args.append("https://example.com/")
        parser = command_line.get_arguments()
        parsed_args = parser.parse_args(args)
        assert not parsed_args.images and parsed_args.pdf

    def test_credentials_proxy(self):
        args = ["-c", "credentials.txt", "--proxy", "http://127.0.0.1:8080", "https://example.com/"]
        parser = command_line.get_arguments()
        parsed_args = parser.parse_args(args)
        assert parsed_args.credentials_file == "credentials.txt"
        assert parsed_args.proxy == "http://127.0.0.1:8080"

    def test_image_pdf_url(self):
        args = []
        args.append("-i")
        args.append("-p")
        args.append("https://example.com/")
        parser = command_line.get_arguments()
        parsed_args = parser.parse_args(args)
        assert parsed_args.images and parsed_args.pdf

    def test_everand_options(self):
        args = ["--epub", "--max-pages", "5", "https://www.everand.com/book/1/Book"]
        parser = command_line.get_arguments()
        parsed_args = parser.parse_args(args)
        assert parsed_args.epub and parsed_args.max_pages == 5

    def test_everand_defaults(self):
        parser = command_line.get_arguments()
        parsed_args = parser.parse_args(["https://www.everand.com/book/1/Book"])
        assert not parsed_args.epub and parsed_args.max_pages == 0
