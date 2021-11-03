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
import numpy as np
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


def map_to_pix(
        xform: list[float],
        x_m: Union[float, list[float]],
        y_m: Union[float, list[float]],
        round: bool = True
) -> Union[tuple[int, int], tuple[np.array, np.array]]:
    """ Convert x/y in map projection (WGS84: lon/lat) to pixel x, y coordinates """

    # Input validation, either both float or both lists
    assert not (isinstance(x_m, float) ^ isinstance(y_m, float))
    is_float = isinstance(x_m, float)
    if is_float:
        x_m = [x_m]
        y_m = [y_m]
    x_m, y_m = np.array(x_m), np.array(y_m)
    assert x_m.ndim == y_m.ndim == 1
    assert len(x_m) == len(y_m)

    # Do the math!
    det = 1 / (xform[1] * xform[5] - xform[2] * xform[4])
    x_p = det * (xform[5] * (x_m - xform[0]) - xform[2] * (y_m - xform[3]))
    y_p = det * (xform[1] * (y_m - xform[3]) - xform[4] * (x_m - xform[0]))

    # Round pixel values, if desired
    if round:
        x_p, y_p = np.round(x_p).astype(int), np.round(y_p).astype(int)

    # Return
    if is_float:
        return x_p[0], y_p[0]
    else:
        return x_p, y_p


def pix_to_map(
        xform: list[float], x_p: float,
        y_p: float) -> Union[tuple[float, float], tuple[np.array, np.array]]:
    """ Convert pixel x, y coordinates to x/y in map projection (WGS84: lon/lat) """
    # Input validation, either both float or both lists
    assert not (isinstance(x_p, float) ^ isinstance(y_p, float))
    is_float = isinstance(x_p, float)
    if is_float:
        x_p = [x_p]
        y_p = [y_p]
    x_p, y_p = np.array(x_p), np.array(y_p)
    assert x_p.ndim == y_p.ndim == 1
    assert len(x_p) == len(y_p)

    # Do the math!
    x_m = xform[0] + xform[1] * x_p + xform[2] * y_p
    y_m = xform[3] + xform[4] * x_p + xform[5] * y_p

    # Return
    if is_float:
        return x_m[0], y_m[0]
    else:
        return x_m, y_m


def get_extreme_points(lat: float, lon: float,
                       radius_km: float) -> tuple[float, float, float, float]:
    """ Given a lat, lon pair, find bounds that enclose a given radius """
    R = 6367  # radius of Earth, km
    lat_dist = np.degrees(radius_km / R)
    lon_dist = lat_dist / np.cos(np.radians(lat))
    lat_max, lat_min = lat + lat_dist, lat - lat_dist
    lon_max, lon_min = lon + lon_dist, lon - lon_dist
    return lon_min, lat_min, lon_max, lat_max


def get_px_in_ellipse(center: tuple[int], a: Union[int, float],
                      b: Union[int, float]) -> np.array:
    """ Get the set of pixels that fall within ellipse defined with a, b """

    # Start by getting array as if centered at (0, 0)
    ax_m = max(a, b)
    grid = np.mgrid[-ax_m:(ax_m + 1), -ax_m:(ax_m + 1)]
    grid_sq = np.square(grid)
    v = (grid_sq[0, :, :] / a**2 + grid_sq[1, :, :] / b**2) <= 1
    x, y = np.where(v)
    pts = grid[:, y, x].T

    # Finally, add the center
    pts[:, 0] += center[0]
    pts[:, 1] += center[1]

    return pts