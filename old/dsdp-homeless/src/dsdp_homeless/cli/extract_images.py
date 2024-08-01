#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2019 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN

The program uses the Root.Distributions in the source package to locate packages to link into a CKAN record.

"""

import argparse
import logging
import sys
from pathlib import Path
from subprocess import call

__author__ = "Eric Busboom"
__copyright__ = "Eric Busboom"
__license__ = "mit"

_logger = logging.getLogger(__name__)


def parse_args(args):
    """Parse command line parameters

    Args:
      args ([str]): command line parameters as list of strings

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """

    parser = argparse.ArgumentParser(
        description='Extract images from SDTP Homeless count pdfs')

    parser.add_argument(
        '-v',
        '--verbose',
        dest="loglevel",
        help="set loglevel to INFO",
        action='store_const',
        const=logging.INFO)
    parser.add_argument(
        '-vv',
        '--very-verbose',
        dest="loglevel",
        help="set loglevel to DEBUG",
        action='store_const',
        const=logging.DEBUG)

    parser.add_argument('source_dir', help='Source directory')
    parser.add_argument('dest_dir', help='Destination directoryr')

    return parser.parse_args()


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    args = parse_args(args)
    setup_logging(args.loglevel)
    _logger.debug("Starting.")

    source = Path(args.source_dir).resolve()

    dest = Path(args.dest_dir).resolve()

    for e in list(source.glob('**/*.pdf')):
        s = e.stem
        if not(len(s) == 6):
            print("Bad filename: ", e)
            continue

        year = s[:4]
        month = s[4:]

        dest_root = dest.joinpath(year, month)

        dest_root.mkdir(parents=True, exist_ok=True)

        dest_prefix = dest_root.joinpath(s)

        print("Extracting ", e)
        call(['pdfimages', '-png', str(e), str(dest_prefix)])

        for image in dest_root.glob('**/*.png'):
            print("  ", image)


def run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
