"""Download annocations for counts and prepare dataframes"""


from pathlib import Path
import json
from operator import itemgetter
import pandas as pd
import numpy as np
import logging
import urllib.request
from .download import download_to_file

from . import count_list_url

logger = logging.getLogger('count')


def get_count_files():
    '''Yield all images, downloading if necessary'''
    logger.debug(f'Downloading {count_list_url}')
    with urllib.request.urlopen(count_list_url) as response:
        for l in response.readlines():
            url = l.strip().decode('ascii')

            yield download_to_file(url)

def extract_region_annotations(fn, o):
    pass

    reg_cols = 'Type count'.split()
    reg_ig = itemgetter(*reg_cols)

    shape_cols = 'cx cy r'.split()
    shape_ig = itemgetter(*shape_cols)

    rect_shape_cols = 'x y width height'.split()  # in case the shape is a rectangle, rather than a circle
    rect_shape_ig = itemgetter(*rect_shape_cols)

    d = o['_via_img_metadata']

    warnings = set()

    for k, v in d.items():
        if k == 'example':
            continue

        for region in v['regions']:

            if region['shape_attributes']['name'] == 'rect':
                k = (fn, v['filename'].strip())
                if k not in warnings:
                    logger.warning( f"Got a rect for {fn}, image {v['filename'].strip()}. This should be a circle, but was converted sucessfully.")
                    warnings.add(k)

                x, y, width, height = list(rect_shape_ig(region['shape_attributes']))
                cx, cy = x + (width / 2), y + (height / 2)
                r = width / 2

            elif region['shape_attributes']['name'] == 'circle':
                cx, cy, r = list(shape_ig(region['shape_attributes']))
            else:
                logger.error(f"Error in count extraction; wrong keys in shape attributes for file {fn}, expected {e}: {region['shape_attributes']}")
                return

            try:
                typ, count = list(reg_ig(region['region_attributes']))
            except KeyError as e:
                try:
                    typ = region['region_attributes']['Type']
                except KeyError:
                    typ = '1'
                    logger.info(f"Missing 'Type' in region attributes, assuming 1, Individual, {fn}, image {v['filename'].strip()}")

                try:
                    count = region['region_attributes']['count']
                except KeyError:
                    count = 1
                    logger.info(f"Missing 'count' in region attributes, assuming 1, {fn}, image {v['filename'].strip()}")


            o={'image_url':v['filename']}

            o.update({
                'cx': cx,
                'cy': cy,
                'r': r,
                'type': typ,
                'count': count

            })

            yield o




def load_count_rows(fn):

    rows = []

    headers = None

    if fn is None:  # Download from S3
        files = get_count_files()
    else:
        logger.debug(f'Loading counts from  {fn}')
        files = fn.glob('**/*.json')

    for e in files:

        with e.open() as f:
            o = json.load(f)

            for a in extract_region_annotations(e, o):
                if headers is None:
                    headers = list(a.keys())

                rows.append(list(a.values()))


    return headers, rows

def count_df(fn=None):

    headers, rows = load_count_rows(fn)

    return pd.DataFrame(rows, columns=headers)

def extract_file_annotations(o):
    d = o['_via_img_metadata']

    file_cols = 'date neighborhood total_count temp rain '.split()

    def get_file_cols(d):
        row = {}
        for c in file_cols:
            row[c] = d.get(c)

        return row

    for k, v in d.items():
        if k == 'example':
            continue

        o={'image_url':v['filename']}
        row = get_file_cols(v['file_attributes'])

        if(any(row.values())):
            o.update(row)
            yield o
        else:
            pass # probabl read the wrong kind of file.


def load_file_rows(fn=None):

    rows = []

    headers = None

    if fn is None:  # Download from S3
        logger.debug('Loading file rows from S3')
        files = get_count_files()
    else:
        logger.debug(f'Loading file rows from {fn}')
        files = fn.glob('**/*.json')

    for e in files:
        logger.debug(f'Process file annotations: {e}')
        with e.open() as f:
            o = json.load(f)

            for a in extract_file_annotations(o):
                if headers is None:
                    headers = list(a.keys())+['source_file']

                rows.append(list(a.values())+[str(e)])


    return headers, rows


def file_df(fn=None):

    headers, rows = load_file_rows(fn)

    return pd.DataFrame(rows, columns=headers)