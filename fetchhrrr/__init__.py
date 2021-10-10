#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import pathlib
from datetime import datetime

import pytz

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
FETCHHRRR_CONFIG_LOC = pathlib.Path(pathlib.Path.home(), '.fetchhrrr')

# Module state variables
_cur_download_dir = None


def get_download_dir():
    """ Get the module-level download directory for HRRR data """
    global _cur_download_dir

    # If we already set the download dir, return it
    if _cur_download_dir is not None:
        return _cur_download_dir

    # If we have a config file with the download directory, load it and return
    attempt_unlink = False
    if FETCHHRRR_CONFIG_LOC.exists():
        try:
            with open(FETCHHRRR_CONFIG_LOC) as f:
                config = json.load(f)
            _cur_download_dir = config.get('download_dir')
            if _cur_download_dir is not None:
                return _cur_download_dir
            else:
                attempt_unlink = True
        except Exception as e:
            print('Got exception when attempting to load save file: %s' %
                  repr(e))
            attempt_unlink = True

    # If we didn't read the config file correctly, attempt an unlink to
    # refresh the state
    if attempt_unlink:
        print('Attempting to unlink existing config file.')
        try:
            FETCHHRRR_CONFIG_LOC.unlink()
        except Exception:
            print('Unlink failed! Continuing anyway.')

    # Otherwise, or if the previous step failed, query the user for a directory!
    got_valid_dir = False
    while not got_valid_dir:
        response = input('Please enter path to download directory: ')
        response_path = pathlib.Path(response).expanduser().resolve()
        if response_path.exists():
            if response_path.is_dir():
                got_valid_dir = True
            else:
                print('Entered path is not a directory! %s' %
                      str(response_path))
        else:
            print('Entered path does not exist! %s' % str(response_path))

    # We entered a valid path!
    _cur_download_dir = response_path

    # Ask the user if we'd like to save this config for later
    response = ''
    while response.lower() not in ('y', 'n'):
        response = input(
            'Save this to a config file for later? (%s) (Respond y/Y/n/N): ' %
            str(FETCHHRRR_CONFIG_LOC))
    if response.lower() == 'y':
        with open(FETCHHRRR_CONFIG_LOC, 'w') as f:
            json.dump(dict(download_dir=str(_cur_download_dir.resolve())),
                      f,
                      indent=2)
        FETCHHRRR_CONFIG_LOC.chmod(0o600)
        print('Download directory successfully saved!')

    # Finally return the download directory that we entered
    return _cur_download_dir


from .hrrr_product import HRRRProduct