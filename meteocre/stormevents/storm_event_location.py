#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import pathlib
from typing import Union, List
from dataclasses import dataclass


@dataclass
class StormEventLocation:
    """ Class to store a storm event location entry the NOAA NCEI Storm Events Database """
    episode_id: int
    event_id: int
    location_idx: int
    range: float
    azimuth: str
    location: str
    lat: float
    lon: float

    @classmethod
    def from_csv(
            cls, csv_file: Union[str,
                                 pathlib.Path]) -> List[StormEventLocation]:
        """
        Load a set of location entries from a CSV file

        Args:
            csv_file (Union[str, pathlib.Path]): CSV file to load in

        Returns:
            List[StormEventLocation]: List of storm event locations from the CSV file
        """
        cls_list = []
        with open(csv_file, 'r') as f:
            dict_reader = csv.DictReader(f)
            for row in dict_reader:
                this_cls = cls(episode_id=int(row['EPISODE_ID']),
                               event_id=int(row['EVENT_ID']),
                               location_idx=int(row['LOCATION_INDEX']),
                               range=float(row['RANGE']),
                               azimuth=row['AZIMUTH'],
                               location=row['LOCATION'],
                               lat=float(row['LATITUDE']),
                               lon=float(row['LONGITUDE']))
                cls_list.append(this_cls)

        return cls_list
