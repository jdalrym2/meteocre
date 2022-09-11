#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Class to describe a ProbSevere feature (i.e. storm) and it's corresponding attributes """

from __future__ import annotations
from datetime import datetime
import json
import math
from typing import List, Tuple, Dict, Union
from typing import Optional     #noqa
from functools import cache

from osgeo import ogr, osr

# Feature descriptions, including units
FEATURE_DESC: Dict[str, str] = {
    "ID":
    "the object ID number of this storm object. This will help link together storm objects through time.",
    "MUCAPE":
    "the most-unstable CAPE for this storm, in units of J/kg",
    "MLCAPE":
    "the mixed-layer CAPE (0-90mb) for this storm, in units of J/kg",
    "MLCIN":
    "the mixed-layer convective inhibition for this storm, in units of J/kg",
    "EBSHEAR":
    "the effective bulk shear for this storm, in units of kts",
    "SRH01KM":
    "the 0-1km storm relative helicity for this storm, in units of J/kg",
    "MEANWIND_1-3kmAGL":
    "the 0-1km AGL mean wind for this storm, in units of kts",
    "MESH":
    "the MRMS maximum expected size of hail for this storm, in units of in",
    "VIL_DENSITY":
    "the MRMS vertically integrated liquid density for this storm, in units of g/m3",
    "FLASH_RATE":
    "the ENI flash rate for this storm, in units of flashes/min",
    "FLASH_DENSITY":
    "the ENI flash density for this storm, in units of flashes/min/km2",
    "MAXLLAZ":
    "the MRMS maximum 0-2km AGL azimuthal shear for this storm, in units of s-1",
    "P98LLAZ":
    "the MRMS 98th percentile value of 0-2km AGL azimuthal shear for this storm, in units of s-1",
    "P98MLAZ":
    "the MRMS 98th percentile value of 3-6km AGL azimuthal shear for this storm, in units of s-1",
    "MAXRC_EMISS":
    "the maximum rate of change in 11 µm top-oftroposphere emissivity (aka normalized satellite growth rate) for this storm, in units of %/min",
    "MAXRC_ICECF":
    "the maximum rate of change in the ice cloud fraction (aka glaciation rate) for this storm, in units of min-1",
    "WETBULB_0C_HGT":
    "the height of the lowest wet-bulb 0oC level for this storm, in units of kft",
    "PWAT":
    "the precipitable water for this storm, in units of in",
    "CAPE_M10M30":
    "the CAPE between -10oC and -30oC levels for this storm, in units of J/kg",
    "LJA":
    "the ENI lightning jump algorithm sigma value for this storm, in units of standard deviation",
    "SIZE":
    "the number of pixels for this storm; each pixel is roughly equivalent to 1 km2.",
    "AVG_BEAM_HGT":
    "the average radar beam height for this storm from the nearest NEXRAD site, assuming standard atmospheric refraction",
    "MOTION_EAST":
    "the eastward or westerly motion for this storm, in units of m/s (values < 0 mean westward/easterly motion)",
    "MOTION_SOUTH":
    "the southward or norther motion for this storm, in units of m/s (values < 0 mean northward/southerly motion). ",
}


