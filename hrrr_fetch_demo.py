#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime

import pytz

from fetchhrrr import HRRRProduct

if __name__ == '__main__':

    run_time = datetime(2018, 5, 1, 18, 0, 0).replace(tzinfo=pytz.UTC)
    forecast_hour = 6
    product_id = 'sfc'

    product = HRRRProduct.from_archive(run_time, forecast_hour, product_id)
