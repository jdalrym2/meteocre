#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import pathlib
import requests
from typing import Union
import urllib.parse

import numpy as np
from osgeo import gdal
from tqdm import tqdm


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
    """
    Safely close a GDAL dataset, unlinking internal memory

    Args:
        ds (gdal.Dataset): GDAL dataset to destroy
    """
    ds.FlushCache()
    ds_path = ds.GetDescription()
    if 'vsimem' in str(list(pathlib.Path(ds_path).parents)[-2]):
        gdal.Unlink(ds_path)
    ds = None     # type: ignore


def map_to_pix(xform: list[float],
               x_m: Union[float, list[float], np.ndarray],
               y_m: Union[float, list[float], np.ndarray],
               round: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """ Convert x/y in map projection (WGS84: lon/lat) to pixel x, y coordinates """

    # Input validation, either both float or both lists
    assert not (isinstance(x_m, float) ^ isinstance(y_m, float))
    if isinstance(x_m, float):
        x_m = [x_m]
    if isinstance(y_m, float):
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
    return x_p, y_p


def pix_to_map(
    xform: list[float], x_p: Union[float, list[float], np.ndarray],
    y_p: Union[float, list[float],
               np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """ Convert pixel x, y coordinates to x/y in map projection (WGS84: lon/lat) """
    # Input validation, either both float or both lists
    assert not (isinstance(x_p, float) ^ isinstance(y_p, float))
    if isinstance(x_p, float):
        x_p = [x_p]
    if isinstance(y_p, float):
        y_p = [y_p]
    x_p, y_p = np.array(x_p), np.array(y_p)
    assert x_p.ndim == y_p.ndim == 1
    assert len(x_p) == len(y_p)

    # Do the math!
    x_m = xform[0] + xform[1] * x_p + xform[2] * y_p
    y_m = xform[3] + xform[4] * x_p + xform[5] * y_p

    # Return
    return x_m, y_m


def get_extreme_points(lat: float, lon: float,
                       radius_km: float) -> tuple[float, float, float, float]:
    """ Given a lat, lon pair, find bounds that enclose a given radius """
    R = 6367     # radius of Earth, km
    lat_dist = np.degrees(radius_km / R)
    lon_dist = lat_dist / np.cos(np.radians(lat))
    lat_max, lat_min = lat + lat_dist, lat - lat_dist
    lon_max, lon_min = lon + lon_dist, lon - lon_dist
    return lon_min, lat_min, lon_max, lat_max


def get_px_in_ellipse(center: tuple[int, int], a: float,
                      b: float) -> np.ndarray:
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