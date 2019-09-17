import json
from operator import itemgetter
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely import wkt

from pt_lib import *

p = Path('/Users/eric/Google Sync/sandiegodata.org/Projects/Downtown Partnership Homeless'
         '/Annotations/complete/gcp')

intersections_file = '../data/gcp_intersections_2230.csv'

cols = 'x y width height'.split()


def load_gcp_files(p):
    region_ig = itemgetter(*cols)

    rows = []
    for fn in p.glob('*.json'):

        if not '-gcp-' in fn.stem:
            continue

        with fn.open() as f:
            d = json.load(f)['_via_img_metadata']

            for k, v in d.items():
                if k == 'example':
                    continue

                image_url = v['filename']

                for region in v['regions']:
                    try:
                        row = [fn, image_url] + \
                              list(region_ig(region['shape_attributes'])) + \
                              [region['region_attributes']['Intersection']]

                        rows.append(row)
                    except KeyError:
                        print("Error in {} wrong keys in shape attributes: {}" \
                              .format(fn, region['shape_attributes']))

    return pd.DataFrame(rows, columns=['source', 'image'] + cols + ['intersection'])


def make_gcp_transform_df(gcp_df, intersections_file):
    intr = pd.read_csv(intersections_file)
    intr_gpd = gpd.GeoDataFrame(intr,
                                geometry=intr.WKT.apply(wkt.loads)).drop(columns='WKT')

    gcp_m = gcp_df.merge(intr_gpd, on='intersection').sort_values(['image', 'neighborhood', 'intersection'])
    df = gpd.GeoDataFrame(gcp_m)

    df['image_x'] = df.x + (df.width / 2)
    df['image_y'] = df.y + (df.height / 2)

    df['geo_x'] = df.geometry.x
    df['geo_y'] = df.geometry.y

    rows = []

    for name, g in df.groupby(['image', 'neighborhood']):
        g = g.sort_values(['image_y', 'image_x'])

        # Y Axis is inverted to match the Y axis orientation of the destination
        # geographic CRS. Adding 2000 to shift the values back to positive, so
        # the sorting algo in reorder_points will have the same sense of where the origin is
        image_p = Polygon([r.image_x, r.image_y] for idx, r in g.iterrows())
        image_p = invert_poly(Polygon(reorder_points(image_p)))

        geo_p = Polygon(reorder_points([[r.geo_x, r.geo_y] for idx, r in g.iterrows()]))

        rows.append([name[0], name[1], image_p.wkt, geo_p.wkt])

    #
    # Save the source ( image ) and dest (map ) polygons,
    # formed from the GCPs for each neighborhood
    #

    df = pd.DataFrame(rows, columns='url neighborhood source dest'.split())

    df['source'] = df.source.apply(wkt.loads)
    df['dest'] = df.dest.apply(wkt.loads)

    def _get_matrix(r):
        try:
            return json.dumps(get_matrix(r).tolist())
        except ValueError as e:
            print(r)
            print(e)

    df['matrix'] = df.apply(_get_matrix, axis=1)

    return df


gcp_df = load_gcp_files(p)

gcp_df.to_csv('../data/raw_gcp.csv', index=False)

df = make_gcp_transform_df(gcp_df, intersections_file)

df.to_csv('../data/gcp_transforms.csv', index=False)

print(len(df))


def test_gcp():
    def test_transform(r):
        """Create the transform matrix, then transform the pri to sec"""
        pri = r.source
        sec = r.dest

        A, pri, sec = solve_transform(pri, sec)

        Ap = np.array(r.tf)

        np.allclose(A, Ap)

        return Polygon(transform_points(Ap, pri)).wkt

    df = pd.read_csv('../data/gcp_transforms.csv')

    df['tf'] = df.matrix.apply(json.loads)

    ## Testing. Transform the source polys into dest, and
    ## check that they look sensible.

    df['source'] = df.source.apply(wkt.loads).apply(reorder_points)

    df['dest'] = df.dest.apply(wkt.loads).apply(reorder_points)

    df['test'] = df.apply(test_transform, axis=1).apply(wkt.loads)

    dest = df[['url', 'dest']].rename(columns={'dest': 'geometry'})
    dest.to_csv('../test/dest_poly.csv')
    test = df[['url', 'test']].rename(columns={'test': 'geometry'})
    test.to_csv('../test/test_poly.csv')


test_gcp()
