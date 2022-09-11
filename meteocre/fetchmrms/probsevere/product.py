#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Class for handling a ProbSevere product JSON file. Allows geospatial filtering of ProbSevere features.

See here for ProbSevere training materials:
https://cimss.ssec.wisc.edu/severe_conv/training/training.html

See here for file format description:
https://cimss.ssec.wisc.edu/severe_conv/training/ProbSevere_v2_FileDescription.pdf
"""

from __future__ import annotations
import json

import pathlib
from datetime import datetime
from typing import Union, Optional, List

import pytz
from osgeo import gdal, ogr

from . import get_logger
from .feature import ProbSevereFeature


class ProbSevereProduct:
    """ Class for handling a ProbSevere product JSON file. Allows geospatial filtering of ProbSevere features. """

    __slots__ = [
        '_ogr_ds', '_valid_time', '_spatial_filter', '_features',
        '_feature_count', '_logger'
    ]

    def __init__(self, ogr_ds: gdal.Dataset):
        """
        Initialize from a GDAL Dataset of the JSON.
        Users should not call this directory, but instead use a `from_` classmethod.

        Args:
            ogr_ds (gdal.Dataset): OSGEO Dataset from the JSON object. Ensure NATIVE_DATA=YES is set upon Open.

        Raises:
            RuntimeError: If NATIVE_DATA is not found.
            RuntimeError: If NATIVE_DATA cannot be decoded.
            ValueError: If validTime is not found within NATIVE_DATA.
            ValueError: If validTime string cannot be parsed.
        """
        # Get logger
        self._logger = get_logger()

        # Persist dataset
        self._ogr_ds = ogr_ds     # type: gdal.Dataset

        # Fetch valid time (also serves as a sanity check for the dataset's validity)
        try:
            layer_metadata = ogr_ds.GetLayer(0).GetMetadata(
                'NATIVE_DATA')['NATIVE_DATA']
        except (AttributeError, KeyError):
            raise RuntimeError(
                'Could not fetch native data for dataset layer! Is this a valid ProbSevere dataset?'
            )
        try:
            valid_time_str = json.loads(layer_metadata).get('validTime')
        except (TypeError, json.JSONDecodeError):
            raise RuntimeError('Could not decode native data! %s' %
                               repr(layer_metadata))
        if valid_time_str is None:
            raise ValueError(
                'Could not find validTime from dataset native data! Is this a valid ProbSevere dataset?'
            )
        try:
            self._valid_time = datetime.strptime(
                valid_time_str, '%Y%m%d_%H%M%S UTC').replace(
                    tzinfo=pytz.UTC)     # type: datetime
        except ValueError as e:
            raise ValueError('Could not parse dataset valid time str: %s.' %
                             str(e))

        # Default attributes
        self._spatial_filter = None     # type: Optional[ogr.Geometry]
        self._features = None     # type: Optional[List[ProbSevereFeature]]
        self._feature_count = None     # type: Optional[int]

    @property
    def ogr_ds(self) -> gdal.Dataset:
        """
        Return the OSGEO Dataset for this product.

        Returns:
            gdal.Dataset: OSGEO Dataset for this product
        """
        return self._ogr_ds

    @property
    def ogr_layer(self) -> ogr.Layer:
        """
        Return the OGR Layer for this object

        Returns:
            ogr.Layer: OGR Layer for this product
        """
        # Note that a ProbSevere GeoJSON has only one "layer"
        return self._ogr_ds.GetLayer(0)

    @property
    def valid_time(self) -> datetime:
        """
        Return this product's valid time.

        Returns:
            datetime: Product valid time (timezone aware)
        """
        return self._valid_time

    @property
    def filter(self) -> Optional[ogr.Geometry]:
        """
        Get the set geospatial filter on this product.
        This can be changed with the `set_*_filter` or `reset_filter` methods.

        Returns:
            Optional[ogr.Geometry]: OGR Geometry for this filter (ogr.wkbPolygon)
        """
        return self._spatial_filter

    @property
    def has_spatial_filter(self) -> bool:
        """
        Returns whether or not this product has an active geospatial filter.

        Returns:
            bool: True if this product has an active geospatial filter.
        """
        return self._spatial_filter is not None

    def __len__(self):
        # Compute or recompute feature count
        if self._feature_count is None:
            self._feature_count = self.ogr_layer.GetFeatureCount()
        return self._feature_count

    def __getitem__(self, n: int):
        return self.features[n]

    def __str__(self):
        return '<%s; Valid Time: %s; Features: %d (%s)>' % (
            self.__class__.__name__, self._valid_time.isoformat(), len(self),
            'Filtered' if self.has_spatial_filter else 'Not Filtered')

    def __repr__(self):
        return self.__str__()

    @property
    def features(self) -> List[ProbSevereFeature]:
        """
        Compute and return a list of ProbSevereFeatures for this product.
        This list is persisted until the active geospatial filter is changed.

        Returns:
            List[ProbSevereFeature]: List of ProbSevereFeatures under the active geospatial filter
        """
        # If self._features is None, then the features
        # haven't been computed or need to be recomputed
        if self._features is None:
            self._features = []
            for _ in range(len(self)):
                this_feat = self.ogr_layer.GetNextFeature(
                )     # type: ogr.Feature
                self._features.append(
                    ProbSevereFeature.from_ogr_feature(self.valid_time,
                                                       this_feat))

        return self._features

    def set_spatial_filter(self, f: Optional[ogr.Geometry]) -> None:
        """
        Set the active geospatial filter for this product.

        Args:
            f (Optional[ogr.Geometry]): OGR Polygon Geometry for the filter. None for no filter.
        """

        # Sanity check OGR polygon
        if f is not None and f.GetGeometryType != ogr.wkbPolygon:
            raise ValueError('Spatial filter must be a polygon! Got: %s' %
                             f.GetGeometryName())

        # Set filter attribute
        self._spatial_filter = f

        # Reset features and feature count, they must
        # be computed again
        self._features = None
        self._feature_count = None

        # Set spatial filter (None clears the filter)
        # Setting the filter clears GetNextFeature such
        # that we can iterate over features
        self.ogr_layer.SetSpatialFilter(f)

    def set_bbox_filter(self, lat_min: float, lon_min: float, lat_max: float,
                        lon_max: float) -> None:
        """
        Set a bounding box geospatial filter.

        Args:
            lat_min (float): Minimum latitude (WGS84 decimal degrees)
            lon_min (float): Minimum longitude (WGS84 decimal degrees)
            lat_max (float): Maximum latitude (WGS84 decimal degrees)
            lon_max (float): Maximum longitude (WGS84 decimal degrees)
        """
        # Create OGR Geometry from bounds
        ogr_ring = ogr.Geometry(ogr.wkbLinearRing)
        ogr_ring.AddPoint_2D(lon_min, lat_max)
        ogr_ring.AddPoint_2D(lon_max, lat_max)
        ogr_ring.AddPoint_2D(lon_max, lat_min)
        ogr_ring.AddPoint_2D(lon_min, lat_min)
        ogr_ring.AddPoint_2D(lon_min, lat_max)
        ogr_poly = ogr.Geometry(ogr.wkbPolygon)
        ogr_poly.AddGeometry(ogr_ring)

        # Set spatial filter
        self.set_spatial_filter(ogr_poly)

    def reset_spatial_filter(self) -> None:
        """
        Clear the active geospatial filter
        """
        self.set_spatial_filter(None)

    @classmethod
    def from_geojson(
            cls, geojson_path: Union[pathlib.Path, str]) -> ProbSevereProduct:
        """
        Create a ProbSevereProduct object from a ProbSevere GeoJSON file.

        Args:
            geojson_path (Union[pathlib.Path, str]): Path to ProbSevere GeoJSON file

        Raises:
            FileNotFoundError: If the JSON file is not found.

        Returns:
            ProbSevereProduct: ProdSevereProduct for this JSON file.
        """
        # Validate GeoJSON path
        geojson_path = pathlib.Path(geojson_path)
        if not geojson_path.exists():
            raise FileNotFoundError(
                'Could not find ProbSevere GeoJSON path: %s' %
                str(geojson_path))

        # Open dataset with GDAL, keeping native data (since this is an extended GeoJSON format)
        ds = gdal.OpenEx(str(geojson_path), open_options=['NATIVE_DATA=YES'])

        # Create the object!
        return cls(ogr_ds=ds)
