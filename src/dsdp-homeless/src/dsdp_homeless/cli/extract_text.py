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
import numpy as np
import pytesseract
from pytesseract import Output, TesseractError

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
    ap.add_argument("-w", "--width", type=int, default=1280,
                    help="resized image width (should be multiple of 32)")
    ap.add_argument("-e", "--height", type=int, default=1280,
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

    ap.add_argument("image", type=str, help="path to input image")

    return ap.parse_args()


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")




region_words = {
    'marina': 'marina',
    'gaslamp': 'gaslamp',
    'east vil': 'east_villiage',
    'village': 'east_villiage',
    'columbia': 'columbia',
    'cowumbia': 'columnbia',
    'core': 'core',
    'cortez': 'cortez',
    'ortez': 'cortez'
}


def find_rw(text):
    for rw in region_words.keys():
        if rw in text:
            return region_words[rw]

    return None

def most_common_color(image):
    '''Sample 10,000 pixels and report the most frequent color. '''
    sample_size = 10000

    img = image.reshape((image.shape[0] * image.shape[1], 3))

    img_sample = img[np.random.choice(img.shape[0], sample_size, replace=False)]

    u = np.unique(img_sample, return_counts=True, axis=0)

    # find the index of the most common color
    most_common = np.argmax(u[1])

    return u[0][most_common]

def image_to_string(image):
    '''Image to string with exception catching. '''

    try:
        return  pytesseract.image_to_string(image)
    except:
        return ''

def process_image(args, image_path, out_path, write=True):

    net = cv2.dnn.readNet(args.east)

    orig_img = cv2.imread(str(image_path))

    # Filter out images that are predominantly black, which are parts of the logo
    #if most_common_color(orig_img).sum() == 0:
    #    return False

    try:
        osd = pytesseract.image_to_osd(orig_img, output_type=Output.DICT)
    except TesseractError as e:
        print("ERROR", e)
        return False,'',image_path


    rot_image = imutils.rotate_bound(orig_img, angle=osd['rotate'])

    # Bluring makes text in halftones recognizable.
    # img = cv2.filter2D(img, -1, kernel)
    img = cv2.blur(rot_image, (5, 5))

    text1 = image_to_string(img).lower()
    rw = find_rw(text1)

    if not rw:
        # Try EAST text detection, then convert to strings.
        areas, marked_img = extract_text_areas(img, args.width, args.height, net, args.min_confidence)

        texts = [image_to_string(area) for i, (size, area) in enumerate(areas[:10])]
        text2 = ' '.join(texts).lower()

        rw = find_rw(text2)
    else:
        text2 = ''

    text = text1.replace('\n', ' ') + '\n\n' + text2

    if rw:

        op = out_path.joinpath(rw).joinpath(image_path.name)
        op.parent.mkdir(parents=True, exist_ok=True)
        print("Copy", str(op))
        cv2.imwrite(str(op), rot_image)

        return True, text, str(op)

    else:
        print("Error", image_path)

        op = out_path.joinpath('errors').joinpath(image_path.name)
        cv2.imwrite(str(op), marked_img)

        with op.with_suffix('.txt').open('w') as f:
            f.write(text)

        return False, text, str(op)

def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    args = parse_args(args)
    setup_logging(args.loglevel)

    imp = Path(args.image)

    # load the pre-trained EAST text detector

    out_path = Path('processed_images')

    out_path.mkdir(parents=True, exist_ok=True)
    out_path.joinpath('errors').mkdir(parents=True, exist_ok=True)

    if imp.is_dir():

        for image_path in imp.glob('**/*.png'):

            process_image(args, image_path, out_path)

    else:

        ret, text, img_path = process_image(args, imp, out_path)

        if not ret:
            print(str(img_path)+'\n\n'+text)


def run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
