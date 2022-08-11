#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Class to allow quick access of HRRR GRIB products """

from __future__ import annotations
from typing import List, Union

# Type hint HRRRProduct w/o circular dependency
# See: https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
# Thanks linting!
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import HRRRProduct

# Running mapping of level strings and their layman's descriptions
level_nice_desc = {
    '0-SFC': 'surface',
    '50000-ISBL': '500 mb',
    '70000-ISBL': '700 mb',
    '85000-ISBL': '850 mb',
    '92500-ISBL': '925 mb',
    '2-HTGL': '2 m above ground',
    '10-HTGL': '10 m above ground',
    '50000-100000-ISBL': '500-1000 mb',
    '0-EATM': 'entire atmosphere (considered as a single layer)',
    '0-LCY': 'low cloud layer',
    '0-1000-HTGL': '0-1000 m above ground',
    '0-6000-HTGL': '0-6000 m above ground',
    '9000-0-SPDL': '90-0 mb above ground'
}


class HRRRInventory():
    """ Class to allow quick access of HRRR GRIB products """

    __slots__ = ['_inventory']

    def __init__(self, hrrr_product: HRRRProduct):
        """ Load corresponding inventory to product """
        self._inventory = {}
        for i in range(1, hrrr_product.gdal_ds.RasterCount):
            band = hrrr_product.gdal_ds.GetRasterBand(i)
            param_dict = {}
            param_dict['idx'] = i
            param_dict['level'] = band.GetMetadata()['GRIB_SHORT_NAME']
            param_dict['level_tech_desc'] = band.GetDescription()
            param_dict['level_desc'] = level_nice_desc.get(
                param_dict['level'], '')
            param_dict['param'] = band.GetMetadata()['GRIB_ELEMENT']
            param_dict['desc'] = band.GetMetadata()['GRIB_COMMENT']
            self._inventory[i] = param_dict

    def get_product_by_index(self,
                             idxs: Union[int, List[int]]) -> Union[list, dict]:
        """
        Get HRRR product metadata by inventory index

        Args:
            idxs (Union[int, List[int]]): Integer or list of integers that correspond to
                inventory indices.

        Raises:
            ValueError: If not product exists for a given index.

        Returns:
            Union[list, dict]: Metadata dict if input is an integer. List of metadata
                dicts if input is a list.
        """
        if not isinstance(idxs, (list, tuple, set)):
            idxs = [idxs]

        # Search for indices, this is easy since
        # this is how the inventory is hashed
        product_list = []
        for idx in idxs:
            try:
                product_list.append(self._inventory[idx])
            except KeyError:
                raise ValueError('No product exists for index %s' % idx)

        # Return results
        if len(idxs) > 1:
            return product_list
        else:
            return product_list[0]

    def get_product_by_param(self,
                             params: Union[str, List[str]],
                             levels: List[str] = []) -> Union[list, dict]:
        """
        Get HRRR product metadata by parameter str.

        Args:
            params (Union[str, List[str]]): Parameter code or list of parameter codes.
            levels (List[str], optional): Levels to apply search too. Leave empty
                to search all levels. Defaults to [].

        Returns:
            Union[list, dict]: Metadata dict if input is a str. List of metadata
                dicts if input is a list.
        """
        if not isinstance(params, (list, tuple, set)):
            params = [params]

        # TODO: params aren't unique based on level!
        # First, search for params all at once
        param_list = []
        params_search = list(params).copy()
        for d in self._inventory.values():
            if d['param'] in params_search:
                if not len(levels) or d['level'] in levels:
                    param_list.append(d)

        # Return results
        return param_list