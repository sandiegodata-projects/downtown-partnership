
from .pt_lib import *

from pathlib import Path
import json
from operator import itemgetter
import pandas as pd
import numpy as np

tf = '../data/gcp_transforms.csv'

p = Path('/Users/eric/Google Sync/sandiegodata.org/Projects/Downtown Partnership Homeless'
         '/Annotations/Complete Count')

shape_cols = 'cx cy r'.split()
shape_ig = itemgetter(*shape_cols)

reg_cols = 'Type count'.split()
reg_ig = itemgetter(*reg_cols)
reg_cols = [e.lower() for e in reg_cols]


shape_cols = 'cx cy r'.split()
shape_ig = itemgetter(*shape_cols)

file_cols = 'date neighborhood total_count temp rain '.split()

def get_file_cols(d):
    row = []
    for c in file_cols:
        row.append(d.get(c))

    return row

rows = []
file_rows = []
for fn in p.glob('*.json'):

    if not '-homeless-' in fn.stem:
        continue

    with fn.open() as f:
        d = json.load(f)['_via_img_metadata']

        for k, v in d.items():
            if k == 'example':
                continue

            image_url = v['filename']

            try:
                file_rows.append([fn, image_url] + get_file_cols(v['file_attributes']))
            except KeyError as e:
                print("Error", e, v['file_attributes'])

            for region in v['regions']:
                try:
                    row = [fn, image_url] \
                          + list(shape_ig(region['shape_attributes'])) \
                          + list(reg_ig(region['region_attributes']))

                    rows.append(row)
                except KeyError as e:
                    print("Error. wrong keys in shape attributes: ", region['shape_attributes'])

tf = pd.read_csv(tf)

file_df = pd.DataFrame(file_rows, columns=['filename', 'url'] + file_cols).merge(tf, on='url')

df = pd.DataFrame(rows, columns=['filename', 'url'] + shape_cols + reg_cols).merge(file_df, on='url')

df = df.drop(columns=['filename_x','neighborhood_x'])\
        .rename(columns={'filename_y':'filename', 'neighborhood_y':'neighborhood'})
df['count'] = df['count'].replace('',1)


df.to_csv('../data/raw_points.csv')
# Load the transforms

tf['tf'] = tf.matrix.apply(json.loads)

tf_map = {r.url: np.array(r.tf) for idx, r in tf.iterrows()}

rows = []
row_header = 'neighborhood date count x y'.split()

for idx, row in df.iterrows():
    url = row.url

    if url in tf_map:
        A = tf_map[url]
        p = transform_point(A, invert_point(np.array([row.cx,row.cy])))
        count = int(row['count'] or 1)
        row = [row.neighborhood, row.date, count, p[0], p[1]]
        rows.append(row)


df = pd.DataFrame(rows, columns=row_header)
df.to_csv('../data/points.csv')
