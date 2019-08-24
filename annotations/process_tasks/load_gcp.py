
from pathlib import Path
import json
from operator import itemgetter
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely import wkt
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import nearest_points


p = Path('/Users/eric/Google Sync/sandiegodata.org/Projects/Downtown Partnership Homeless/Uploads')

cols = 'x y width height'.split()

region_ig = itemgetter(*cols)

rows = []
for fn in p.glob('*.json'):
    with fn.open() as f:
        d = json.load(f)['_via_img_metadata']

        for k,v in d.items():
            if k == 'example':
                continue

            image_url = v['filename']

            for region in v['regions']:
                row = [fn,image_url] + list(region_ig(region['shape_attributes'])) + [region['region_attributes']['Intersection']]
                rows.append(row)

df = pd.DataFrame(rows, columns=['source','image']+cols+['intersection'])

intr = pd.read_csv('../generate_tasks/gcp_intersections_2230.csv')
intr_gpd = gpd.GeoDataFrame(intr, geometry=intr.WKT.apply(wkt.loads)).drop(columns='WKT')

df = gpd.GeoDataFrame(df.merge(intr_gpd, on='intersection').sort_values(['image', 'neighborhood', 'intersection']))

df['image_x'] = df.x+(df.width/2)
df['image_y'] = df.y+(df.height/2)

df['geo_x'] = df.geometry.x
df['geo_y'] = df.geometry.y

df.to_csv('intersections.csv')

rows = []

def norm(pri):
    pri = pri.copy()
    pri[:,0] = pri[:,0] - pri[:,0].mean()
    pri[:,0] = pri[:,0] / pri[:,0].max()
    pri[:,1] = pri[:,1] - pri[:,1].mean()
    pri[:,1] = pri[:,1] / pri[:,1].max()
    return pri

def reorder_points(v):
    """Reorder points to ensure the shape is valid. The only works if all of the points
    are on the convex hull, which is true for our shapes. """

    from math import sqrt

    points = list(v.convex_hull.exterior.coords)[:-1]

    # Find the point closest to the origin
    # Norming ensures origin finding is consistent. I guess.
    normed_points = norm(np.array(points)) + 10  # +10 to void div by zero in distance

    mp = next(iter(sorted(normed_points, key=lambda p: sqrt(p[0] ** 2 + p[1] ** 1))))

    # Rotate the list of points so the mp point is first in the list
    mpos = normed_points.tolist().index(mp.tolist())
    points = points[mpos:] + points[:mpos]

    return np.array(points)

for name,g in  df.groupby(['image', 'neighborhood']):

    g = g.sort_values(['image_y', 'image_x'])

    # Y Axis is inverted to match the Y axis orientation of the destination
    # geographic CRS. Adding 2000 to shift the values back to positive, so
    # the sorting algo in reorder_points will have the same sense of where the origin is
    image_p = Polygon([ [r.image_x, -r.image_y+2000] for idx, r in g.iterrows()])

    geo_p = Polygon([[r.geo_x, r.geo_y] for idx, r in g.iterrows()])

    rows.append([name[0], name[1], Polygon(reorder_points(image_p)).wkt, geo_p.wkt])

df = pd.DataFrame(rows, columns='url neighborhood source dest'.split())

df['source'] = df.source.apply(wkt.loads)
df['dest'] = df.dest.apply(wkt.loads)

df.to_csv('poly.csv', index=False)

##
##



df = gpd.GeoDataFrame(df, geometry='source').rename(columns={0:'idx'})
df['id'] = df.index


def geo_to_array(p):
    return np.array([np.array(p) for p in p.exterior.coords[:-1]])


pad = lambda x: np.hstack([x, np.ones((x.shape[0], 1))])
unpad = lambda x: x[:, :-1]


def solve_transform(primary, secondary):
    try:
        # Maybe shapely object
        primary = np.array(primary.exterior.coords)[:-1]

    except AttributeError:
        pass

    try:
        # Maybe shapely object
        secondary = np.array(secondary.exterior.coords)[:-1]
    except AttributeError:
        pass


    # Solve the least squares problem X * A = Y
    # to find our transformation matrix A
    # Padding allows matrix to do translations
    A, res, rank, s = np.linalg.lstsq(pad(primary), pad(secondary), rcond=None)

    A[np.abs(A) < 1e-12] = 0

    return A, primary, secondary


def transform_point(A, x):
    # The extra np.array in pad() presumes this is a point, not a matrix
    # The final [0] unpacks back to a point.

    # Invert Y axis to match CRS
    x[1] = -x[1]

    return unpad(np.dot(pad(np.array([x])), A))[0]


def transform_points(A, x):
    return unpad(np.dot(pad(x), A))


def get_transform(r):
    A, transform = solve_transform(r.source, r.dest)
    return transform


def get_matrix(r):
    A, transform = solve_transform(r.source, r.dest)
    return A


def test_transform(r):
    """Create the transform maxtric, then transform the pri to sec"""
    pri = r.source
    sec = r.dest

    A, pri, sec = solve_transform(pri, sec)

    return Polygon(transform_points(A, pri)).wkt

##
## Testing
##

df['source'] = df.source.apply(reorder_points)
df['dest'] = df.dest.apply(reorder_points)

df['test'] = df.apply(test_transform, axis=1)
#df['source'] = df.source.apply(wkt.loads)
df['test'] = df.test.apply(wkt.loads)
#df['dest'] = df.dest.apply(wkt.loads)

dest = df[['url','dest']].rename(columns={'dest':'geometry'})
dest.to_csv('dest_poly.csv')
test = df[['url','test']].rename(columns={'test':'geometry'})
test.to_csv('test_poly.csv')

