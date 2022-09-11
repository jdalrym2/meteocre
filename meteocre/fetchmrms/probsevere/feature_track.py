#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Class to describe a single ProbSevere feature over a time series """

from __future__ import annotations
from datetime import datetime
from typing import List, Tuple
from functools import cache

from osgeo import ogr

from .feature import ProbSevereFeature


class ProbSevereFeatureTrack:
    """ Class to describe a single ProbSevere feature over a time series """

    __slots__ = ['feat_id', '_feature_list']

    def __init__(self,
                 feat_id: int,
                 feature_list: List[ProbSevereFeature],
                 validate: bool = True):
        self.feat_id = feat_id
        if validate:
            for f in feature_list:
                if not f.__class__ == ProbSevereFeature:
                    raise ValueError(
                        'Each item in feature list must be of class ProbSevereFeature! Got %s'
                        % f.__class__.__name__)
                if not f.feat_id == feat_id:
                    raise ValueError(
                        'Feature ID mismatch in list! Got %d. Expected %d.' %
                        (f.feat_id, feat_id))
        self._feature_list = feature_list

    def __str__(self):
        return '<%s; ID: %d; Features: %d; Valid Times: %s -> %s>' % (
            self.__class__.__name__, self.feat_id, len(self._feature_list),
            min(self.valid_times).isoformat(), max(
                self.valid_times).isoformat())

    def __repr__(self):
        return self.__str__()

    def __len__(self) -> int:
        return self._feature_list.__len__()

    def __getitem__(self, key: int) -> ProbSevereFeature:
        return self._feature_list.__getitem__(key)

    def __add__(self,
                other: ProbSevereFeatureTrack,
                validate: bool = True) -> ProbSevereFeatureTrack:
        if other.__class__ != ProbSevereFeatureTrack:
            raise ValueError('Cannot to add to object of class %s!' %
                             other.__class__.__name__)
        if validate and other.feat_id != self.feat_id:
            raise ValueError('Feature ID mismatch between classes!')
        return self.__class__(self.feat_id,
                              self._feature_list + other._feature_list)

    @property
    @cache
    def valid_times(self) -> List[datetime]:
        """
        Valid times for this track

        Returns:
            List[datetime]: Valid times for this track
        """
        return [e.valid_time for e in self._feature_list]

    @property
    @cache
    def centroids(self) -> List[Tuple[float, float]]:
        """
        Centroids for this track

        Returns:
            List[Tuple[float, float]]: Centroids for this track
        """
        return [e.centroid for e in self._feature_list]

    @property
    @cache
    def speed_list(self) -> List[float]:
        """
        List of speeds for this track

        Returns:
            List[float]: List of speeds for this track
        """
        return [e.speed for e in self._feature_list]

    @property
    @cache
    def bearing_list(self) -> List[float]:
        """
        List of bearings (degrees) for this track

        Returns:
            List[float]: List of bearings (degrees) for this track
        """
        return [e.bearing for e in self._feature_list]

    @property
    @cache
    def area_list(self) -> List[float]:
        """
        List of areas [km^2] for this track

        Returns:
            List[float]: List of areas [km^2] for this track
        """
        return [e.area for e in self._feature_list]

    @property
    @cache
    def probsevere_trend(self) -> List[int]:
        """
        Trend of probability of severe weather [%] values for this track

        Returns:
            List[int]: Trend of probability of severe weather [%] values for this track
        """
        return [e.probsevere for e in self._feature_list]

    @property
    @cache
    def probtor_trend(self) -> List[int]:
        """
        Trend of probability of a tornado [%] values for this track

        Returns:
            List[int]: Trend of probability of a tornado [%] values for this track
        """
        return [e.probtor for e in self._feature_list]

    @property
    @cache
    def probhail_trend(self) -> List[int]:
        """
        Trend of probability of severe hail [%] values for this track

        Returns:
            List[int]: Trend of probability of severe hail [%] values for this track
        """
        return [e.probhail for e in self._feature_list]

    @property
    @cache
    def probwind_trend(self) -> List[int]:
        """
        Trend of probability of severe wind [%] values for this track

        Returns:
            List[int]: Trend of probability of severe wind [%] values for this track
        """
        return [e.probwind for e in self._feature_list]

    @property
    @cache
    def property_trend(self, key: str) -> List[float]:
        """
        Fetch the trend for a miscellaneous property.

        Args:
            key (str): Property key

        Returns:
            List[float]: Property trend
        """
        return [float(e.get_property(key)) for e in self._feature_list]

    @property
    @cache
    def linestring(self) -> ogr.Geometry:
        """
        OGR LineString Geometry for this track

        Returns:
            ogr.Geometry: OGR LineString Geometry for this track
        """
        line = ogr.Geometry(ogr.wkbLineString)
        for pt_x, pt_y in self.centroids:
            line.AddPoint_2D(pt_x, pt_y)
        return line

    @property
    def wkt_str(self) -> str:
        """
        LineString WKT string for this track

        Returns:
            str: LineString WKT string for this track
        """
        return self.linestring.ExportToWkt()