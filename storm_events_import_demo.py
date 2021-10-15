#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from stormevents import StormEventDetailedReport

A = [
    e for e in StormEventDetailedReport.from_csv(
        'StormEvents_details-ftp_v1.csv') if e.is_tornado_event
]

pass
