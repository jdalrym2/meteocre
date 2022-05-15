#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Class for handling a collection of ProbSevereProduct objects """

from __future__ import annotations

import pathlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from osgeo import ogr

from .product import ProbSevereProduct
from .feature import ProbSevereFeature
from .feature_track import ProbSevereFeatureTrack


class ProbSevereProductCollection:
    """ Class for handling a collection of ProbSevereProduct objects """

    __slots__ = ['_product_list']

    def __init__(self,
                 product_list: List[ProbSevereProduct],
                 validate: bool = True):
        """
        Create a ProbSevereProductCollection from a list of ProbSevereProduct objects.
        Product list will be sorted by valid time upon import.

        Args:
            product_list (List[ProbSevereProduct]): List of ProbSevereProduct objects
            validate (bool, optional): Whether or not to sanity check the list. Defaults to True.

        Raises:
            ValueError: If, while sanity checking, an item that is not of class ProbSeverePRoduct is found
        """
        # Sanity check product_list
        if validate:
            for p in product_list:
                if not p.__class__ == ProbSevereProduct:
                    raise ValueError(
                        'Product list must be a list of ProbSevereProduct objects! Found: %s'
                        % repr(p))

        # Sort by valid time (increasing)
        product_list = sorted(product_list, key=lambda p: p.valid_time)

        # Persist product list, it is assumed it remain sorted by valid time
        self._product_list = product_list

    def __str__(self):
        v = self.valid_times()
        return '<%s; Products: %d; Valid Times: %s -> %s>' % (
            self.__class__.__name__, len(
                self._product_list), min(v).isoformat(), max(v).isoformat())

    def __repr__(self):
        return self.__str__()

    def __len__(self) -> int:
        return self._product_list.__len__()

    def __getitem__(self, key: int) -> ProbSevereProduct:
        return self._product_list.__getitem__(key)

    def __add__(
            self,
            other: ProbSevereProductCollection) -> ProbSevereProductCollection:
        if other.__class__ != ProbSevereProductCollection:
            raise ValueError('Cannot to add to object of class %s!' %
                             other.__class__.__name__)
        return self.__class__(self._product_list + other._product_list,
                              validate=False)

    def valid_times(self) -> List[datetime]:
        """
        Get list of valid times for the products in this collection.

        Returns:
            List[datetime]: List of valid times
        """
        return [p.valid_time for p in self._product_list]

    def set_spatial_filter(self, f: Optional[ogr.Geometry]) -> None:
        """
        Set the active geospatial filter all products in this collection

        Args:
            f (Optional[ogr.Geometry]): OGR Polygon Geometry for the filter. None for no filter.
        """
        for p in self._product_list:
            p.set_spatial_filter(f)

    def set_bbox_filter(self, lat_min: float, lon_min: float, lat_max: float,
                        lon_max: float) -> None:
        """
        Set a bounding box geospatial filter for all products in this collection

        Args:
            lat_min (float): Minimum latitude (WGS84 decimal degrees)
            lon_min (float): Minimum longitude (WGS84 decimal degrees)
            lat_max (float): Maximum latitude (WGS84 decimal degrees)
            lon_max (float): Maximum longitude (WGS84 decimal degrees)
        """
        # Create OGR Geometry from bounds (doing this once so each subproduct
        # doesn't duplicate the work)
        ogr_ring = ogr.Geometry(ogr.wkbLinearRing)
        ogr_ring.AddPoint_2D(lon_min, lat_max)
        ogr_ring.AddPoint_2D(lon_max, lat_max)
        ogr_ring.AddPoint_2D(lon_max, lat_min)
        ogr_ring.AddPoint_2D(lon_min, lat_min)
        ogr_ring.AddPoint_2D(lon_min, lat_max)
        ogr_poly = ogr.Geometry(ogr.wkbPolygon)
        ogr_poly.AddGeometry(ogr_ring)

        # Set spatial filter
        for p in self._product_list:
            p.set_spatial_filter(ogr_poly)

    def reset_spatial_filter(self) -> None:
        """
        Clear the active geospatial filter for all products in this collection.
        """
        for p in self._product_list:
            p.set_spatial_filter(None)

    def compute_feature_tracks(
        self,
        temporal_filter: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[int, ProbSevereFeatureTrack]:
        """ """
        # Sanity check temporal filter
        if temporal_filter is not None:
            assert temporal_filter[0].__class__ == datetime
            assert temporal_filter[1].__class__ == datetime
            assert temporal_filter[0] < temporal_filter[1]
            if temporal_filter[0].tzinfo is None or temporal_filter[
                    1].tzinfo is None:
                raise ValueError(
                    'Temporal filter times must be timezone-aware!')

        # Loop through all sub-products, and aggregate a dictionary
        # mapping feature IDs to features
        feature_id_dict: Dict[int, List[ProbSevereFeature]] = {}
        for p in self._product_list:
            # Skip if outside temporal filter
            if temporal_filter is not None:
                if p.valid_time < temporal_filter[0]:
                    continue
                if p.valid_time > temporal_filter[1]:
                    continue

            # Otherwise, loop through features
            for f in p.features:
                if f.feat_id not in feature_id_dict:
                    feature_id_dict[f.feat_id] = []
                feature_id_dict[f.feat_id].append(f)

        # Compute a set of tracks from these lists
        track_dict: Dict[int, ProbSevereFeatureTrack] = {}
        for feat_id, feat_list in feature_id_dict.items():
            track_dict[feat_id] = ProbSevereFeatureTrack(feat_id,
                                                         feat_list,
                                                         validate=False)

        return track_dict

    @classmethod
    def from_directory(
            cls, path: Union[pathlib.Path,
                             str]) -> ProbSevereProductCollection:
        """
        Import a set of ProbSevere products from a directory.
        The products in the resulting collection will be sorted by valid time.

        Args:
            path (Union[pathlib.Path, str]): Path to directory of ProbSevere JSON files.

        Raises:
            ValueError: If the path does not exist.
            ValueError: If the path is not a directory.

        Returns:
            ProbSevereProductCollection: Collection of ProbSevereProducts
        """
        # Sanity check path
        path = pathlib.Path(path)
        if not path.exists():
            raise ValueError('Path does not exist!')
        if not path.is_dir():
            raise ValueError('Path is not a directory!')

        # Get a list of ProbSevereProduct objects by globbing through the directory
        product_list = [
            ProbSevereProduct.from_geojson(p) for p in path.glob('*.json')
        ]

        # Create object, will sort upon init
        return cls(product_list, validate=False)