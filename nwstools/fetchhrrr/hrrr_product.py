#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Class to fetch, interpret, and parse HRRR GRIB2 products """

from __future__ import annotations

import re
import uuid
import pathlib
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, List, Optional, Tuple, Union
import warnings

import pytz
import numpy as np
from osgeo import gdal, osr

from .. import GDAL_TO_NUMPY_MAP
from . import PRODUCT_ID_MAP, get_logger, get_download_dir
from .hrrr_inventory import HRRRInventory
from .utils import fetch_from_url, gdal_close_dataset, get_hrrr_version, validate_product_id, url_exists, is_url
from .utils import map_to_pix, get_extreme_points, get_px_in_ellipse


class HRRRProduct():
    """ Class to fetch, interpret, and parse HRRR GRIB2 products """

    __slots__ = [
        '_loc', '_run_time', '_forecast_hour', '_product_id', '_version',
        '_gdal_ds', '_inventory', '_logger'
    ]

    FILE_PATTERN = re.compile(
        r'hrrr\.t([0-1][0-9]|2[0-3])z\.wrf(prs|nat|sfc|subh)f([0-3][0-9]|4[0-8]).grib2'
    )

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

        # Get logger
        self._logger = get_logger()

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
        if is_url(str(self.loc)):
            self._logger.info('Downloading HRRR product from URL: %s' %
                              self.loc)

            # Determine path to download to
            download_dir = get_download_dir()
            date_dir = pathlib.Path(
                download_dir,
                '%s' % self.run_time.astimezone(pytz.UTC).strftime('%Y-%m-%d'))
            date_dir.mkdir(parents=False, exist_ok=True)
            url_parse = urllib.parse.urlparse(str(self.loc))
            file_name = pathlib.PosixPath(url_parse.path).name
            output_path = pathlib.Path(date_dir, file_name)

            try:
                self._loc = fetch_from_url(str(self.loc), output_path)
            except FileExistsError:
                self._logger.info('File already exists! Re-using.')
                self._loc = output_path

        # Sanity check that our path exists
        if not pathlib.Path(self.loc).exists():
            raise FileNotFoundError('Input path does not exist!')

        # Populate GDAL dataset
        self._gdal_ds = gdal.Open(str(self.loc))

    @classmethod
    def from_archive(cls, run_time: datetime, forecast_hour: int,
                     product_id: str) -> HRRRProduct:
        validate_product_id(product_id)
        loc = cls.build_archive_url(run_time, forecast_hour, product_id)
        return cls(loc, run_time, forecast_hour, product_id)

    @classmethod
    def from_grib2(cls, file_path: Union[str, pathlib.Path]) -> HRRRProduct:
        """
        Load a HRRR product from a GRIB2 file.

        Args:
            file_path (Union[str, pathlib.Path]): Path to GRIB2 file.

        Raises:
            FileNotFoundError: If the provided file path does not exist.
            ValueError: If the file naming convention is not recognized.
            ValueError: If the GRIB metadata reference time could not be read.
            ValueError: If the GRIB metadata valid time could not be read.

        Returns:
            HRRRProduct: HRRR product object from file
        """
        # Get module logger
        logger = get_logger()

        # Sanity check file path
        file_path = pathlib.Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError('File not found: %s' % str(file_path))

        # Validate filename
        m = cls.FILE_PATTERN.match(file_path.name)
        if m is None:
            raise ValueError(
                'Unsupported or unknown file naming convention. See %s.FILE_PATTERN. %s'
                % (cls.__name__, file_path.name))

        # Get data from filename
        utc_hour, product_id, forecast_hour = int(m.group(1)), m.group(2), int(
            m.group(3))

        # Load GDAL dataset from file
        gdal_ds = gdal.Open(str(file_path))

        # Extract necessary metadata
        metadata = gdal_ds.GetRasterBand(1).GetMetadata()
        try:
            grib_ref_timestamp = int(
                metadata['GRIB_REF_TIME'].lstrip().split(' ')[0])
            grib_ref_time = datetime.fromtimestamp(
                grib_ref_timestamp).astimezone(pytz.UTC)
        except Exception:
            raise ValueError('Could not get GRIB reference time!')
        try:
            grib_valid_timestamp = int(
                metadata['GRIB_REF_TIME'].lstrip().split(' ')[0])
            grib_valid_time = datetime.fromtimestamp(
                grib_valid_timestamp).astimezone(pytz.UTC)
        except Exception:
            raise ValueError('Could not get GRIB valid time!')

        # Sanity check UTC hour and forecast error, throw warnings if mismatch
        if grib_ref_time.hour != utc_hour:
            logger.warning(
                'GRIB2 reference time does not match UTC hour from filename! %s vs. %s'
                % (grib_ref_time.hour, utc_hour))
        expected_fh = (grib_valid_time - grib_ref_time).total_seconds() / 3600
        if expected_fh != forecast_hour:
            logger.warning(
                'Expected forcast hour based on GRIB metadata does not match filename! %s vs. %s'
                % (expected_fh, forecast_hour))

        # Return class instance!
        return cls(loc=file_path,
                   run_time=grib_ref_time,
                   forecast_hour=forecast_hour,
                   product_id=product_id,
                   gdal_ds=gdal_ds)

    @staticmethod
    def build_archive_url(run_time: datetime, forecast_hour: int,
                          product_id: str) -> str:
        """ Build a HRRR archive URL from the runtime, forecast hour, and product ID """

        # TODO: this might not work for the subh products atm
        if product_id == 'subh':
            raise NotImplementedError()

        run_time = run_time.astimezone(pytz.UTC)
        valid_locs = (
            ('https://storage.googleapis.com/high-resolution-rapid-refresh/'
             'hrrr.%s/conus/hrrr.t%02dz.wrf%sf%02d.grib2' %
             (run_time.strftime(r'%Y%m%d'), run_time.hour, product_id,
              forecast_hour)),
            ('https://noaa-hrrr-bdp-pds.s3.amazonaws.com/'
             'hrrr.%s/conus/hrrr.t%02dz.wrf%sf%02d.grib2' %
             (run_time.strftime(r'%Y%m%d'), run_time.hour, product_id,
              forecast_hour)),
        )

        # Search all provided archives for the file
        loc = None
        for _loc in valid_locs:
            if url_exists(_loc):
                loc = _loc
                break
        if loc is None:
            raise ValueError('Could not find HRRR product for this time')
        return loc

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
        bounds: Optional[Tuple[float, float, float, float]] = None
    ) -> gdal.Dataset:
        """ Return GDAL dataset for a specific set of product indices
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
        else:
            lon_min = lat_min = lon_max = lat_max = None

        # Setup src coordinate system
        # Lambert Conformal Conic Projection
        o_srs = osr.SpatialReference()
        o_srs.ImportFromProj4(
            '+proj=lcc +units=m +a=6370000.0 +b=6370000.0 '
            '+lat_1=38.5 +lat_2=38.5 +lat_0=38.5 +lon_0=-97.5 +nadgrids=@null')
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

        # Extract bands from gdal dataset
        nat_mem_path = '/vsimem/%s' % str(uuid.uuid4())
        nat_ds = gdal.Translate(nat_mem_path,
                                self.gdal_ds,
                                format='MEM',
                                bandList=product_idx_list,
                                outputSRS=o_srs.ExportToProj4(),
                                noData='nan',
                                callback=gdal.TermProgress)

        # Suppress warnings
        h = gdal.PopErrorHandler()
        gdal.PushErrorHandler('CPLQuietErrorHandler')

        # Convert to destination coordinate system
        dst_mem_path = '/vsimem/%s' % str(uuid.uuid4())
        warp_options = dict[str, Any](format='MEM',
                                      dstSRS=dst_srs.ExportToProj4(),
                                      srcNodata='nan',
                                      dstNodata='nan',
                                      callback=gdal.TermProgress)
        if bounds is not None:
            warp_options['outputBounds'] = [lon_min, lat_min, lon_max, lat_max]
        dst_ds = gdal.Warp(dst_mem_path, nat_ds, **warp_options)

        # Unsuppress warnings
        gdal.PopErrorHandler()
        if h is not None:
            gdal.PushErrorHandler(h)

        # Close dataset while unlinking in-RAM memory
        gdal_close_dataset(nat_ds)

        return dst_ds

    def to_numpy_ar(
        self,
        product_idx_list: List[int],
        proj: str = 'world',
        bounds: Optional[Tuple[float, float, float,
                               float]] = None) -> np.ndarray:
        """
        For a set of product indices, return a numpy array of the values.

        Args:
            product_idx_list (List[int]): List of product indicies. Use HRRRProduct.inventory to search if necessary.
            proj (str, optional): Map projection to use: 'map' or 'world'. Defaults to 'world'.
            bounds (Optional[Tuple[float, float, float, float]], optional): Optional bounding box (lon_min, lat_min, lon_max, lat_max).
                Defaults to None.

        Returns:
            np.ndarray: Output 3D numpy array for the set of products.
        """
        # Load a GDAL dataset in the correct projection and with the desired
        # product idxs
        ds = self.get_ds_for_product_idx(product_idx_list, proj, bounds)
        w, h, n_channels = ds.RasterXSize, ds.RasterYSize, ds.RasterCount
        dt = ds.GetRasterBand(1).DataType

        # Prepare output array
        output = np.empty((h, w, n_channels),
                          dtype=GDAL_TO_NUMPY_MAP.get(dt, np.float32))

        # Fill output array
        for idx in range(ds.RasterCount):
            mem_band = ds.GetRasterBand(idx + 1)
            output[:, :, idx] = mem_band.ReadAsArray()
            mem_band = None

        # Profit
        return output

    def to_geotiff(
            self,
            output_path: Union[str, pathlib.Path],
            product_idx_list: List[int],
            proj: str = 'world',
            bounds: Optional[Tuple[float, float, float,
                                   float]] = None) -> None:
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

    def query_for_pts(self, product_idx_list, pt_ar):
        """ Query the HRRR product raster for a set of points """
        # Get bounds based on pt array
        pt_ar = np.array(pt_ar)
        lat_max, lat_min = np.max(pt_ar[:, 0]) + 0.1, np.min(pt_ar[:, 0]) - 0.1
        lon_max, lon_min = np.max(pt_ar[:, 1]) + 0.1, np.min(pt_ar[:, 1]) - 0.1
        bounds = lon_min, lat_min, lon_max, lat_max

        # Fetch the dataset for these points
        ds = self.get_ds_for_product_idx(product_idx_list,
                                         proj='world',
                                         bounds=bounds)

        # Get raster points for ds
        x, y = map_to_pix(ds.GetGeoTransform(), pt_ar[:, 1], pt_ar[:, 0])

        # Bounds checking and trimming
        v = (x >= 0) & (y >= 0) & (x < ds.RasterXSize) & (y < ds.RasterYSize)
        if len(v) < pt_ar.shape[0]:
            warnings.warn(
                'query_for_pts: some points provided were out of bounds!',
                RuntimeWarning)
        valid_x, valid_y = x[v], y[v]

        # Prepare output list
        output = np.zeros((pt_ar.shape[0], ds.RasterCount),
                          dtype=GDAL_TO_NUMPY_MAP.get(
                              ds.GetRasterBand(1).DataType, np.float32))
        for idx in range(ds.RasterCount):
            mem_band = ds.GetRasterBand(idx + 1)
            output[v, idx] = mem_band.ReadAsArray()[valid_y, valid_x]
            mem_band = None

        # Safely close the dataset
        gdal_close_dataset(ds)

        # Return
        return output

    def query_for_radius(self, product_idx_list, lat, lon, radius_km):
        """ Query the HRRR product raster for a set of points """
        # Get bounds based on pt array
        bounds = get_extreme_points(lat, lon, radius_km)

        # Fetch the dataset for these points
        ds = self.get_ds_for_product_idx(product_idx_list,
                                         proj='world',
                                         bounds=bounds)

        # Find points that are contained in our radius, now in pixel space
        _, _, lon_max, lat_max = bounds
        test_pts = np.array([
            (lat, lon),
            (lat_max, lon_max),
        ])
        test_pts_x, test_pts_y = map_to_pix(ds.GetGeoTransform(),
                                            test_pts[:, 1], test_pts[:, 0])
        c_x, c_y = test_pts_x[0], test_pts_y[0]
        ax_x = test_pts_x[1] - test_pts_x[0]
        ax_y = test_pts_y[1] - test_pts_y[0]

        # Use this to get all the pixel values that encompass this radius
        pt_ar = get_px_in_ellipse((c_x, c_y), ax_x, ax_y)
        x, y = pt_ar[:, 0], pt_ar[:, 1]

        # Bounds checking and trimming
        v = (x >= 0) & (y >= 0) & (x < ds.RasterXSize) & (y < ds.RasterYSize)
        if len(v) < pt_ar.shape[0]:
            warnings.warn(
                'query_for_pts: some points provided were out of bounds!',
                RuntimeWarning)
        valid_x, valid_y = x[v], y[v]

        # Prepare output list
        output = np.zeros((pt_ar.shape[0], ds.RasterCount),
                          dtype=GDAL_TO_NUMPY_MAP.get(
                              ds.GetRasterBand(1).DataType, np.float32))
        for idx in range(ds.RasterCount):
            mem_band = ds.GetRasterBand(idx + 1)
            output[v, idx] = mem_band.ReadAsArray()[valid_y, valid_x]
            mem_band = None

        # Safely close the dataset
        gdal_close_dataset(ds)

        # Return
        return output