#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import json
import pickle
import pathlib
import logging
from datetime import timedelta
from typing import OrderedDict

import numpy as np
import pytz

import nwstools
from nwstools import fetchhrrr


def get_param_idxs(param_dict, product):
    param_idxs = {}
    inventory = product.inventory
    for param_name, param_tuple in param_dict.items():
        param_level, _, param_id = param_tuple
        matches = inventory.get_product_by_param(param_id,
                                                 levels=[param_level])
        if len(matches) > 1:
            print('Found multiple matches! Taking first.')
        elif not len(matches):
            raise RuntimeError('No matches found for %s', param_name)
        param_idxs[param_name] = matches[0]['idx']
    return param_idxs


def get_desired_fields(product, param_dict, lat, lon, r_km) -> dict:

    fields = {}

    # Get product idxs we want
    param_idxs = get_param_idxs(param_dict, product)

    # Simple parameters, the ones we just query the point at
    simple_params = [
        'Surface Gust',
        '500mb Height',
        '500mb Temperature',
        '500mb Dew Point',
        '700mb Height',
        '700mb Temperature',
        '700mb Dew Point',
        '850mb Height',
        '850mb Temperature',
        '850mb Dew Point',
        '925mb Temperature',
        '925mb Dew Point',
        'Surface Pressure',
        'Surface Height',
        'Surface Temperature',
        '2-meter Dew Point',
        'Lifted Index',
        'Surface CAPE',
        'Surface CIN',
        'Precipitable Water',
        'Low Cloud Cover',
        'Near-Surface CAPE',
        'Near-Surface CIN',
        '500mb Wind U',
        '500mb Wind V',
        '700mb Wind U',
        '700mb Wind V',
        '850mb Wind U',
        '850mb Wind V',
        '925mb Wind U',
        '925mb Wind V',
        '10-meter Wind U',
        '10-meter Wind V',
        '0-1000 m Shear U',
        '0-1000 m Shear V',
        '0-6000 m Shear U',
        '0-6000 m Shear V',
    ]
    for param in simple_params:
        param_idx = param_idxs[param]
        fields[param] = product.query_for_pts([param_idx], [(lat, lon)])[0][0]

    # Radius querys
    gust_r = product.query_for_radius([param_idxs['Surface Gust']], lat, lon,
                                      r_km)
    fields['Max Gust in Radius'] = np.max(gust_r)

    tmp_r = product.query_for_radius([param_idxs['Surface Temperature']], lat,
                                     lon, r_km)
    fields['Surface Temp 25/75 Differential in Radius'] = np.percentile(
        tmp_r, 75) - np.percentile(tmp_r, 25)

    fields['Surface Temp 10/90 Differential in Radius'] = np.percentile(
        tmp_r, 90) - np.percentile(tmp_r, 10)

    dpt_r = product.query_for_radius([param_idxs['2-meter Dew Point']], lat,
                                     lon, r_km)
    fields['Surface Dew Point 25/75 Differential in Radius'] = np.percentile(
        dpt_r, 75) - np.percentile(dpt_r, 25)

    fields['Surface Dew Point 10/90 Differential in Radius'] = np.percentile(
        dpt_r, 90) - np.percentile(dpt_r, 10)

    return fields


