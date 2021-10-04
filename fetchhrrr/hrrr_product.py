#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pathlib
import urllib.parse
from datetime import datetime, timedelta
from typing import Union

import pytz
from osgeo import gdal

from . import PRODUCT_ID_MAP, get_download_dir
from .utils import fetch_from_url, get_hrrr_version, validate_product_id, url_exists, is_url


class HRRRProduct():
    """ Class to describe any HRRR product"""

    __slots__ = [
        '_loc', '_run_time', '_forecast_hour', '_product_id', '_version',
        '_gdal_ds'
    ]

    def __init__(self,
                 loc: Union[str, pathlib.Path],
                 run_time: datetime,
                 forecast_hour: int,
                 product_id: str,
                 gdal_ds: Union[None, gdal.Dataset] = None):
        """ Instantiate the class """

        # Location of product: could be filesystem, HTTP, FTP, etc
        self._loc = loc

        # The HRRR run time of the product
        self._run_time = run_time

        # The forecast hour of the product
        self._forecast_hour = forecast_hour

        # The product id of the product
        validate_product_id(product_id)
        self._product_id = product_id

        # The HRRR version of the product
        self._version = get_hrrr_version(run_time)

        # A GDAL dataset for this object
        self._gdal_ds = gdal_ds

    @property
    def loc(self):
        return self._loc

    @property
    def run_time(self):
        return self._run_time

    @property
    def forecast_hour(self):
        return self._forecast_hour

    @property
    def forecast_time(self):
        return self.run_time + timedelta(hours=self.forecast_hour)

    @property
    def product_id(self):
        return self._product_id

    @property
    def product_name(self):
        return PRODUCT_ID_MAP.get(self.product_id, 'Unknown')

    @property
    def product_version(self):
        return self._version

    @property
    def gdal_ds(self):
        if self._gdal_ds is None:
            self.fetch()
        return self._gdal_ds

    def fetch(self) -> None:
        """ Fetch the HRRR product from its source."""
        # The ultimate goal of this method is to populate the GDAL dataset from source
        if is_url(self.loc):
            print('Downloading HRRR product from URL: %s' % self.loc)

            # Determine path to download to
            download_dir = get_download_dir()
            date_dir = pathlib.Path(
                download_dir,
                '%s' % self.run_time.astimezone(pytz.UTC).strftime('%Y-%m-%d'))
            date_dir.mkdir(parents=False, exist_ok=True)
            url_parse = urllib.parse.urlparse(self.loc)
            file_name = pathlib.PosixPath(url_parse.path).name
            output_path = pathlib.Path(date_dir, file_name)

            try:
                self._loc = fetch_from_url(self.loc, output_path)
            except FileExistsError:
                print('File already exists! Re-using.')
                self._loc = output_path

        # Sanity check that our path exists
        if not self.loc.exists():
            raise FileNotFoundError('Input path does not exist!')

        # Populate GDAL dataset
        self._gdal_ds = gdal.Open(str(self.loc))

    @classmethod
    def from_archive(cls, run_time: datetime, forecast_hour: int,
                     product_id: str):
        validate_product_id(product_id)
        loc = cls.build_archive_url(run_time, forecast_hour, product_id)
        if not url_exists(loc):
            raise ValueError(
                'Could not find HRRR product for this time (URL does not exist: %s'
                % loc)
        return cls(loc, run_time, forecast_hour, product_id)

    @staticmethod
    def build_archive_url(run_time: datetime, forecast_hour: int,
                          product_id: str) -> str:
        """ Build a HRRR archive URL from the runtime, forecast hour, and product ID """

        # TODO: this might not work for the subh products atm
        if product_id == 'subh':
            raise NotImplementedError()

        run_time = run_time.astimezone(pytz.UTC)
        return 'https://storage.googleapis.com/high-resolution-rapid-refresh/hrrr.%s/conus/hrrr.t%02dz.wrf%sf%02d.grib2' % (
            run_time.strftime(r'%Y%m%d'), run_time.hour, product_id,
            forecast_hour)

    def __str__(self):
        return '%s(Run Time: %s, Forecast Time: %s, Type: %s)' % (
            self.__class__.__name__, self.run_time.isoformat(),
            self.forecast_time.isoformat(), self.product_name)

    def __repr__(self):
        return self.__str__()
