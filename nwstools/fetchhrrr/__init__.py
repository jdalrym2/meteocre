#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pathlib
from datetime import datetime

import pytz

from .. import get_logger as _get_logger
from .. import get_download_dir as _get_download_dir

# Module constants
CUR_DIR = pathlib.Path(__file__).parent.resolve()
HRRR_V1_INIT_TIME = datetime(2014, 9, 30, 14, 0, 0).replace(tzinfo=pytz.UTC)
HRRR_V2_INIT_TIME = datetime(2016, 8, 23, 12, 0, 0).replace(tzinfo=pytz.UTC)
HRRR_V3_INIT_TIME = datetime(2018, 7, 12, 12, 0, 0).replace(tzinfo=pytz.UTC)
HRRR_V4_INIT_TIME = datetime(2020, 12, 2, 12, 0, 0).replace(tzinfo=pytz.UTC)
PRODUCT_ID_MAP = {
    'prs': '3D Pressure Levels',
    'nat': 'Native Levels',
    'sfc': '2D Surface Levels',
    'subh': '2D Surface Levels - Sub Hourly'
}
HRRR_VERSION_JSON_MAP = {
    1: pathlib.Path(CUR_DIR, 'inventory_json',
                    'hrrr_v1_inventory.json').resolve(),
    2: pathlib.Path(CUR_DIR, 'inventory_json',
                    'hrrr_v2_inventory.json').resolve(),
    3: pathlib.Path(CUR_DIR, 'inventory_json',
                    'hrrr_v3_inventory.json').resolve(),
    4: pathlib.Path(CUR_DIR, 'inventory_json',
                    'hrrr_v4_inventory.json').resolve()
}


def get_logger():
    return _get_logger()


def get_download_dir():
    d = pathlib.Path(_get_download_dir(), 'fetchhrrr')
    d.mkdir(parents=False, exist_ok=True)
    return d


from .hrrr_product import HRRRProduct
