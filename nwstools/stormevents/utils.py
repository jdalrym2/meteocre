#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gzip
import typing
import shutil
from io import BytesIO
from ftplib import FTP
from datetime import datetime, timedelta

import pytz


def to_datetime(yearmonth_str: str,
                day_str: str,
                time_str: int = "",
                tz_str: typing.Union[None, str] = None) -> datetime:
    """ Convert CSV fields to datetime object """
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


def ftp_download_and_extract_gzip(ftp: FTP, ftp_name: str,
                                  output_path: typing.BinaryIO) -> None:
    """ Download and extract gzip'd file at an FTP location """
    fio = BytesIO()
    ftp.retrbinary('RETR %s' % ftp_name, fio.write)
    fio.seek(0)
    with open(output_path, 'wb') as fout, gzip.GzipFile(fileobj=fio) as gz:
        shutil.copyfileobj(gz, fout)
