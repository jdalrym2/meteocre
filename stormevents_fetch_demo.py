#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gzip
import shutil
import pathlib
import typing
import warnings
from io import BytesIO
from ftplib import FTP


def ftp_download_and_extract_gzip(ftp: FTP, ftp_name: str,
                                  output_path: typing.BinaryIO) -> None:
    fio = BytesIO()
    ftp.retrbinary('RETR %s' % ftp_name, fio.write)
    fio.seek(0)
    with open(output_path, 'wb') as fout, gzip.GzipFile(fileobj=fio) as gz:
        shutil.copyfileobj(gz, fout)


if __name__ == '__main__':

    query_year = 2019
    download_dir = pathlib.Path('.').resolve()

    with FTP('ftp.ncei.noaa.gov') as ftp:
        ftp.login()
        ftp.cwd('/pub/data/swdi/stormevents/csvfiles/')
        file_list = ftp.nlst()

        details_match = [
            e for e in file_list
            if ('d%d' % query_year in e and 'details' in e)
        ]
        if not len(details_match):
            raise ValueError('Found no matches for event details!')
        if len(details_match) > 1:
            warnings.warn('Multiple matches found for details! Taking first.')
        details_match = details_match[0]

        fatalities_match = [
            e for e in file_list
            if ('d%d' % query_year in e and 'fatalities' in e)
        ]
        if not len(fatalities_match):
            raise ValueError('Found no matches for event fatalities!')
        if len(fatalities_match) > 1:
            warnings.warn(
                'Multiple matches found for fatalities! Taking first.')
        fatalities_match = fatalities_match[0]

        locations_match = [
            e for e in file_list
            if ('d%d' % query_year in e and 'locations' in e)
        ]
        if not len(locations_match):
            raise ValueError('Found no matches for event locations!')
        if len(locations_match) > 1:
            warnings.warn(
                'Multiple matches found for locations! Taking first.')
        locations_match = locations_match[0]

        print('Downloading and unzipping details file...')
        details_csv_path = pathlib.Path(download_dir,
                                        '%s.csv' % details_match.split('.')[0])
        ftp_download_and_extract_gzip(ftp, details_match, details_csv_path)

        print('Downloading and unzipping fatalities file...')
        fatalities_csv_path = pathlib.Path(
            download_dir, '%s.csv' % fatalities_match.split('.')[0])
        ftp_download_and_extract_gzip(ftp, fatalities_match,
                                      fatalities_csv_path)

        print('Downloading and unzipping locations file...')
        locations_csv_path = pathlib.Path(
            download_dir, '%s.csv' % locations_match.split('.')[0])
        ftp_download_and_extract_gzip(ftp, locations_match, locations_csv_path)