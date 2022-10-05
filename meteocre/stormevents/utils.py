#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gzip
import shutil
import pathlib
from typing import Union, Optional
from io import BytesIO
from ftplib import FTP
from datetime import datetime, timedelta

import pytz


def to_datetime(yearmonth_str: str,
                day_str: str,
                time_str: str = "",
                tz_str: Optional[str] = None) -> datetime:
    """
    Convert CSV fields to datetime object

    Args:
        yearmonth_str (str): Year/month string from CSV file
        day_str (str): Day string from CSV file
        time_str (str, optional): Time string from CSV file (if applicable). Defaults to "".
        tz_str (Optional[str], optional): Timezone string if applicable. If None, assume UTC. Defaults to None.

    Returns:
        datetime: Timezone-aware datetime object from the CSV fields
    """
    year = int(yearmonth_str[:4])
    month = int(yearmonth_str[-2:])
    day = int(day_str)
    if len(time_str) == 4:
        hour, minute = int(time_str[:2]), int(time_str[-2:])
    elif len(time_str) == 3:
        hour, minute = int(time_str[:1]), int(time_str[-2:])
    else:
        hour, minute = 0, 0

    if tz_str is not None:
        tz_offset = int(tz_str[-2:])
    else:
        tz_offset = 0

    return (datetime(year, month, day, hour, minute) -
            timedelta(hours=tz_offset)).replace(tzinfo=pytz.UTC)


def ftp_download_and_extract_gzip(
        ftp: FTP, ftp_name: str, output_path: Union[str,
                                                    pathlib.Path]) -> None:
    """
    Download and extract gzip'd file at an FTP location

    Args:
        ftp (FTP): FTP object
        ftp_name (str): Filename to retrieve
        output_path (Union[str, pathlib.Path]): Output path
    """
    fio = BytesIO()
    ftp.retrbinary('RETR %s' % ftp_name, fio.write)
    fio.seek(0)
    with open(output_path, 'wb') as fout, gzip.GzipFile(fileobj=fio) as gz:
        shutil.copyfileobj(gz, fout)
