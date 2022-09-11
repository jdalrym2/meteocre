#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Representations of MRMS GRIB2 products """

from __future__ import annotations

import uuid
import pathlib
from datetime import datetime
from typing import Union, Tuple, Optional, Any
import numpy as np

import pytz
from osgeo import gdal, osr
import matplotlib as mpl
import matplotlib.image
import matplotlib.pyplot as plt

from . import get_logger
from .colormaps import mrms_mesh_cmap, mrms_rotation_cmap, mrms_refl_cmap, mrms_shi_cmap
from ..utils import gdal_close_dataset


class MRMSProduct:
    """ General class to load MRMS product files in GRIB2 format """

    __slots__ = ['_valid_time', '_loc', '_gdal_ds', '_logger']

    def __init__(self, loc: Union[pathlib.Path, str], valid_time: datetime,
                 gdal_ds: gdal.Dataset):
        """
        Instantiate a MRMS Product from file path, valid time, and GDAL Dataset

        Args:
            loc (Union[pathlib.Path, str]): location to the product on the timesystem
            valid_time (datetime): aware datetime of the product's valid time
            gdal_ds (gdal.Dataset): gdal.Dataset for this product

        Raises:
            ValueError: if the valid time isn't an aware datetime object
        """
        self._loc = pathlib.Path(loc)
        self._valid_time = valid_time
        if self._valid_time.tzinfo is None:
            raise ValueError('Valid time must be contain tzinfo!')
        self._gdal_ds = gdal_ds
        self._logger = get_logger()

    @property
    def loc(self):
        return self._loc

    @property
    def valid_time(self):
        return self._valid_time

    @property
    def gdal_ds(self):
        return self._gdal_ds

    def get_grib_metadata(self) -> dict:
        """
        Returns the metadata dictionary for this GRIB2 file

        Returns:
            dict: GRIB2 metadata dict
        """
        band = self.gdal_ds.GetRasterBand(1)
        meta = band.GetMetadata()
        band = None
        return meta

    def reproject_to_geotiff(
            self,
            proj: str = 'world',
            bounds: Optional[Tuple[float, float, float, float]] = None,
            shapefile: Optional[Union[pathlib.Path, str]] = None,
            save_path: Optional[Union[pathlib.Path,
                                      str]] = None) -> gdal.Dataset:
        """
        Reproject the product to a GeoTIFF Raster

        Args:
            proj (str, optional): Raster projection: 'map' (EPSG:3857) or 'world' (EPSG:4326). Defaults to 'world'.
            bounds (Optional[Tuple[float, float, float, float]], optional): Bounding box in the form (lon_min, lat_min, lon_max, lat_max). Defaults to None.
            shapefile (Optional[Union[pathlib.Path, str]], optional): Path to shapefile to cut to. If bounds is also provided, it will be unused. Defaults to None.
            save_path (Optional[Union[pathlib.Path, str]], optional): Optional save path of the output GeoTIFF raster. Defaults to None.

        Raises:
            ValueError: if proj isn't 'world' or 'map'

        Returns:
            gdal.Dataset: GDAL dataset of the reprojected raster
        """
        # Can only parse bounds or shapefile
        if bounds is not None and shapefile is not None:
            self._logger.warning(
                'Can only specify bounds or cutline shapefile. Prefering shapefile...'
            )
            bounds = None

        # Parse bounds
        if bounds is not None:
            lon_min, lat_min, lon_max, lat_max = bounds
        else:
            lon_min = lat_min = lon_max = lat_max = None

        # Setup src coordinate system
        # Lambert Conformal Conic Projection
        o_srs = osr.SpatialReference()
        o_srs.ImportFromWkt(self.gdal_ds.GetProjection())
        assert len(o_srs.ExportToProj4())

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
                # NOTE: WGS-84 need to be in the form of lat, lon (not lon, lat) for some reason
                (lon_min, lat_min, _), (lon_max, lat_max, _) = [
                    transform.TransformPoint(*e)
                    for e in ((lat_min, lon_min), (lat_max, lon_max))
                ]
        else:
            raise ValueError('Projection must be \'world\' or \'map\'!')
        assert len(dst_srs.ExportToWkt())

        # Set reprojection options
        dst_ds_path = str(
            save_path) if save_path is not None else '/vsimem/%s.tif' % str(
                uuid.uuid4())
        warp_options = dict[str, Any](format='GTiff',
                                      dstSRS=dst_srs.ExportToProj4(),
                                      srcNodata='nan',
                                      dstNodata='nan',
                                      callback=gdal.TermProgress)

        # Bounds-specific options
        if bounds is not None:
            warp_options['outputBounds'] = [lon_min, lat_min, lon_max, lat_max]

        # Shapefile cutline specific options
        if shapefile is not None:
            warp_options['cutlineDSName'] = str(shapefile)
            warp_options['cropToCutline'] = True

        self._logger.info('Reprojecting dataset...')
        dst_ds = gdal.Warp(dst_ds_path, self.gdal_ds, **warp_options)

        return dst_ds

    def get_default_colormap(self):
        """
        Get default matplotlib colormap and norm objects for this MRMS product.

        Meant to be overridden by subclasses.

        Raises:
            NotImplementedError: This method must be overridden by child classes
        """
        raise NotImplementedError(
            'This method must be overridden by child classes!')

    def plot(self, cmap: Any, norm: Any, **reproj_kwargs) -> Tuple[Any, Any]:
        """
        Generate a plot of this MRMS product

        Args:
            cmap (Any): Colormap (given by colormaps module)
            norm (Any): Matplotlib norm (given by colormaps module)

        Returns:
            Tuple[Any, Any]: Matplotlib figure and axis object
        """
        ds = self.reproject_to_geotiff(**reproj_kwargs)
        metadata = self.get_grib_metadata()
        band = ds.GetRasterBand(1)
        im = band.ReadAsArray()
        fig, ax = plt.subplots()
        ax.imshow(im, cmap=cmap, norm=norm)
        fig.colorbar(
            mpl.cm.ScalarMappable(norm=norm, cmap=cmap),     # type: ignore
            ax=ax,
            label=metadata.get('GRIB_UNIT', ''))
        ax.set_title(
            f"{metadata.get('GRIB_COMMENT', 'Unknown Product')}\nValid Time: {self.valid_time.isoformat()}"
        )
        band = None
        gdal_close_dataset(ds)
        return fig, ax

    def plot_default(self, **reproj_kwargs) -> Tuple[Any, Any]:
        """
        Create a plot using this product's default colormap. Not implemented for this base class.

        Returns:
            Tuple[Any, Any]: Matplotlib figure and axis object
        """
        cmap, norm = self.get_default_colormap()
        return self.plot(cmap, norm, **reproj_kwargs)

    def to_png_raster(self, cmap: Any, norm: Any,
                      save_path: Optional[Union[pathlib.Path, str]],
                      **reproj_kwargs) -> np.ndarray:
        """
        Save raster to 8-bit RGBA PNG file.

        Args:
            cmap (Any): Colormap (given by colormaps module)
            norm (Any): Matplotlib norm (given by colormaps module)
            save_path (Optional[Union[pathlib.Path, str]]): Optional PNG file save path.

        Returns:
            np.ndarray: 4-channel RGBA numpy array of raster.
        """
        ds = self.reproject_to_geotiff(**reproj_kwargs)
        band = ds.GetRasterBand(1)
        im = band.ReadAsArray()
        rgb_im = cmap(norm(im))
        if save_path is not None:
            matplotlib.image.imsave(str(save_path), rgb_im)
        band = None
        gdal_close_dataset(ds)
        return rgb_im

    def to_png_raster_default(self, save_path: Optional[Union[pathlib.Path,
                                                              str]],
                              **reproj_kwargs) -> np.ndarray:
        """
        Save raster to 8-bit RGBA PNG file using default colormap.

        Args:
            save_path (Optional[Union[pathlib.Path, str]]): Optional PNG file save path.

        Returns:
            np.ndarray: 4-channel RGBA numpy array of raster.
        """
        cmap, norm = self.get_default_colormap()
        return self.to_png_raster(cmap, norm, save_path, **reproj_kwargs)

    @classmethod
    def from_grib2(cls, grib2_path: Union[pathlib.Path, str]) -> MRMSProduct:
        """
        Create an instance of this class from a GRIB2 file. This is the preferred way
        of instantiating this class.

        Args:
            grib2_path (Union[pathlib.Path, str]): Path to a MRMS GRIB2 file

        Raises:
            FileNotFoundError: If the GRIB2 file is not found.
            ValueError: If the input file is not in GRIB2 format.
            ValueError: If unable to fetch the valid time from the GRIB2 file.

        Returns:
            MRMSProduct: MRMS product represented by the GRIB2 file
        """
        # Sanity check existence
        grib2_path = pathlib.Path(grib2_path)
        if not grib2_path.exists():
            raise FileNotFoundError('Could not find GRIB2 file: %s' %
                                    str(grib2_path))

        # Verify it is a GRIB2 suffix, and whether or not it it gzipped
        is_gz = len(grib2_path.suffixes) >= 2 and grib2_path.suffixes[-2:] == [
            '.grib2', '.gz'
        ]
        if not is_gz and grib2_path.suffix != '.grib2':
            raise ValueError('Input file must be a GRIB2 file! %s' %
                             str(grib2_path))

        # Get GDAL Dataset
        ds = gdal.Open(('/vsigzip/' if is_gz else '') + str(grib2_path))
        if ds is None:
            raise RuntimeError('Dataset invalid! Cannot load MRMS product.')

        # Get Unix timestamp
        band = ds.GetRasterBand(1)
        ts: Optional[str] = band.GetMetadata().get('GRIB_VALID_TIME')
        band = None
        if ts is None:
            raise ValueError('Could not get timestamp from GRIB2 file!')
        ts_dt = datetime.fromtimestamp(int(
            ts.strip().split(' ')[0])).astimezone(pytz.UTC)

        return cls(loc=grib2_path, valid_time=ts_dt, gdal_ds=ds)


class MRMSRotationProduct(MRMSProduct):
    """ Subclass for MRMS Rotation Products """

    def get_default_colormap(self):
        """
        Get default matplotlib colormap and norm objects for this MRMS product.
        """
        return mrms_rotation_cmap()


class MRMSReflectivityProduct(MRMSProduct):
    """ Subclass for MRMS Reflectivity Products """

    def get_default_colormap(self):
        """
        Get default matplotlib colormap and norm objects for this MRMS product.
        """
        return mrms_refl_cmap()


class MRMSSevereHailIndexProduct(MRMSProduct):
    """ Subclass for MRMS Severe Hail Index (SHI) Products """

    def get_default_colormap(self):
        """
        Get default matplotlib colormap and norm objects for this MRMS product.
        """
        return mrms_shi_cmap()


class MRMSMaximumExpectedSizeOfHailProduct(MRMSProduct):
    """ Subclass for MRMS Maximum Expected Size of Hail (MESH) Products """

    def get_default_colormap(self):
        """
        Get default matplotlib colormap and norm objects for this MRMS product.
        """
        return mrms_mesh_cmap()