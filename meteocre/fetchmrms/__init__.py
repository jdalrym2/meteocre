#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pathlib

from .. import get_logger as _get_logger
from .. import get_download_dir as _get_download_dir


def get_logger():
    return _get_logger()


def get_download_dir():
    d = pathlib.Path(_get_download_dir(), 'mrms')
    d.mkdir(parents=False, exist_ok=True)
    return d


from .mrms_product import MRMSProduct, MRMSRotationProduct, MRMSReflectivityProduct, MRMSSevereHailIndexProduct, MRMSMaximumExpectedSizeOfHailProduct
from . import probsevere