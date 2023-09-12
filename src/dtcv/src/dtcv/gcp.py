"""Read GCP annotations and create the GCP datasets"""
import json
import logging
from operator import itemgetter

import geopandas as gpd
import pandas as pd

from . import gcp_list_url, intersections_url
from .images import *

logger = logging.getLogger('gcp')


def get_gcp_files():
    '''Yield all images, downloading if necessary'''

    logger.debug("Loading GCP from "+gcp_list_url)

    with urllib.request.urlopen(gcp_list_url) as response:
        for l in response.readlines():
            url = l.strip().decode('ascii')

            yield download_to_file(url)


def extract_gcp_annotations(fn, o):
    """Extract GCP data from VIA JSON file data"""

    cols = 'x y width height'.split()
    region_ig = itemgetter(*cols)

    d = o['_via_img_metadata']

    neib_map = {}

    for k, v in d.items():
        try:
            # For 2023, the neighborhood is a file attribute
            neighborhood = v['file_attributes']['neighborhood'].lower().replace(' ','_')
        except KeyError:
            # For 2019, the neighborhood was part of the file name
            neighborhood = fn.stem.split('-')[0]

        neib_map[k] = neighborhood

    annotations = []

    try:
        inter_map = o["_via_attributes"]["region"]["Intersection"]['options']
    except KeyError:
        print(o["_via_attributes"]["region"])
        raise

    for k, v in d.items():

        if k == 'example':
            continue

        for region in v['regions']:

            try:
                x, y, width, height = region_ig(region['shape_attributes'])

                annotations.append({
                    'image_url': v['filename'],
                    'x': x,
                    'y': y,
                    'width': width,
                    'height': height,
                    'neighborhood': neib_map[v['filename']],
                    'intersection': inter_map[region['region_attributes']['Intersection']]
                })

            except KeyError:
                raise
                logger.debug("Error in GCP extraction; Wrong keys in shape attributes: {}".format(region['shape_attributes']))


    return annotations


def load_gcp_rows(fn=None):
    rows = []

    if fn is None:  # Download from S3
        files = get_gcp_files()
    else:
        files = fn.glob('**/*.json')

    for e in files:

        with e.open() as f:
            try:
                rows.extend(extract_gcp_annotations(e, json.load(f)))
            except Exception as exc:
                print(f"ERROR in file {e}: {exc}")
                raise

    return rows


def intersections_df(fn=None):
    if not fn:
        logger.debug(f"Loading intersections from {intersections_url}")
        df = pd.read_csv(intersections_url).rename(columns={'WKT': 'geometry'})
    else:
        logger.debug(f"Loading intersections from {fn}")
        df = pd.read_csv(fn).rename(columns={'WKT': 'geometry'})

    df['geometry'] = df.geometry.apply(wkt.loads)
    return gpd.GeoDataFrame(df, geometry='geometry')


def gcp_df(fn=None):
    """Return a dataframe composed of records of GCP annotations downloaded from S3"""

    rows = load_gcp_rows(fn)

    return pd.DataFrame([list(d.values()) for d in rows], columns=list(rows[0].keys()))

def gcp_transform_df(intr_gpd, gcpdf):
    """Return a dataframe of GCP intersection polygons with Affine transformations to EPSG 2230"""

    gcp_m = gcpdf.merge(intr_gpd, on=['intersection', 'neighborhood']).\
        sort_values(['image_url', 'neighborhood', 'intersection'])

    df = gpd.GeoDataFrame(gcp_m)
    df['image_x'] = df.x + (df.width / 2)
    df['image_y'] = df.y + (df.height / 2)

    df['geo_x'] = df.geometry.x
    df['geo_y'] = df.geometry.y

    rows = []

    for name, g in df.groupby(['image_url', 'neighborhood']):
        g = g.sort_values(['image_y', 'image_x'])

        # Y Axis is inverted to match the Y axis orientation of the destination
        # geographic CRS. Adding 2000 to shift the values back to positive, so
        # the sorting algo in reorder_points will have the same sense of where the origin is
        try:
            image_p = Polygon([r.image_x, r.image_y] for idx, r in g.iterrows())
            image_p = invert_poly(Polygon(reorder_points(image_p)))
        except ValueError:
            print("ERROR", g)
            raise

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

    m = df.apply(_get_matrix, axis=1)

    df['matrix'] = m

    return df


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