class ProbSevereFeature:
    """ Class to describe a ProbSevere feature (i.e. storm) and it's corresponding attributes """
    __slots__ = [
        '_feat_id', '_ogr_poly', '_valid_time', '_probsevere', '_probtor',
        '_probhail', '_probwind', '_probsevere_msg', '_probtor_msg',
        '_probhail_msg', '_probwind_msg', '_properties'
    ]

    def __init__(self, feat_id: int, ogr_poly: ogr.Geometry,
                 valid_time: datetime, **kwargs):
        """
        Initialize a ProbSevere Feature object. The user is unlikely to call
        this, and should use a `from_*` method instead.

        Args:
            feat_id (int): Unique identifier for the feature. Used to track over time.
            ogr_poly (ogr.Geometry): OGR Geometry (Polygon) for the feature
            valid_time (datetime): Valid time for this feature.

        Keyword Args:
            probsevere (int): Probability of severe weather within 60 minutes [%]
            probtor (int): Probability of tornado within 60 minutes [%]
            probhail (int): Probability of severe hail within 60 minutes [%]
            probwind (int): Probability of severe wind within 60 minutes [%]
            probsevere_msg (str): Probability of severe weather message (intended for display)
            probtor_msg (str): Probability of tornado message (intended for display)
            probhail_msg (str): Probability of severe hail message (intended for display)
            probwind_msg (str): Probability of severe wind message (intended for display)
            properties (Dict[str, str]): GeoJSON properties for the feature

        Raises:
            ValueError: _description_
        """ """ """
        # Feature ID
        self._feat_id = feat_id

        # Feature OGR Geometry (polygon)
        if not ogr_poly.GetGeometryType() == ogr.wkbPolygon:
            raise ValueError('Feature geometry must be a polygon! Got: %s' %
                             ogr_poly.GetGeometryName())
        self._ogr_poly = ogr_poly

        # Probabilities
        self._probsevere = kwargs.get('probsevere', -1)     # type: int
        self._probtor = kwargs.get('probtor', -1)     # type: int
        self._probhail = kwargs.get('probhail', -1)     # type: int
        self._probwind = kwargs.get('probwind', -1)     # type: int

        # Model output messages
        self._probsevere_msg = kwargs.get('probsevere_msg', '')     # type: str
        self._probtor_msg = kwargs.get('probtor_msg', '')     # type: str
        self._probhail_msg = kwargs.get('probhail_msg', '')     # type: str
        self._probwind_msg = kwargs.get('probwind_msg', '')     # type: str

        # Properties
        self._properties = kwargs.get('properties',
                                      {})     # type: Dict[str, str]

        # Valid time
        self._valid_time = valid_time

    def __str__(self) -> str:
        return '<%s; ID: %d; ProbSevere: %d%%; ProbTor: %d%%; ProbHail: %d%%; ProbWind: %d%%>' % (
            self.__class__.__name__, self.feat_id, self.probsevere,
            self.probtor, self.probhail, self.probwind)

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def feat_id(self) -> int:
        """
        Return a unique identifier for the feature.
        This ID is consistent for the same storm over time.

        Returns:
            int: Unique identifier for the feature
        """
        return self._feat_id

    @property
    def ogr_poly(self) -> ogr.Geometry:
        """
        Return an OGR Geometry (Polygon) for this feature.

        Returns:
            ogr.Geometry: OGR Polygon geometry for the feature
        """
        return self._ogr_poly

    @property
    @cache
    def ogr_poly_eq_area(self) -> ogr.Geometry:
        """
        OGR Equal Area (EPSG:6933) Polygon Geometry for the feature.
        Used for calculation of area and perimeter. Not computed until
        called.

        Returns:
            ogr.Geometry: OGR Equal Area Polygon Geometry object
        """
        # Create coordinate transformation object from source SRS -> EPSG:6933
        src_srs = self.ogr_poly.GetSpatialReference()
        dst_srs = osr.SpatialReference()
        dst_srs.ImportFromEPSG(
            6933)     # cyclindrical equal-area projection (units: m)
        xform = osr.CoordinateTransformation(src_srs, dst_srs)

        # Compute equal-area polygon from current polygon.
        ogr_poly_eq_area = self._ogr_poly.Clone()
        ogr_poly_eq_area.Transform(xform)

        return ogr_poly_eq_area

    @property
    def wkt_str(self) -> str:
        """
        WGS84 Polygon WKT sting for this feature

        Returns:
            str: WGS84 Polygon WKT sting for this feature
        """
        return self._ogr_poly.ExportToWkt()

    @property
    def valid_time(self) -> datetime:
        """
        Feature valid time

        Returns:
            datetime: Feature valid time
        """
        return self._valid_time

    @property
    def centroid(self) -> Tuple[float, float]:
        """
        Feature centroid

        Returns:
            Tuple[float, float]: Feature centroid in WGS84 decimal degrees: (lon, lat)
        """
        c = self.ogr_poly.Centroid()     # type: ogr.Geometry
        return c.GetX(), c.GetY()

    @property
    def velocity(self) -> Tuple[float, float]:
        """
        Feature southward and eastward velocity. Units of m/s.

        Returns:
            Tuple[float, float]: (Southward velocity in m/s, Eastword velocity in m/s)
        """
        return self.get_property('MOTION_SOUTH'), self.get_property(
            'MOTION_EAST')     # type: ignore

    @property
    def speed(self) -> float:
        """
        Speed of the feature (velocity magnitude) in m/s

        Returns:
            float: Feature speed in m/s
        """
        v_south, v_east = self.velocity
        return (v_south**2 + v_east**2)**0.5

    @property
    def bearing(self) -> float:
        """
        Feature bearing (velocity angle) in degrees.
        0 -> N, 90 -> E, 180 -> S, 270 -> W

        Returns:
            float: Feature bearing in degrees.
        """
        v_south, v_east = self.velocity
        return math.degrees(math.atan2(v_south, v_east)) + 90.0

    @property
    def area(self) -> float:
        """
        Feature area in km^2

        Returns:
            float: Feature area in km^2
        """
        return self.ogr_poly_eq_area.GetArea() * 1e-6

    @property
    def perimeter(self) -> float:
        """
        Feature perimeter in km

        Returns:
            float: Feature perimeter in km
        """
        return self.ogr_poly_eq_area.Boundary().Length() * 1e-3

    @property
    def probsevere(self) -> int:
        """
        Probability of severe weather [%] within 60 minutes

        Returns:
            int: Probability of severe weather [%]
        """
        return self._probsevere

    @property
    def probtor(self) -> int:
        """
        Probability of a tornado [%] within 60 minutes

        Returns:
            int: Probability of a tornado [%]
        """
        return self._probtor

    @property
    def probhail(self) -> int:
        """
        Probability of severe hail [%] within 60 minutes

        Returns:
            int: Probability of severe hail [%]
        """
        return self._probhail

    @property
    def probwind(self) -> int:
        """
        Probability of severe wind [%] within 60 minutes

        Returns:
            int: Probability of severe wind [%]
        """
        return self._probwind

    @property
    def properties(self) -> Dict[str, str]:
        """
        Other feature properties (thermodynamic / kinematic environment, lightning flash density, etc)

        Returns:
            Dict[str, str]: Other feature properties (copied)
        """
        return self._properties.copy()

    def get_property(self, key: str) -> Union[float, str]:
        """
        Retrieve the value of a property.

        Args:
            key (str): Property key

        Returns:
            Union[float, str]: Property value (float if castable, else str)
        """
        v = self._properties[key]
        # Try to cast to float if possible
        try:
            return float(v)
        except ValueError:
            return v

    def get_description(self, key: str) -> str:
        """
        Get the description for a property, including units.

        Args:
            key (str): Property key

        Returns:
            str: Property description, including units.
        """
        return FEATURE_DESC[key]

    def get_message(
            self,
            filter: List[str] = ['severe', 'tor', 'hail', 'wind']) -> str:
        """
        Get a printable message for a set of hazard types.

        Args:
            filter (List[str], optional): Which hazard messages to display. Defaults to ['severe', 'tor', 'hail', 'wind'].

        Raises:
            ValueError: If an unknown hazard string is provided. Expecting any of 'severe', 'tor', 'hail', or 'wind'.

        Returns:
            str: Printable message for the provided set of hazard types.
        """
        msg_list = []     # type: List[str]
        for f in filter:
            if f.lower() == 'severe':
                msg_list.append(self._probsevere_msg)
            elif f.lower() == 'tor':
                msg_list.append(self._probtor_msg)
            elif f.lower() == 'hail':
                msg_list.append(self._probhail_msg)
            elif f.lower() == 'wind':
                msg_list.append(self._probwind_msg)
            else:
                raise ValueError('Unknown filter: %s' % repr(f))
        return '\n\n'.join(msg_list)

    @classmethod
    def from_ogr_feature(cls, valid_time: datetime,
                         feat: ogr.Feature) -> ProbSevereFeature:
        """
        Create an object from an OGR Feature object (i.e. from opening a ProbSevere GeoJSON file.)

        Args:
            valid_time (datetime): Valid time for the OGR feature
            feat (ogr.Feature): OGR Feature object describing this feature.

        Returns:
            ProbSevereFeature: ProbSevere feature object
        """
        # Get feature polygon
        ogr_poly = feat.GetGeometryRef().Clone()

        # Get native data
        native_data = json.loads(str(feat.GetNativeData()))

        # Process probsevere
        probsevere_data = native_data['models']['probsevere']
        probsevere = int(probsevere_data['PROB'])
        probsevere_msg = '\n'.join([
            probsevere_data[e] for e in probsevere_data.keys()
            if e.startswith('LINE')
        ])

        # Process probtor
        probtor_data = native_data['models']['probtor']
        probtor = int(probtor_data['PROB'])
        probtor_msg = '\n'.join([
            probtor_data[e] for e in probtor_data.keys()
            if e.startswith('LINE')
        ])

        # Process probhail
        probhail_data = native_data['models']['probhail']
        probhail = int(probhail_data['PROB'])
        probhail_msg = '\n'.join([
            probhail_data[e] for e in probhail_data.keys()
            if e.startswith('LINE')
        ])

        # Process probwind
        probwind_data = native_data['models']['probwind']
        probwind = int(probwind_data['PROB'])
        probwind_msg = '\n'.join([
            probwind_data[e] for e in probwind_data.keys()
            if e.startswith('LINE')
        ])

        # Get properties
        properties = native_data['properties']

        # Get feature ID
        feat_id = int(properties['ID'])

        # Put it all together!
        return cls(feat_id=feat_id,
                   ogr_poly=ogr_poly,
                   valid_time=valid_time,
                   probsevere=probsevere,
                   probtor=probtor,
                   probhail=probhail,
                   probwind=probwind,
                   probsevere_msg=probsevere_msg,
                   probtor_msg=probtor_msg,
                   probhail_msg=probhail_msg,
                   probwind_msg=probwind_msg,
                   properties=properties)
