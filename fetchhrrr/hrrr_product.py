#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Class to fetch, interpret, and parse HRRR GRIB2 products """

import uuid
import pathlib
import urllib.parse
from datetime import datetime, timedelta
from typing import Union

import pytz
from osgeo import gdal, osr

from . import PRODUCT_ID_MAP, get_download_dir
from .hrrr_inventory import HRRRInventory
from .utils import fetch_from_url, gdal_close_dataset, get_hrrr_version, validate_product_id, url_exists, is_url


class HRRRProduct():
    """ Class to fetch, interpret, and parse HRRR GRIB2 products """

    __slots__ = [
        '_loc', '_run_time', '_forecast_hour', '_product_id', '_version',
        '_gdal_ds', '_inventory'
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

        # Inventory, only initialize if desired
        self._inventory = None

    @property
    def loc(self) -> Union[str, pathlib.Path]:
        return self._loc

    @property
    def run_time(self) -> datetime:
        return self._run_time

    @property
    def forecast_hour(self) -> int:
        return self._forecast_hour

    @property
    def forecast_time(self) -> datetime:
        return self.run_time + timedelta(hours=self.forecast_hour)

    @property
    def product_id(self) -> str:
        return self._product_id

    @property
    def product_name(self) -> str:
        return PRODUCT_ID_MAP.get(self.product_id, 'Unknown')

    @property
    def product_version(self) -> int:
        return self._version

    @property
    def gdal_ds(self) -> gdal.Dataset:
        if self._gdal_ds is None:
            self.fetch()
        return self._gdal_ds

    @property
    def inventory(self) -> HRRRInventory:
        if self._inventory is None:
            self._inventory = HRRRInventory(self)
        return self._inventory

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

    def get_ds_for_product_idx(
            self,
            product_idx_list: list[int],
            proj: str = 'world',
            bounds: Union[None, list[Union[int,
                                           float]]] = None) -> gdal.Dataset:
        """ 
            Return GDAL dataset for a specific set of product indices
            - proj = 'map' -> EPSG:3857
            - proj = 'world' -> EPSG:4326

            - bounds = None
            - bounds = [lon_min, lat_min, lon_max, lat_max]
        """
        """
        How to get the HRRR PROJ4 string

        HRRR Domain Params are at: https://rapidrefresh.noaa.gov/hrrr/HRRR_conus.domain.txt

        Then execute the following:

            pip install wrf-python

        >>> import wrf
        >>> params = dict(
                TRUELAT1=38.5,
                TRUELAT2=38.5,
                MOAD_CEN_LAT=38.5,
                STAND_LON=-97.5,
                POLE_LAT=90.0,
                POLE_LON=0
        )
        >>> wrf.LambertConformal(**params).proj4()

        '+proj=lcc +units=m +a=6370000.0 +b=6370000.0 +lat_1=38.5 +lat_2=38.5
        +lat_0=38.5 +lon_0=-97.5 +nadgrids=@null'
        """

        # Parse bounds
        if bounds is not None:
            lon_min, lat_min, lon_max, lat_max = bounds

        # Setup src coordinate system
        # Lambert Conformal Conic Projection
        o_srs = osr.SpatialReference()
        o_srs.ImportFromProj4(
            '+proj=lcc +units=m +a=6370000.0 +b=6370000.0 +lat_1=38.5 +lat_2=38.5 +lat_0=38.5 +lon_0=-97.5 +nadgrids=@null'
        )
        assert len(o_srs.ExportToWkt())

        # Setup destination coordinate system
        dst_srs = osr.SpatialReference()
        if proj == 'world':
            dst_srs.ImportFromEPSG(4326)
        elif proj == 'map':
            dst_srs.ImportFromEPSG(3857)

            # If map... transform bounds to meters
            if bounds is not None:
                wgs84_srs = osr.SpatialReference()
                wgs84_srs.ImportFromEPSG(4326)
                transform = osr.CoordinateTransformation(wgs84_srs, dst_srs)
                (lon_min, lat_min,
                 _), (lon_max, lat_max,
                      _) = transform.TransformPoints([(lon_min, lat_min),
                                                      (lon_max, lat_max)])
        else:
            raise ValueError('Projection must be \'world\' or \'map\'!')
        assert len(dst_srs.ExportToWkt())

        # Convert GRIB2 product into a GeoTIFF with native coordinate system
        nat_mem_path = '/vsimem/%s.tif' % str(uuid.uuid4())
        nat_ds = gdal.Translate(nat_mem_path,
                                self.gdal_ds,
                                format='GTiff',
                                bandList=product_idx_list,
                                outputSRS=o_srs.ExportToProj4(),
                                noData='nan')

        # Suppress warnings
        h = gdal.PopErrorHandler()
        gdal.PushErrorHandler('CPLQuietErrorHandler')

        # Convert to destination coordinate system
        dst_mem_path = '/vsimem/%s.tif' % str(uuid.uuid4())
        warp_options = dict(format='GTiff',
                            dstSRS=dst_srs.ExportToProj4(),
                            srcNodata='nan',
                            dstNodata='nan')
        if bounds is not None:
            warp_options.update(
                dict(outputBounds=[lon_min, lat_min, lon_max, lat_max]))
        dst_ds = gdal.Warp(dst_mem_path, nat_ds, **warp_options)

        # Unsuppress warnings
        gdal.PopErrorHandler()
        if h is not None:
            gdal.PushErrorHandler(h)

        # Close dataset while unlinking in-RAM memory
        gdal_close_dataset(nat_ds)

        return dst_ds

    def to_geotiff(
            self,
            output_path: Union[str, pathlib.Path],
            product_idx_list: list[int],
            proj: str = 'world',
            bounds: Union[None, list[Union[int, float]]] = None) -> None:
        """ Export product as a GeoTiff """

        # Load a GDAL dataset in the correct projection and with the desired
        # product idxs
        in_ds = self.get_ds_for_product_idx(product_idx_list, proj, bounds)
        w, h, n_channels = in_ds.RasterXSize, in_ds.RasterYSize, in_ds.RasterCount
        dt = in_ds.GetRasterBand(1).DataType

        # Save GeoTIFF raster data
        driver = gdal.GetDriverByName('GTiff')
        out_ds = driver.Create(str(output_path), w, h, n_channels, dt)
        for band_idx in range(out_ds.RasterCount):
            mem_band = out_ds.GetRasterBand(1 + band_idx)
            mem_band.WriteArray(
                in_ds.GetRasterBand(1 + band_idx).ReadAsArray())
            mem_band.FlushCache()
            mem_band = None

        # Set projection and geotransform
        out_ds.SetProjection(in_ds.GetProjection())
        out_ds.SetGeoTransform(in_ds.GetGeoTransform())

        # Close generated dataset and free in-RAM memory
        gdal_close_dataset(in_ds)
        out_ds = None