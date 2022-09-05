#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from nwstools.stormevents import fetch_from_storm_events_archive

if __name__ == '__main__':

    for query_year in range(2015, 2021 + 1):
        print('Getting detailed products for query year %d...' % query_year)
        fetch_from_storm_events_archive(query_year, 'details', load=False)
