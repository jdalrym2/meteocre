#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import requests
import pathlib
from datetime import datetime
from typing import Union
import urllib.parse

import pytz
from tqdm import tqdm


class HRRRProduct():

    __slots__ = []

    def __init__():
        pass

    def fetch() -> None:
        """ Fetch the HRRR product from its source """
        pass

    @staticmethod
    def validate_product_id(product_id: str) -> None:
        """ Validate a HRRR product ID string """
        valid_ids = ('sfc', 'nat', 'prs', 'subh')
        if product_id not in valid_ids:
            raise ValueError('Product ID invalid! Must be one of %s' %
                             valid_ids)

    @classmethod
    def build_archive_url(cls, run_time: datetime, forecast_hour: int,
                          product_id: str) -> str:
        """ Build a HRRR archive URL from the runtime, forecast hour, and product ID """
        cls.validate_product_id(product_id)
        run_time = run_time.astimezone(pytz.UTC)
        if product_id == 'subh':
            raise NotImplementedError()
        return 'https://storage.googleapis.com/high-resolution-rapid-refresh/hrrr.%s/conus/hrrr.t%02dz.wrf%sf%02d.grib2' % (
            run_time.strftime(r'%Y%m%d'), run_time.hour, product_id,
            forecast_hour)

    @staticmethod
    def fetch_from_url(url: str,
                       output_path: Union[str, pathlib.Path],
                       exist_ok: bool = False) -> pathlib.Path:
        """ Fetch a file from a URL """

        # Parse the incoming URL
        parse_result = urllib.parse.urlparse(url)

        # Sanity check URL scheme
        if 'http' not in parse_result.scheme:
            raise RuntimeError('URL scheme is not HTTP or HTTPS!')

        # Resolve output path
        output_path = pathlib.Path(output_path).resolve()
        if not output_path.is_dir() and output_path.exists() and not exist_ok:
            raise RuntimeError('Output path already exists!')

        # If the output path was a directory, add a filename
        if output_path.is_dir():
            filename = pathlib.PosixPath(parse_result.path).name
            output_path = pathlib.Path(output_path, filename)

        # Fetch the file
        filesize = int(requests.head(url).headers["Content-Length"])
        with requests.get(url, stream=True) as r, open(
                output_path,
                'wb') as f, tqdm(unit='B',
                                 unit_scale=True,
                                 unit_divisor=1024,
                                 total=filesize,
                                 file=sys.stdout,
                                 desc=output_path.name) as progress:
            for chunk in r.iter_content(chunk_size=1024):
                size = f.write(chunk)
                progress.update(size)

        return output_path


if __name__ == '__main__':

    run_time = datetime(2018, 5, 1, 18, 0, 0).replace(tzinfo=pytz.UTC)
    forecast_hour = 6
    product_id = 'sfc'

    url = HRRRProduct.build_archive_url(run_time=run_time,
                                        forecast_hour=forecast_hour,
                                        product_id=product_id)

    print(url)
    HRRRProduct.fetch_from_url(url, '.')
