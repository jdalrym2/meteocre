#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
from datetime import datetime, timedelta

import pytz

day_of_interest = '2021/04/27'

dt = datetime.strptime(day_of_interest, '%Y/%m/%d').replace(hour=18,
                                                            tzinfo=pytz.UTC)

for i in range(13):
    this_dt = dt + timedelta(hours=i)
    fetch_url = f"https://mrms.agron.iastate.edu/{this_dt.year}/{this_dt.month:02d}/{this_dt.day:02d}/{datetime.strftime(this_dt, '%Y%m%d%H')}.zip"

    print('Fetching %s...' % fetch_url)

    try:
        subprocess.run(['wget', '-L', fetch_url])
    except Exception as e:
        print('Exception occurred!')
        print(e)