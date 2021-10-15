#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import typing
from datetime import datetime, timedelta
from dataclasses import dataclass

import pytz


def to_datetime(yearmonth_str: str,
                day_str: str,
                time_str: str,
                tz_str: typing.Union[None, str] = None):
    """ Convert CSV fields to datetime object """
    year = int(yearmonth_str[:4])
    month = int(yearmonth_str[-2:])
    day = int(day_str)
    if len(time_str) == 4:
        hour, minute = int(time_str[:2]), int(time_str[-2:])
    elif len(time_str) == 3:
        hour, minute = int(time_str[:1]), int(time_str[-2:])
    else:
        hour, minute = 0, 0

    tz_offset = int(tz_str[-2:])
    return (datetime(year, month, day, hour, minute) -
            timedelta(hours=tz_offset)).replace(tzinfo=pytz.UTC)


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
    magnitude: typing.Union[None, dict]
    flood_cause: str
    tornado: typing.Union[None, dict]
    begin_location: dict
    end_location: dict
    episode_narrative: str
    event_narrative: str

    @classmethod
    def from_csv(cls, csv_file: typing.TextIO):
        """ Load a set of detailed reports from a CSV file """
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
                        row['TOR_F_SCALE'],
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
                        'lON':
                        float(row['BEGIN_LON'])
                    } if len(row['BEGIN_RANGE']) else None,
                    end_location={
                        'str':
                        '%d %s %s' % (int(row['END_RANGE']),
                                      row['END_AZIMUTH'], row['END_LOCATION']),
                        'lat':
                        float(row['END_LAT']),
                        'lON':
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
    def duration(self):
        return self.end_time - self.start_time

    @property
    def is_tornado_event(self):
        return self.tornado is not None
