#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pickle
from datetime import datetime

import pytz

from nwstools.stormevents import fetch_from_storm_events_archive

if __name__ == '__main__':

    # Query all reports from 2015 to 2020, 2021 is holdout set
    all_reports = []
    for query_year in range(2015, 2021 + 1):
        all_reports.extend(
            fetch_from_storm_events_archive(query_year, 'details')['details'])

    # Filter reports based on whether or not it's an EF-2+ tornado
    ef2_plus_reports = []
    for report in all_reports:
        if report.is_tornado_event and report.tornado['f-scale'] in (
                'EF2', 'EF3', 'EF4', 'EF5'):
            ef2_plus_reports.append(report)
    del all_reports

    # Regions we care about
    region_geo_map = {
        'Great Plains': [31, -102, 43, -94.5],
        'Dixie Alley': [29, -94.5, 36.5, -82],
        'Midwest': [36.5, -94.5, 43, -82]
    }

    # Dates we care about
    region_season_map = {
        'Great Plains':
        (datetime(2000, 4, 1,
                  tzinfo=pytz.UTC), datetime(2000, 6, 1, tzinfo=pytz.UTC)),
        'Dixie Alley': (datetime(2000, 3, 1, tzinfo=pytz.UTC),
                        datetime(2000, 5, 1, tzinfo=pytz.UTC)),
        'Midwest': (datetime(2000, 2, 15, tzinfo=pytz.UTC),
                    datetime(2000, 4, 15, tzinfo=pytz.UTC)),
    }

    # Find our positive samples
    pos_sample_map = {}
    holdout_pos_sample_map = {}
    for (region, (lat_min, lon_min, lat_max,
                  lon_max)), (_,
                              (season_start,
                               season_end)) in zip(region_geo_map.items(),
                                                   region_season_map.items()):

        print('Processing region: %s...' % region)
        pos_sample_map[region] = {}
        holdout_pos_sample_map[region] = {}

        for report in ef2_plus_reports:
            # Get report details: location and time
            lat, lon = report.begin_location['lat'], report.begin_location[
                'lon']
            report_start_time = report.start_time.astimezone(
                pytz.timezone('America/Chicago'))
            start_time = report_start_time.replace(year=2000)
            start_time_2 = report_start_time.replace(hour=0,
                                                     minute=0,
                                                     second=0,
                                                     microsecond=0)
            report_year = report.start_time.year

            # Determine if it is in our region and season, if so, save the date only
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max and season_start <= start_time <= season_end:
                if report_year <= 2020:
                    if start_time_2 not in pos_sample_map[region]:
                        pos_sample_map[region][start_time_2] = []
                    pos_sample_map[region][start_time_2].append((lat, lon))
                else:
                    if start_time_2 not in holdout_pos_sample_map[region]:
                        holdout_pos_sample_map[region][start_time_2] = []
                    holdout_pos_sample_map[region][start_time_2].append(
                        (lat, lon))

    print([len(v) for v in pos_sample_map.values()])
    print([len(v) for v in holdout_pos_sample_map.values()])

    # Save pickle'd output
    print('Pickling output...')
    with open('./data/positive_reports.pkl', 'wb') as f:
        pickle.dump(pos_sample_map, f)
    with open('./data/positive_reports_holdout.pkl', 'wb') as f:
        pickle.dump(holdout_pos_sample_map, f)
