#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
An object to describe an NWS Watch / Warning / Advisory (WWA) Polygon.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from osgeo import ogr
import pytz


@dataclass(frozen=True, kw_only=True, slots=True)
class WWAPolygon:
    """
    An object to describe an NWS Watch / Warning / Advisory (WWA) Polygon.

    Credit to IA State for attribute descriptions (comes from VTEC format):
    https://mesonet.agron.iastate.edu/info/datasets/vtec.html

    Attributes:
        wfo (str): This is the three character NWS Office/Center identifier.
            For CONUS locations, this is the 4 character ID dropping
            the first K. For non-CONUS sites, this is the identifier
            dropping the P.
        issued_time (datetime): This timestamp represents the start time of the event.
            When an event's lifecycle begins, this issued value can be updated as the NWS issues updates.
            The value presented represents the last known state of the event start time.
        expired_time (datetime): This timestamp represents the end time of the event.
            This value is updated as the event lifecycle happens with updates made by the NWS.
            The value presented represents the last known state of the event end time.
        init_issued_time (datetime): This is timestamp of the NWS Text Product that started the event.
            This timestamp is important for products like Winter Storm Watch,
            which have a begin time a number of days/hours into the future,
            but are typically considered to be in effect at the time of the text
            product issuace. This timestamp can also be used to form a canonical URL back
            to the IEM to fetch the raw NWS Text for this event. It is *not* updated during
            the event's lifecycle.
        init_expired_time (datetime): This is the expiration of the event denoted with the first
            issuance of the event. It is *not* updated during the event's lifecycle.
        phenom (str): This is the two character NWS identifier used to denote the VTEC event type.
            For example, TO for Tornado and SV for Severe Thunderstorm.
        significance:(str): This is the one character NWS identifier used to denote the VTEC significance.
        geotype (str): Either P for polygon or C for county/zone/parish.
        event_id (int): The VTEC event identifier. A tracking number that should be unique for this event,
            but sometimes it is not. Note that the uniqueness is not based on the combination of a UGC code,
            but the issuance center and a continuous spatial region for the event.
        status (str): The VTEC status code denoting the state the event is during its life cycle. This is
            purely based on any updates the event got and not some logic on the IEM's end denoting if
            the event is in the past or not.
        nws_ugc (str): For county,zone,parish warnings GTYPE=C, the Universal Geographic Code that the NWS uses.
        area (float): The IEM computed area of this event, this area computation is done in Albers (EPSG:2163).
        updated (datetime): The timestamp when this event's lifecycle was last updated by the NWS.
        hv_nwsli (str): For events that have H-VTEC (Hydro VTEC), this is the five character NWS Location Identifier.
        hv_sev (str): For events that have H-VTEC (Hydro VTEC), this is the one character flood severity at issuance.
        hv_cause (str): For events that have H-VTEC (Hydro VTEC), this is the two character cause of the flood.
        hv_rec (str): For events that have H-VTEC (Hydro VTEC), this is the code denoting if a record crest is
            expected at issuance.
        is_emergency (bool): Based on unofficial IEM logic, is this event an "Emergency" at any point during its life cycle.
        poly_begin_time (datetime): In the case of polygons (GTYPE=P) the UTC timestamp that the polygon is initially valid for.
        poly_end_time (datetime): In the case of polygons (GTYPE=P) the UTC timestamp that the polygon expires at.
        hail_tag (str): 	The IBW hail size tag (inches). This is only included with the (GTYPE=P) entries as there is a
            1 to 1 association between the tags and the polygons. If you do not include SVS updates, it is just the issuance tag.
        tornado_tag (str): 	The IBW wind gust tag (MPH).
        wind_tag (str): The IBW tornado tag.
        damage_tag (str): The IBW damage tag.
        ogr_poly (ogr.Geometry): OGR Polygon geometry for the hazard.
    """
    wfo: str
    issued_time: datetime
    expired_time: datetime
    init_issued_time: datetime
    init_expired_time: datetime
    phenom: str
    significance: str
    geotype: str
    event_id: int
    status: str
    nws_ugc: Optional[str] = None
    area: float
    updated: datetime
    hv_nwsli: Optional[str] = None
    hv_sev: Optional[str] = None
    hv_cause: Optional[str] = None
    hv_rec: Optional[str] = None
    is_emergency: bool
    poly_begin_time: Optional[datetime] = None
    poly_end_time: Optional[datetime] = None
    hail_tag: Optional[str] = None
    tornado_tag: Optional[str] = None
    wind_tag: Optional[str] = None
    damage_tag: Optional[str] = None
    ogr_poly: ogr.Geometry

    def __post_init__(self):
        if self.ogr_poly.GetGeometryType() != ogr.wkbPolygon:
            raise ValueError('OGR Geometry must be Polygon! Got: %s' %
                             self.ogr_poly.GetGeometryName())

    @property
    def wkt_str(self) -> str:
        """
        Returns the polygon WKT string

        Returns:
            str: Polygon WKT string
        """
        return self.ogr_poly.ExportToWkt()

    @staticmethod
    def _parse_dt_str(dt_str: str) -> datetime:
        """
        Parse datetime string from input GeoJSON into
        timezone-aware datetime.

        Args:
            dt_str (str): Input datetime string

        Returns:
            datetime: Output timezone-aware datetime
        """
        return datetime.strptime(dt_str,
                                 r'%Y%m%d%H%M').replace(tzinfo=pytz.UTC)

    @classmethod
    def from_ogr_feature(cls, feat: ogr.Feature) -> WWAPolygon:
        """
        Create a WWAPolygon from an OGR feature

        Args:
            feat (ogr.Feature): Input OGR feature

        Returns:
             WWAPolygon: Generated object
        """
        return cls.from_json(json.loads(
            feat.ExportToJson()))     # type: ignore

    @classmethod
    def from_json(cls, json_dict: Dict[str, Any]) -> WWAPolygon:
        """
        Create a WWAPolygon from a GeoJSON dict

        Args:
            json_dict (Dict[str, Any]): input GeoJSON dict

        Returns:
             WWAPolygon: Generated object
        """
        props: Dict[str, Any] = json_dict['properties']

        wfo = props['WFO']
        issued_time = cls._parse_dt_str(props['ISSUED'])
        expired_time = cls._parse_dt_str(props['EXPIRED'])
        init_issued_time = cls._parse_dt_str(props['INIT_ISS'])
        init_expired_time = cls._parse_dt_str(props['INIT_EXP'])
        phenom = props['PHENOM']
        significance = props['SIG']
        geotype = props['GTYPE']
        event_id = int(props['ETN'])
        status = props['STATUS']
        nws_ugc = props['NWS_UGC']
        area = float(props['AREA_KM2'])
        updated = cls._parse_dt_str(props['UPDATED'])
        hv_nwsli = props['HV_NWSLI']
        hv_sev = props['HV_SEV']
        hv_cause = props['HV_CAUSE']
        hv_rec = props['HV_REC']
        is_emergency = bool(props['EMERGENC'])
        poly_begin_time = cls._parse_dt_str(
            props['POLY_BEG']) if props['POLY_BEG'] is not None else None
        poly_end_time = cls._parse_dt_str(
            props['POLY_END']) if props['POLY_END'] is not None else None
        hail_tag = props['HAILTAG']
        tornado_tag = props['TORNTAG']
        wind_tag = props['WINDTAG']
        damage_tag = props['DAMAGTAG']
        ogr_poly = ogr.CreateGeometryFromJson(str(json_dict['geometry']))
        assert ogr_poly.GetGeometryType() == ogr.wkbPolygon

        return cls(wfo=wfo,
                   issued_time=issued_time,
                   expired_time=expired_time,
                   init_issued_time=init_issued_time,
                   init_expired_time=init_expired_time,
                   phenom=phenom,
                   significance=significance,
                   geotype=geotype,
                   event_id=event_id,
                   status=status,
                   nws_ugc=nws_ugc,
                   area=area,
                   updated=updated,
                   hv_nwsli=hv_nwsli,
                   hv_sev=hv_sev,
                   hv_cause=hv_cause,
                   hv_rec=hv_rec,
                   is_emergency=is_emergency,
                   poly_begin_time=poly_begin_time,
                   poly_end_time=poly_end_time,
                   hail_tag=hail_tag,
                   tornado_tag=tornado_tag,
                   wind_tag=wind_tag,
                   damage_tag=damage_tag,
                   ogr_poly=ogr_poly)
