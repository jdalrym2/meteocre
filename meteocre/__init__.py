#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import logging
import pathlib
from typing import Optional
import numpy as np
from osgeo import gdal

meteocre_CONFIG_LOC = pathlib.Path(pathlib.Path.home(), '.meteocre')

# Module state variables
_cur_download_dir = None

# Configure logger
_logger = logging.getLogger(__name__)
_logger.setLevel(
    logging.DEBUG)  # configure log level here. TODO: add to ~/.meteocre
_logger_handlers = [logging.StreamHandler(sys.stdout)]
_logger_formatter = logging.Formatter(
    r'%(asctime)-15s %(levelname)s [%(module)s] %(message)s')
_logger.handlers.clear()
for h in _logger_handlers:
    h.setFormatter(_logger_formatter)
    _logger.addHandler(h)


def get_logger():
    """ Fetch the meteocre logger """
    return _logger


# Map of GDAL datatypes to numpy datatypes
GDAL_TO_NUMPY_MAP = {
    gdal.GDT_Byte: np.uint8,
    gdal.GDT_UInt16: np.uint16,
    gdal.GDT_UInt32: np.uint32,
    gdal.GDT_Int16: np.int16,
    gdal.GDT_Int32: np.int32,
    gdal.GDT_Float32: np.float32,
    gdal.GDT_Float64: np.float64,
    gdal.GDT_CInt16: np.complex128,
    gdal.GDT_CInt32: np.complex128,
    gdal.GDT_CFloat32: np.complex128,
    gdal.GDT_CFloat64: np.complex128,
    gdal.GDT_Unknown: np.float64,
}
NUMPY_TO_GDAL_MAP = dict([(v, k) for k, v in GDAL_TO_NUMPY_MAP.items()])


# Get download directory for meteocre files
def get_download_dir():
    """ Get the module-level download directory for HRRR data """
    global _cur_download_dir

    # If we already set the download dir, return it
    if _cur_download_dir is not None:
        assert _cur_download_dir.exists()
        return _cur_download_dir

    # If we have a config file with the download directory, load it and return
    attempt_unlink = False
    if meteocre_CONFIG_LOC.exists():
        try:
            with open(meteocre_CONFIG_LOC) as f:
                config = json.load(f)
            _cur_download_dir = config.get('download_dir')
            if _cur_download_dir is not None:
                _cur_download_dir = pathlib.Path(_cur_download_dir)
                if _cur_download_dir.exists():
                    return _cur_download_dir
                else:
                    _logger.error(
                        'Configured download directory no longer exists!')
            else:
                attempt_unlink = True
        except Exception as e:
            _logger.error('Got exception when attempting to load save file!')
            _logger.exception(e)
            attempt_unlink = True

    # If we didn't read the config file correctly, attempt an unlink to
    # refresh the state
    if attempt_unlink:
        _logger.info('Attempting to unlink existing config file.')
        try:
            meteocre_CONFIG_LOC.unlink()
        except Exception as e:
            _logger.error(
                'Unlink failed (exception below)! Continuing anyway.')
            _logger.exception(e)

    # Otherwise, or if the previous step failed, query the user for a directory!
    got_valid_dir = False
    response_path = None  # type: Optional[pathlib.Path]
    while not got_valid_dir:
        response = input('Please enter path to download directory: ')
        response_path = pathlib.Path(response).expanduser().resolve()
        if response_path.exists():
            if response_path.is_dir():
                got_valid_dir = True
            else:
                _logger.error('Entered path is not a directory! %s' %
                              str(response_path))
        else:
            _logger.error('Entered path does not exist! %s' %
                          str(response_path))

    # We entered a valid path!
    if not isinstance(response_path, pathlib.Path):
        raise RuntimeError('Response path is None!')
    _cur_download_dir = response_path

    # Ask the user if we'd like to save this config for later
    response = ''
    while response.lower() not in ('y', 'n'):
        response = input(
            'Save this to a config file for later? (%s) (Respond y/Y/n/N): ' %
            str(meteocre_CONFIG_LOC))
    if response.lower() == 'y':
        with open(meteocre_CONFIG_LOC, 'w') as f:
            json.dump(dict(download_dir=str(_cur_download_dir.resolve())),
                      f,
                      indent=2)
        meteocre_CONFIG_LOC.chmod(0o600)
        _logger.info('Download directory successfully saved!')

    # Finally return the download directory that we entered
    return _cur_download_dir
