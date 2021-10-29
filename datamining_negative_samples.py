#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pickle
from datetime import datetime, timedelta

import pytz
import numpy as np

if __name__ == '__main__':

    # Open postiive centroids
    with open('./data/positive_clusters_main.pkl', 'rb') as f:
        pos = pickle.load(f)

    # Dates we care about
    region_season_map = {
        'Great Plains':
        (datetime(2000, 4, 1,
                  tzinfo=pytz.UTC), datetime(2000, 6, 1, tzinfo=pytz.UTC)),
        'Dixie Alley': (datetime(2000, 3, 1, tzinfo=pytz.UTC),
                        datetime(2000, 5, 1, tzinfo=pytz.UTC)),
        'Midwest': (datetime(2000, 2, 15, tzinfo=pytz.UTC),
                    datetime(2000, 4, 15, tzinfo=pytz.UTC)),
    }

    all_samples = {}
    for region_name, region_dict in pos.items():
        all_samples[region_name] = {}
        season_start, season_end = [
            e.replace(tzinfo=None) for e in region_season_map[region_name]
        ]
        season_len = (season_end - season_start).days
        all_dts = [e.replace(tzinfo=None) for e in region_dict.keys()]

        # Loop through all dates
        for dt, centroids in region_dict.items():
            all_samples[region_name][dt] = []

            # Loop through all centroids for the date
            for centroid in centroids:

                # Add positive sample
                all_samples[region_name][dt].append((centroid, 'pos'))

                # Find a datetime that is not associated with a strong
                # tornado yet
                new_dt = None
                while new_dt is None or new_dt in all_dts:
                    t = np.random.randint(0, season_len)
                    y = np.random.randint(2015, 2020 + 1)
                    new_dt = season_start.replace(year=y) + timedelta(days=t)

                # Add negative sample
                if new_dt not in all_samples[region_name]:
                    all_samples[region_name][new_dt] = []
                all_samples[region_name][new_dt].append((centroid, 'neg'))

    # Save all samples
    with open('./data/all_samples.pkl', 'wb') as f:
        pickle.dump(all_samples, f)