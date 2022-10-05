#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import pathlib
from typing import Union, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from .utils import to_datetime


@dataclass
class StormEventDetailedReport:
    """ Class to store a detailed event report from the NOAA NCEI Storm Events Database """
    event_id: int
    episode_id: int
    start_time: datetime
    end_time: datetime
    state: str
    state_fips: int
    event_type: str
    cz: dict
    wfo: str
    injuries: dict
    deaths: dict
    damage: dict
    source: str
    magnitude: Union[None, dict]
    flood_cause: str
    tornado: Union[None, dict]
    begin_location: Optional[dict]
    end_location: Optional[dict]
    episode_narrative: str
    event_narrative: str

    @classmethod
    def from_csv(
            cls,
            csv_file: Union[str,
                            pathlib.Path]) -> List[StormEventDetailedReport]:
        """
        Load a set of detailed reports from a CSV file

        Args:
            csv_file (Union[str, pathlib.Path]): CSV file to read in

        Returns:
            List[StormEventDetailedReport]: Storm event report objects from the CSV file
        """
        cls_list = []
        with open(csv_file, 'r') as f:
            dict_reader = csv.DictReader(f)
            for row in dict_reader:
                this_cls = cls(
                    event_id=int(row['EVENT_ID']),
                    episode_id=int(row['EPISODE_ID']),
                    start_time=to_datetime(row['BEGIN_YEARMONTH'],
                                           row['BEGIN_DAY'], row['BEGIN_TIME'],
                                           row['CZ_TIMEZONE']),
                    end_time=to_datetime(row['END_YEARMONTH'], row['END_DAY'],
                                         row['END_TIME'], row['CZ_TIMEZONE']),
                    state=row['STATE'],
                    state_fips=int(row['STATE_FIPS']),
                    event_type=row['EVENT_TYPE'],
                    cz={
                        'type': row['CZ_TYPE'],
                        'fips': int(row['CZ_FIPS']),
                        'name': row['CZ_NAME'],
                    },
                    wfo=row['WFO'],
                    injuries={
                        'direct': int(row['INJURIES_DIRECT']),
                        'indirect': int(row['INJURIES_INDIRECT']),
                    },
                    deaths={
                        'direct': int(row['DEATHS_DIRECT']),
                        'indirect': int(row['DEATHS_INDIRECT']),
                    },
                    damage={
                        'property': row['DAMAGE_PROPERTY'],
                        'crops': row['DAMAGE_CROPS'],
                    },
                    source=row['SOURCE'],
                    magnitude={
                        'value': row['MAGNITUDE'],
                        'type': row['MAGNITUDE_TYPE']
                    } if len(row['MAGNITUDE']) else None,
                    flood_cause=row['FLOOD_CAUSE'],
                    tornado={
                        'f-scale':
                        row['TOR_F_SCALE'],
                        'length':
                        float(row['TOR_LENGTH'])
                        if len(row['TOR_LENGTH']) else None,
                        'width':
                        float(row['TOR_WIDTH'])
                        if len(row['TOR_WIDTH']) else None,
                        'other_wfo':
                        row['TOR_OTHER_WFO'],
                        'other_cz': {
                            'state': row['TOR_OTHER_CZ_STATE'],
                            'fips': row['TOR_OTHER_CZ_FIPS'],
                            'name': row['TOR_OTHER_CZ_NAME'],
                        } if row['TOR_OTHER_CZ_STATE'] else None
                    } if len(row['TOR_F_SCALE']) else None,
                    begin_location={
                        'str':
                        '%d %s %s' %
                        (int(row['BEGIN_RANGE']), row['BEGIN_AZIMUTH'],
                         row['BEGIN_LOCATION']),
                        'lat':
                        float(row['BEGIN_LAT']),
                        'lon':
                        float(row['BEGIN_LON'])
                    } if len(row['BEGIN_RANGE']) else None,
                    end_location={
                        'str':
                        '%d %s %s' % (int(row['END_RANGE']),
                                      row['END_AZIMUTH'], row['END_LOCATION']),
                        'lat':
                        float(row['END_LAT']),
                        'lon':
                        float(row['END_LON'])
                    } if len(row['END_RANGE']) else None,
                    episode_narrative=row['EPISODE_NARRATIVE'],
                    event_narrative=row['EVENT_NARRATIVE'])
                cls_list.append(this_cls)

        return cls_list

    def to_json_dict(self):
        """ Return a JSON dictionary for this report """
        raise NotImplementedError()

    @property
    def duration(self) -> timedelta:
        """
        Duration of the event

        Returns:
            timedelta: Duration as datetime.timedelta
        """
        return self.end_time - self.start_time

    @property
    def is_tornado_event(self) -> bool:
        """
        Whether or not this storm event is for a tornado

        Returns:
            bool: True if this event is related to a tornado
        """
        return self.tornado is not None
