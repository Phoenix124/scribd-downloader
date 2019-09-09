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

    def test_image_pdf_url(self):
        args = []
        args.append("-i")
        args.append("-p")
        args.append("https://example.com/")
        parser = command_line.get_arguments()
        parsed_args = parser.parse_args(args)
        assert parsed_args.images and parsed_args.pdf
