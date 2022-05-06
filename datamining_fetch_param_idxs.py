#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from datetime import datetime
from nwstools.fetchhrrr import HRRRProduct

if __name__ == '__main__':

    # Load a product that we have
    product = HRRRProduct.from_archive(datetime(2020, 5, 18, 12), 0, 'sfc')

    # Params we care about
    params = {
        'Surface Gust': ('0-SFC', 'surface', 'GUST'),
        '500mb Height': ('50000-ISBL', '500 mb', 'HGT'),
        '500mb Temperature': ('50000-ISBL', '500 mb', 'TMP'),
        '500mb Dew Point': ('50000-ISBL', '500 mb', 'DPT'),
        '500mb Wind U': ('50000-ISBL', '500 mb', 'UGRD'),
        '500mb Wind V': ('50000-ISBL', '500 mb', 'VGRD'),
        '700mb Height': ('70000-ISBL', '700 mb', 'HGT'),
        '700mb Temperature': ('70000-ISBL', '700 mb', 'TMP'),
        '700mb Dew Point': ('70000-ISBL', '700 mb', 'DPT'),
        '700mb Wind U': ('70000-ISBL', '700 mb', 'UGRD'),
        '700mb Wind V': ('70000-ISBL', '700 mb', 'VGRD'),
        '850mb Height': ('85000-ISBL', '850 mb', 'HGT'),
        '850mb Temperature': ('85000-ISBL', '850 mb', 'TMP'),
        '850mb Dew Point': ('85000-ISBL', '850 mb', 'DPT'),
        '850mb Wind U': ('85000-ISBL', '850 mb', 'UGRD'),
        '850mb Wind V': ('85000-ISBL', '850 mb', 'VGRD'),
        '925mb Temperature': ('92500-ISBL', '925 mb', 'TMP'),
        '925mb Dew Point': ('92500-ISBL', '925 mb', 'DPT'),
        '925mb Wind U': ('92500-ISBL', '925 mb', 'UGRD'),
        '925mb Wind V': ('92500-ISBL', '925 mb', 'VGRD'),
        'Surface Pressure': ('0-SFC', 'surface', 'PRES'),
        'Surface Height': ('0-SFC', 'surface', 'HGT'),
        'Surface Temperature': ('0-SFC', 'surface', 'TMP'),
        '2-meter Dew Point': ('2-HTGL', '2 m above ground', 'DPT'),
        '10-meter Wind U': ('10-HTGL', '10 m above ground', 'UGRD'),
        '10-meter Wind V': ('10-HTGL', '10 m above ground', 'VGRD'),
        'Lifted Index': ('50000-100000-ISBL', '500-1000 mb', 'LFTX'),
        'Surface CAPE': ('0-SFC', 'surface', 'CAPE'),
        'Surface CIN': ('0-SFC', 'surface', 'CIN'),
        'Precipitable Water':
        ('0-EATM', 'entire atmosphere (considered as a single layer)', 'PWAT'),
        'Low Cloud Cover': ('0-LCY', 'low cloud layer', 'LCDC'),
        '0-1000 m Shear U': ('0-1000-HTGL', '0-1000 m above ground', 'VUCSH'),
        '0-1000 m Shear V': ('0-1000-HTGL', '0-1000 m above ground', 'VVCSH'),
        '0-6000 m Shear U': ('0-6000-HTGL', '0-6000 m above ground', 'VUCSH'),
        '0-6000 m Shear V': ('0-6000-HTGL', '0-6000 m above ground', 'VVCSH'),
        'Near-Surface CAPE': ('9000-0-SPDL', '90-0 mb above ground', 'CAPE'),
        'Near-Surface CIN': ('9000-0-SPDL', '90-0 mb above ground', 'CIN'),
    }

    param_idxs = {}

    inventory = product.inventory

    for param_name, param_tuple in params.items():
        param_level, param_level_desc, param_id = param_tuple
        matches = inventory.get_product_by_param(param_id,
                                                 levels=[param_level])

        param_idxs[param_name] = matches[0]['idx']