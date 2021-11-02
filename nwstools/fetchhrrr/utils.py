#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import pathlib
import requests
from typing import Union
import urllib.parse
from datetime import datetime

import pytz
from osgeo import gdal
from tqdm import tqdm

from . import HRRR_V1_INIT_TIME, HRRR_V2_INIT_TIME, HRRR_V3_INIT_TIME, HRRR_V4_INIT_TIME


def get_hrrr_version(run_time: datetime) -> int:
    """ Get the HRRR version corresponding to the run time """
    # Add UTC timezone if not specified
    if run_time.tzinfo is None:
        run_time = run_time.replace(tzinfo=pytz.UTC)

    if run_time > HRRR_V4_INIT_TIME:
        return 4
    elif run_time > HRRR_V3_INIT_TIME:
        return 3
    elif run_time > HRRR_V2_INIT_TIME:
        return 2
    elif run_time > HRRR_V1_INIT_TIME:
        return 1
    else:
        raise ValueError(
            'Invalid run time. Cannot determine HRRR product version.')


def validate_product_id(product_id: str) -> None:
    """ Validate the product id is a valid one for HRRR, otherwise raise an expection """
    if not re.match('/(prs)|(nat)|(sfc)|(subh)$', product_id):
        raise ValueError(
            'Invalid product ID: %s! Must be one of \'prs\', \'nat\', \'sfc\', \'subh\'.'
            % str(product_id))


def is_url(url: str) -> bool:
    return urllib.parse.urlparse(url).scheme in ('http', 'https')


def url_exists(url: str) -> bool:
    """ Return if a URL exists and can be downloaded """
    response = requests.head(url)
    if response.status_code == 200:
        return 'content-length' in response.headers
    else:
        return False


def fetch_from_url(url: str,
                   output_path: Union[str, pathlib.Path],
                   exist_ok: bool = False) -> pathlib.Path:
    """ Fetch a file from a URL """

    # Parse the incoming URL
    parse_result = urllib.parse.urlparse(url)

    # Sanity check URL scheme
    if not is_url(url):
        raise ValueError('URL scheme is not HTTP or HTTPS!')

    # Resolve output path
    output_path = pathlib.Path(output_path).resolve()
    if not output_path.is_dir() and output_path.exists() and not exist_ok:
        raise FileExistsError('Output path already exists!')

    # If the output path was a directory, add a filename
    if output_path.is_dir():
        filename = pathlib.PosixPath(parse_result.path).name
        output_path = pathlib.Path(output_path, filename)

    # Fetch the file
    filesize = int(requests.head(url).headers["Content-Length"])
    with requests.get(url, stream=True) as r, open(
            output_path, 'wb') as f, tqdm(unit='B',
                                          unit_scale=True,
                                          unit_divisor=1024,
                                          total=filesize,
                                          file=sys.stdout,
                                          desc=output_path.name) as progress:
        for chunk in r.iter_content(chunk_size=1024):
            size = f.write(chunk)
            progress.update(size)

    return output_path


def gdal_close_dataset(ds: gdal.Dataset) -> None:
    """ Safely close a GDAL dataset, unlinking internal memory """
    ds_path = ds.GetDescription()
    if 'vsimem' in str(list(pathlib.Path(ds_path).parents)[-2]):
        gdal.Unlink(ds_path)
    ds = None
