#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gzip
import shutil
import pathlib
from io import BytesIO
from ftplib import FTP
from typing import Optional, Union, Sequence

from . import get_logger, get_download_dir

from . import StormEventDetailedReport, StormEventFatalityReport, StormEventLocation


def _get_filename_for_product_type(year: int, product_type: str) -> str:
    """
    Return filename we will give for a specific set of records

    Args:
        year (int): Year (ex. 2022)
        product_type (str): Product type to generate name for

    Returns:
        str: _description_
    """
    return 'stormevents_%s_%d.csv' % (product_type, year)


def _ftp_download_and_extract_gzip(
        ftp: FTP, ftp_name: str, output_path: Union[str,
                                                    pathlib.Path]) -> None:
    """
    Simultaneously download and unzip a Gzip archive from an FTP target

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


def fetch_from_storm_events_archive(
        query_year: int,
        products_to_load: Union[str, Sequence[str]] = 'all',
        load: bool = True) -> Optional[dict[str, list]]:
    """
    Fetch a set of products for a given year from the NCEI archive,
        or load them up if they've already been fetched

    Args:
        query_year (int): Year to query
        products_to_load (Union[str, Sequence[str]], optional): Products to fetch. Defaults to 'all'.
        load (bool, optional): Whether or not to load into memory once fetched. Defaults to True.

    Raises:
        ValueError: If the product type is invalid.
        ValueError: If no matches are found for event details.
        ValueError: If no matches are found for event fatalities.
        ValueError: If no matches are found for event locations.

    Returns:
        Optional[dict[str, list]]: If load is True, loaded products. Else None.
    """

    # Get logger
    logger = get_logger()

    # Parse products input
    valid_products = ('details', 'fatalities', 'locations')
    if isinstance(products_to_load, str):
        products_to_load = [products_to_load]
    if 'all' in products_to_load:
        products_to_load = valid_products
    else:
        for e in products_to_load:
            if e not in valid_products:
                raise ValueError('Invalid product type! Must be in %s' %
                                 str(valid_products))

    # Get download directory
    download_dir = get_download_dir()

    # Get file paths for the products we will download
    product_paths = []
    for e in products_to_load:
        this_path = pathlib.Path(download_dir,
                                 _get_filename_for_product_type(query_year, e))
        product_paths.append(this_path)

    # Narrow down products to fetch if any of these are already downloaded
    products_to_fetch = []
    for product, product_path in zip(products_to_load, product_paths):
        if product_path.exists():
            logger.info(
                'Product already downloaded for query year: %d, product: %s' %
                (query_year, product))
        else:
            products_to_fetch.append(product)

    # FTP to NCEI storm events archive
    with FTP('ftp.ncei.noaa.gov') as ftp:
        ftp.login()
        ftp.cwd('/pub/data/swdi/stormevents/csvfiles/')
        file_list = ftp.nlst()

        # Get 'details' products
        if 'details' in products_to_fetch:
            details_match = [
                e for e in file_list
                if ('d%d' % query_year in e and 'details' in e)
            ]
            if not len(details_match):
                raise ValueError('Found no matches for event details!')
            if len(details_match) > 1:
                logger.warning(
                    'Multiple matches found for details! Taking first.')
            details_match = details_match[0]

            logger.info('Downloading and unzipping details file...')
            details_csv_path = pathlib.Path(
                download_dir,
                _get_filename_for_product_type(query_year, 'details'))
            _ftp_download_and_extract_gzip(ftp, details_match,
                                           details_csv_path)

        if 'fatalities' in products_to_fetch:
            fatalities_match = [
                e for e in file_list
                if ('d%d' % query_year in e and 'fatalities' in e)
            ]
            if not len(fatalities_match):
                raise ValueError('Found no matches for event fatalities!')
            if len(fatalities_match) > 1:
                logger.warning(
                    'Multiple matches found for fatalities! Taking first.')
            fatalities_match = fatalities_match[0]

            logger.info('Downloading and unzipping fatalities file...')
            fatalities_csv_path = pathlib.Path(
                download_dir,
                _get_filename_for_product_type(query_year, 'fatalities'))
            _ftp_download_and_extract_gzip(ftp, fatalities_match,
                                           fatalities_csv_path)

        if 'locations' in products_to_fetch:
            locations_match = [
                e for e in file_list
                if ('d%d' % query_year in e and 'locations' in e)
            ]
            if not len(locations_match):
                raise ValueError('Found no matches for event locations!')
            if len(locations_match) > 1:
                logger.warning(
                    'Multiple matches found for locations! Taking first.')
            locations_match = locations_match[0]

            logger.info('Downloading and unzipping locations file...')
            locations_csv_path = pathlib.Path(
                download_dir,
                _get_filename_for_product_type(query_year, 'locations'))
            _ftp_download_and_extract_gzip(ftp, locations_match,
                                           locations_csv_path)

    # Load requested products
    if load:
        loaded_products = {}
        for product, product_path in zip(products_to_load, product_paths):
            logger.info('Loading %s products for query year %d...' %
                        (product, query_year))
            if product == 'details':
                obj_lst = StormEventDetailedReport.from_csv(product_path)
            elif product == 'fatalities':
                obj_lst = StormEventFatalityReport.from_csv(product_path)
            elif product == 'locations':
                obj_lst = StormEventLocation.from_csv(product_path)
            else:
                logger.warning('Seeing unknown product: %s' % product)
                obj_lst = []
            loaded_products[product] = obj_lst

        # Return loaded products
        return loaded_products
