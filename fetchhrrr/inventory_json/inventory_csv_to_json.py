#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import pathlib

if __name__ == '__main__':

    # Path to inventory CSV files
    inventory_csv_path = pathlib.Path('./fetchhrrr/inventory_csv').resolve()
    assert inventory_csv_path.exists()

    # Path to output HRRR inventory JSON files
    hrrr_v1_json_path = pathlib.Path(
        './fetchhrrr/inventory_json/hrrr_v1_inventory.json')
    hrrr_v2_json_path = pathlib.Path(
        './fetchhrrr/inventory_json/hrrr_v2_inventory.json')
    hrrr_v3_json_path = pathlib.Path(
        './fetchhrrr/inventory_json/hrrr_v3_inventory.json')
    hrrr_v4_json_path = pathlib.Path(
        './fetchhrrr/inventory_json/hrrr_v4_inventory.json')

    # Allocate dicts for HRRR versions
    hrrr_v1_dict = {}
    hrrr_v2_dict = {}
    hrrr_v3_dict = {}
    hrrr_v4_dict = {}

    # Create a mapping to quickly lookup
    # correct output dict with version num
    hrrr_version_map = {
        1: hrrr_v1_dict,
        2: hrrr_v2_dict,
        3: hrrr_v3_dict,
        4: hrrr_v4_dict,
    }

    # Loop through all CSV files in the directory
    for csv_path in inventory_csv_path.glob('*.csv'):
        # Parse filename
        split = csv_path.stem.split('_')
        hrrr_version = int(split[0][-1])
        product_id = split[1]
        start_hour = int(split[2])
        end_hour = int(split[3])

        # Add metadata to inventory file
        this_version_dict = hrrr_version_map[hrrr_version]
        if not product_id in this_version_dict:
            this_version_dict[product_id] = {}
        hour_str = ','.join([str(e) for e in range(start_hour, end_hour + 1)])
        this_version_dict[product_id][hour_str] = {}
        out_dict = this_version_dict[product_id][hour_str]

        # Parse file
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                # Add each row to output dict
                idx, level, param, valid_time, desc = row
                out_dict[int(idx)] = dict(idx=int(idx),
                                          level=level,
                                          param=param,
                                          valid_time=valid_time,
                                          desc=desc)

    # Finally, save output dicts
    with open(hrrr_v1_json_path, 'w') as f:
        json.dump(hrrr_v1_dict, f, indent=2)
    with open(hrrr_v2_json_path, 'w') as f:
        json.dump(hrrr_v2_dict, f, indent=2)
    with open(hrrr_v3_json_path, 'w') as f:
        json.dump(hrrr_v3_dict, f, indent=2)
    with open(hrrr_v4_json_path, 'w') as f:
        json.dump(hrrr_v4_dict, f, indent=2)