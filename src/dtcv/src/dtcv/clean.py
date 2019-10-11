"""Pandas codes to clean files. """

import json
from pathlib import Path

import numpy as np
import pandas as pd
from dtcv.pt_lib import transform_point, invert_point
from shapely.geometry import Polygon
from pathlib import Path
def uninvert_point(p):
    x, y = p

    y = -y + 2000
    return (x, y)

def uninvert_poly(poly):
    return Polygon(uninvert_point(p) for p in poly_to_array(poly))

def poly_to_array(poly):
    try:

        return np.array(poly.exterior.coords)[:-1]
    except AttributeError:
        return poly


def bound_dims(v):
    (minx, miny, maxx, maxy) = v.bounds
    return round(maxx - minx, -1), round(maxy - miny, -1)


def agg_inter(g):
    """Aggregate a list of intersections into a comma separated string"""
    return ','.join(sorted(g.unique()))


# some extra variant information
def map_names(r):
    ym = r.year * 100 + r.month

    if ym < 201600:
        return r.neighborhood + '_14'
    elif 201600 <= ym < 201704:
        return r.neighborhood + '_16'
    elif 201704 <= ym:
        return r.neighborhood + '_17'
    else:
        # Should not get here.
        print(ym, r.year, r.month)
        return r.neighborhood + '_18'


# Different maps variants, based on the intersections
intersection_group_map = {
    'Ketner_A,Ketner_Broadway,State_A,State_Broadway': 'a',  # 'columbia',
    '11th_B,11th_Broadway,Front_B,Front_Broadway': 'a',  # 'core_columbia',
    '1st_Ash,1st_Cedar,9th_Ash,9th_Cedar': 'a',  # 'cortez',
    '16th_E,16th_Imperial,7th_E,7th_Imperial': 'a',  # 'east_village_a',
    '16th_Imperial,16th_Market,7th_Imperial,7th_Market': 'b',  # 'east_village_b',
    '16th_E,16th_Market,7th_E,7th_Market': 'c',  # 'east_village_c',
    '4th_Broadway,4th_K,6th_Broadway,6th_K': 'a',  # 'gaslamp',
    '3rd_G,3rd_K,Ketner_G,Ketner_Market': 'a'}  # 'marina'}


def intersection_regions_df(gcp_transform_df, gcp_df):
    df = gcp_transform_df.rename(columns={'source': 'source_inv'})

    df['source'] = df.source_inv.apply(uninvert_poly)
    df['source_area'] = df.source.apply(lambda v: v.area)

    df['source_shape'] = df.source.apply(bound_dims)
    df['source_shape_x'] = df.source_shape.apply(lambda v: v[0])
    df['source_shape_y'] = df.source_shape.apply(lambda v: v[1])

    t = gcp_df.rename(columns={'image_url': 'url'}).groupby('url').agg({'intersection': agg_inter}).reset_index() \
        .rename(columns={'intersection': 'intersections_id'})
    df = df.merge(t, on='url')

    df['year'] = df.url.apply(lambda v: int(Path(v).stem[:4]))
    df['month'] = df.url.apply(lambda v: int(Path(v).stem[4:6]))

    df['map_name'] = df.apply(map_names, axis=1)

    df['intersection_group'] = t.intersections_id.apply(lambda v: intersection_group_map[v])

    intersection_regions = df[
        ['url', 'neighborhood', 'year', 'month', 'intersections_id', 'intersection_group', 'map_name',
         'source_inv', 'source', 'source_area', 'source_shape', 'source_shape_x', 'source_shape_y',
         'dest', 'matrix']]

    return intersection_regions


def clean_file_annotations(file_df):
    import hashlib, base64
    import re

    fa = file_df.copy()

    n_map = {
        'Columbia': 'columbia',
        'east_vllage': 'east_village',
        'East Village': 'east_village',
        'East Village N': 'east_village',
        'East Village South': 'east_village_south',
        'east villiage': 'east_village',
        'Core Columbia': 'core',
        'Core': 'core',
        'Cortez': 'cortez',
        'Gaslamp': 'gaslamp',
        'Marina': 'marina',
        '' : 'gaslamp',
        float('nan'): 'gaslamp'
    }

    fa = fa.replace('2017-03-30\n', '2017-03-30')  # Error in one of the dates
    fa['neighborhood'] = fa.neighborhood.replace(n_map)
    fa['rain'] = fa.rain.fillna('')
    fa['temp'] = pd.to_numeric(fa.temp, errors='coerce')

    fa['url_year'] = fa.image_url.apply(lambda v: int(Path(v.strip()).stem[0:4]))
    fa['url_month'] = fa.image_url.apply(lambda v: int(Path(v.strip()).stem[4:6]))
    fa['date'] = pd.to_datetime(fa.apply(lambda r: r.date if r.date else f'{r.url_year}-{r.url_month:02d}-01', axis=1))
    fa['url_neighborhood'] = fa.image_url.apply(lambda v: v.strip().split('/')[-2])
    #fa['neighborhood'] = fa.apply(lambda r: r.neighborhood if r.neighborhood else r.url_neighborhood, axis=1)

    # Fix Dates. Maps for November 2016 and October 2016 both have
    # dates of enumeration in October 2016. The maps with enumeration dates
    # of 2016-10-23 are in the map set for November 2016, so these
    # dates were changed to 2016-11-23

    fa.loc[fa.date == '2016-10-23', 'date'] = pd.to_datetime('2016-11-23')

    # Remove some files. These files have errors. See the documentation README for more information.

    fa['keep'] = True
    fa.loc[(fa.date.dt.month == 9) & (fa.date.dt.year == 2014), 'keep'] = False
    fa.loc[(fa.date.dt.month == 8) & (fa.date.dt.year == 2014), 'keep'] = False
    fa.loc[(fa.date.dt.month == 6) & (fa.date.dt.year == 2015), 'keep'] = False
    fa = fa[fa.keep].drop(columns='keep')

    pd.set_option('display.width', 1000)

    def file_id_hash(v):
        # Git rid of digits, so Excel doesn't mangle the ids.
        return base64.b64encode(hashlib.sha224(v.encode('utf8')).digest()).decode('ascii')

    fa['file_id'] = fa.image_url.apply(file_id_hash)

    # Choke if there are duplicated file_ids. If there is, increase the length of the file id
    assert len(fa[fa.duplicated(subset='file_id', keep=False)]) == 0

    fa = fa[
        ['image_url', 'file_id', 'source_file', 'url_year', 'url_month', 'date', 'neighborhood', 'url_neighborhood', 'total_count', 'temp',
         'rain', ]]

    return fa

def clean_counts(rc_df, f_df, tf_df):
    """

    :param rc_df: Raw counts dataframe, raw_count_annotations.csv
    :param f_df:  File annotations, file.csv
    :param tf_df: gcp transforms, gcp_transforms.csv
    :return:
    """

    rc_df['count'] = rc_df['count'].replace('', 1).fillna(1)

    t = f_df.merge(rc_df, on='image_url')

    tf_df['tf'] = tf_df.matrix.apply(json.loads)
    tf_map = {r.url: np.array(r.tf) for idx, r in tf_df.iterrows()}

    rows = []

    for idx, row in t.iterrows():
        url = row.image_url

        if url in tf_map:
            A = tf_map[url]
            p = transform_point(A, invert_point(np.array([row.cx, row.cy])))
            count = int(row['count'] or 1)
            new_row = [row.file_id, row.neighborhood, row.date, count, row['type'], p[0], p[1]]
            rows.append(new_row)

    return pd.DataFrame(rows, columns='file_id neighborhood date count type x y'.split())
