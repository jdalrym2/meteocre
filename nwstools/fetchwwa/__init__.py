#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pathlib

from .. import get_logger as _get_logger
from .. import get_download_dir as _get_download_dir


def get_logger():
    return _get_logger()


def get_download_dir():
    d = pathlib.Path(_get_download_dir(), 'wwa')
    d.mkdir(parents=False, exist_ok=True)
    return d


from .wwa_polygon import WWAPolygon