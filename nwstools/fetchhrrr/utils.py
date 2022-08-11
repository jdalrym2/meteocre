#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from datetime import datetime

import pytz

from . import HRRR_V1_INIT_TIME, HRRR_V2_INIT_TIME, HRRR_V3_INIT_TIME, HRRR_V4_INIT_TIME


def get_hrrr_version(run_time: datetime) -> int:
    """
    Get the HRRR version corresponding to the run time.

    Args:
        run_time (datetime): HRRR runtime. Assumes UTC if not
            timezone aware.

    Raises:
        ValueError: If HRRR product version could not be determined.

    Returns:
        int: HRRR product version. 1 -> 4
    """
    # Add UTC timezone if not specified
    if run_time.tzinfo is None:
        run_time = run_time.replace(tzinfo=pytz.UTC)

    if run_time > HRRR_V4_INIT_TIME:
        return 4
    elif run_time > HRRR_V3_INIT_TIME:
        return 3
    elif run_time > HRRR_V2_INIT_TIME:
        return 2
    elif run_time > HRRR_V1_INIT_TIME:
        return 1
    else:
        raise ValueError(
            'Invalid run time. Cannot determine HRRR product version.')


def validate_product_id(product_id: str) -> None:
    """
    Validate the product ID is a valid one for HRRR, otherwise raise an expection.

    Args:
        product_id (str): Product ID to validate.

    Raises:
        ValueError: If product ID is invalid.
    """
    if not re.match('(prs|nat|sfc|subh)', product_id):
        raise ValueError(
            'Invalid product ID: %s! Must be one of \'prs\', \'nat\', \'sfc\', \'subh\'.'
            % str(product_id))