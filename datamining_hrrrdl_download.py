#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pickle
import pathlib
import logging
from datetime import timedelta

import pytz

import nwstools
from nwstools import fetchhrrr

if __name__ == '__main__':

    logger = nwstools.get_logger()

    # Add file handler to nwstools logger
    log_location = pathlib.Path('./hrrr_download.log').resolve()
    if log_location.exists():
        log_location.unlink()
    h = logging.FileHandler(str(log_location))
    _logger_formatter = logging.Formatter(
        r'%(asctime)-15s %(levelname)s [%(module)s] %(message)s')
    h.setLevel(logging.DEBUG)
    h.setFormatter(_logger_formatter)
    logger.addHandler(h)

    # Load all samples
    with open('./data/all_samples.pkl', 'rb') as f:
        all_samples = pickle.load(f)

    # Loop through all samples and download
    for region_name, region_dict in all_samples.items():

        logger.info('Processing region: %s' % region_name)

        for dt in region_dict.keys():

            logger.info('Processing date: %s' % dt.isoformat())

            morning_run = dt.replace(hour=12, tzinfo=pytz.UTC)
            midday_run = morning_run + timedelta(hours=6)
            evening_run = morning_run + timedelta(hours=12)

            # Fetch products
            try:
                morning_product = fetchhrrr.HRRRProduct.from_archive(
                    morning_run, 0, 'sfc')
            except Exception as e:
                logger.error('Exception raised! Skipping.')
                logger.exception(e)
                morning_product = None

            try:
                midday_product = fetchhrrr.HRRRProduct.from_archive(
                    midday_run, 0, 'sfc')
            except Exception as e:
                logger.error('Exception raised! Skipping.')
                logger.exception(e)
                morning_product = None

            try:
                evening_product = fetchhrrr.HRRRProduct.from_archive(
                    evening_run, 0, 'sfc')
            except Exception as e:
                logger.error('Exception raised! Skipping.')
                logger.exception(e)
                morning_product = None

            for product in (morning_product, midday_product, evening_product):
                if product is None:
                    continue
                try:
                    product.fetch()
                except Exception as e:
                    logger.error('Exception raised! Skipping.')
                    logger.exception(e)

    logger.info('Done!')