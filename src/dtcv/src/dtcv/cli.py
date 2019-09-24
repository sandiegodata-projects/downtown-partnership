import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from .clean import clean_file_annotations, clean_counts
from .counts import file_df, count_df
from .gcp import gcp_df, gcp_transform_df, intersections_df

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

    parser = argparse.ArgumentParser(description='')

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

    parser.add_argument('-c', '--counts', action='store_true', help='Process counts')

    parser.add_argument('-g', '--gcp', action='store_true', help='Process ground control points')

    parser.add_argument('-f', '--final', action='store_true', help='Create final datasets')

    parser.add_argument('-i', '--intersections', default=None, help='Path to intersections file')

    parser.add_argument('source_dir', default=None, nargs='?',
                        help='Source directory for GCP files. If none, get files from S3')
    parser.add_argument('dest_dir', default=None, nargs='?',
                        help='Destination directory for output files')

    pa = parser.parse_args()

    # If only one if given, it is the destination directory
    if (pa.source_dir and not pa.dest_dir):
        pa.source_dir, pa.dest_dir = pa.dest_dir, pa.source_dir

    return pa


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def run():
    """Entry point for console_scripts
    """

    args = parse_args(sys.argv[1:])
    setup_logging(args.loglevel)

    if args.dest_dir:
        dest = Path(args.dest_dir)
    else:
        dest = Path.cwd()

    if not dest.exists():
        dest.mkdir(parents=True)

    if args.source_dir:
        source = Path(args.source_dir)
    else:
        source = None

    if not any([args.gcp, args.counts, args.final ]):
        args.gcp, args.counts, args.final = True, True, True

    if args.gcp:
        load_gcp(args, source, dest)

    if args.counts:
        load_counts(args, source, dest)

    if args.final:
        run_clean_files(args, source, dest)
        run_clean_counts(args, source, dest)


if __name__ == "__main__":
    run()


def load_gcp(args, source, dest):
    if not dest.exists():
        dest.mkdir(parents=True)

    intr_gpd = intersections_df(args.intersections)

    gcp = gcp_df(source)
    gcp_out = dest.joinpath('raw_gcp.csv')
    _logger.info(f'Writing {gcp_out}')
    gcp.to_csv(gcp_out, index=False)

    tf = gcp_transform_df(intr_gpd, gcp)
    tf_out = dest.joinpath('gcp_transforms.csv')
    _logger.info(f'Writing {tf_out}')
    tf.to_csv(tf_out, index=False)


def load_counts(args, source, dest):
    fdf_out = dest.joinpath('raw_file_annotations.csv')
    _logger.info(f'Writing {fdf_out}')
    fdf = file_df(source)
    fdf.to_csv(fdf_out)

    fdf_out = dest.joinpath('raw_count_annotations.csv')
    _logger.info(f'Writing {fdf_out}')
    fdf = count_df(source)
    fdf.to_csv(fdf_out)


def run_clean_files(args, source, dest):

    fdf_out = dest.joinpath('raw_file_annotations.csv')

    file_df = pd.read_csv(fdf_out)

    fdf_out = dest.joinpath('files.csv')
    _logger.info(f'Writing {fdf_out}')
    df = clean_file_annotations(file_df)
    df.to_csv(fdf_out)


def run_clean_counts(args, source, dest):

    rc_df = pd.read_csv(dest.joinpath('raw_count_annotations.csv'))

    f_df = pd.read_csv(dest.joinpath('files.csv'))

    tf_df = pd.read_csv(dest.joinpath('gcp_transforms.csv'))

    df = clean_counts(rc_df, f_df, tf_df)

    df_out = dest.joinpath('counts.csv')
    _logger.info(f'Writing {df_out}')

    df.to_csv(df_out)
