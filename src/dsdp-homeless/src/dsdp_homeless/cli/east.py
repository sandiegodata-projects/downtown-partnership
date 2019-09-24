#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2019 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE.txt

"""
"""

import argparse
import logging
import sys
from pathlib import Path

import cv2
import imutils
import pytesseract
from pytesseract import Output

from dsdp_homeless.ocr import extract_text_areas

_logger = logging.getLogger(__name__)


def parse_args(args):
    """Parse command line parameters

    Args:
      args ([str]): command line parameters as list of strings

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """

    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", type=str,
                    help="path to input image")
    ap.add_argument("-east", "--east", type=str,
                    help="path to input EAST text detector")
    ap.add_argument("-c", "--min-confidence", type=float, default=0.5,
                    help="minimum probability required to inspect a region")
    ap.add_argument("-w", "--width", type=int, default=320,
                    help="resized image width (should be multiple of 32)")
    ap.add_argument("-e", "--height", type=int, default=320,
                    help="resized image height (should be multiple of 32)")

    ap.add_argument(
        '-v',
        '--verbose',
        dest="loglevel",
        help="set loglevel to INFO",
        action='store_const',
        const=logging.INFO)
    ap.add_argument(
        '-vv',
        '--very-verbose',
        dest="loglevel",
        help="set loglevel to DEBUG",
        action='store_const',
        const=logging.DEBUG)

    return ap.parse_args()


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")



def rotate_extract(image_fn):
    i = cv2.imread(str(image_fn))

    osd = pytesseract.image_to_osd(i, output_type=Output.DICT)
    i = imutils.rotate(i, angle=-osd['rotate'])

    text = pytesseract.image_to_string(i)

    return text.replace('\n', ' ').lower(), i, osd['rotate']

region_words = {
    'marina': 'marina',
    'gaslamp': 'gaslamp',
    'east vil': 'ev',
    'columbia': 'columbia',
    'core columbia': 'columbia'
}

def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    args = parse_args(args)
    setup_logging(args.loglevel)

    imp = Path(args.image)

    areas, img = extract_text_areas(str(imp), args.width, args.height, args.east, args.min_confidence)

    for i, (size, area) in enumerate(areas[:10]):
        text = pytesseract.image_to_string(area)
        print(size, text)

    cv2.imwrite('output.png',img)


def run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