if __name__ == '__main__':

    logger = nwstools.get_logger()

    with open('./data/datamining_params.json', 'r') as f:
        params_dict = json.load(f)

    # Add file handler to nwstools logger
    log_location = pathlib.Path('./hrrr_fields.log').resolve()
    if log_location.exists():
        log_location.unlink()
    h = logging.FileHandler(str(log_location))
    _logger_formatter = logging.Formatter(
        r'%(asctime)-15s %(levelname)s [%(module)s] %(message)s')
    h.setLevel(logging.DEBUG)
    h.setFormatter(_logger_formatter)
    logger.addHandler(h)

    # Load all samples
    with open('./data/all_samples_holdout.pkl', 'rb') as f:
        all_samples = pickle.load(f)

    fieldnames = [
        'region',
        'date',
        'hour',
        'sample_type',
        'lat',
        'lon',
        'Surface Gust',
        '500mb Height',
        '500mb Temperature',
        '500mb Dew Point',
        '700mb Height',
        '700mb Temperature',
        '700mb Dew Point',
        '850mb Height',
        '850mb Temperature',
        '850mb Dew Point',
        '925mb Temperature',
        '925mb Dew Point',
        'Surface Pressure',
        'Surface Height',
        'Surface Temperature',
        '2-meter Dew Point',
        'Lifted Index',
        'Surface CAPE',
        'Surface CIN',
        'Precipitable Water',
        'Low Cloud Cover',
        'Near-Surface CAPE',
        'Near-Surface CIN',
        '500mb Wind U',
        '500mb Wind V',
        '700mb Wind U',
        '700mb Wind V',
        '850mb Wind U',
        '850mb Wind V',
        '925mb Wind U',
        '925mb Wind V',
        '10-meter Wind U',
        '10-meter Wind V',
        '0-1000 m Shear U',
        '0-1000 m Shear V',
        '0-6000 m Shear U',
        '0-6000 m Shear V',
        'Max Gust in Radius',
        'Surface Temp 25/75 Differential in Radius',
        'Surface Temp 10/90 Differential in Radius',
        'Surface Dew Point 25/75 Differential in Radius',
        'Surface Dew Point 10/90 Differential in Radius',
    ]

    # Loop through all samples and download
    for region_name, region_dict in all_samples.items():

        logger.info('Processing region: %s' % region_name)

        # Write to CSV
        with open(
                './data/dataset_holdout_%s.csv' %
                region_name.lower().replace(' ', '_'), 'w') as f:

            writer = csv.DictWriter(f, fieldnames)
            writer.writeheader()

            for dt, cluster_list in region_dict.items():

                logger.info('Processing date: %s' % dt.isoformat())

                morning_run = dt.replace(hour=12, tzinfo=pytz.UTC)
                midday_run = morning_run + timedelta(hours=6)
                evening_run = morning_run + timedelta(hours=12)

                # Fetch products
                try:
                    morning_product = fetchhrrr.HRRRProduct.from_archive(
                        morning_run, 0, 'sfc')
                except Exception:
                    morning_product = None

                try:
                    midday_product = fetchhrrr.HRRRProduct.from_archive(
                        midday_run, 0, 'sfc')
                except Exception:
                    midday_product = None

                try:
                    evening_product = fetchhrrr.HRRRProduct.from_archive(
                        evening_run, 0, 'sfc')
                except Exception:
                    evening_product = None

                for product in (morning_product, midday_product,
                                evening_product):
                    if product is None:
                        continue

                    date_str = dt.strftime('%Y-%m-%d')
                    hour_str = product.forecast_time.strftime('%H')

                    logger.info('Processing product: (%s, %s)' %
                                (date_str, hour_str))

                    for (lat, lon), sample_type in cluster_list:

                        logger.info('Processing cluster... (%s, %s, %s)' %
                                    (lat, lon, sample_type))

                        try:
                            fields = get_desired_fields(product,
                                                        params_dict,
                                                        lat,
                                                        lon,
                                                        r_km=120)

                            row = OrderedDict(fields)

                            row.update({'lon': lon})
                            row.move_to_end('lon', last=False)

                            row.update({'lat': lat})
                            row.move_to_end('lat', last=False)

                            row.update({'sample_type': sample_type})
                            row.move_to_end('sample_type', last=False)

                            row.update({'hour': hour_str})
                            row.move_to_end('hour', last=False)

                            row.update({'date': date_str})
                            row.move_to_end('date', last=False)

                            row.update({'region': region_name})
                            row.move_to_end('region', last=False)

                            writer.writerow(row)
                        except Exception as e:
                            logger.error('Exception caught! Skipping')
                            logger.exception(e)

    logger.info('Done!')