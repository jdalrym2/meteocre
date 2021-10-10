#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Class to allow quick access of HRRR GRIB products """

from __future__ import annotations
import json
from typing import Union
from . import HRRR_VERSION_JSON_MAP

# Type hint HRRRProduct w/o circular dependency
# See: https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
# Thanks linting!
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import HRRRProduct


class HRRRInventory():
    """ Class to allow quick access of HRRR GRIB products """

    __slots__ = ['_inventory']

    def __init__(self, hrrr_product: HRRRProduct):
        """ Load corresponding inventory to product """
        with open(HRRR_VERSION_JSON_MAP[hrrr_product.product_version],
                  'r') as f:
            json_dict = json.load(f)
        for hour_str, hour_dict in json_dict[hrrr_product.product_id].items():
            hour_list = [int(e.strip()) for e in hour_str.split(',')]
            if hrrr_product.forecast_hour in hour_list:
                self._inventory = hour_dict
                break
        if self._inventory is None:
            raise ValueError('Could not find inventory for product!')

    def get_product_by_index(self, idxs) -> Union[list, dict]:
        """ Get product by index """
        if not isinstance(idxs, (list, tuple, set)):
            idxs = [idxs]

        # Search for indices, this is easy since
        # this is how the inventory is hashed
        product_list = []
        for idx in idxs:
            try:
                product_list.append(self._inventory[str(idx)])
            except KeyError:
                raise ValueError('No product exists for index %s' % idx)

        # Return results
        if len(idxs) > 1:
            return product_list
        else:
            return product_list[0]

    def get_product_by_param(self, params) -> Union[list, dict]:
        """ Get product by param code """
        if not isinstance(params, (list, tuple, set)):
            params = [params]

        # TODO: params aren't unique based on level!
        # First, search for params all at once
        # we will get an out of order list
        param_list_unsorted = []
        params_search = list(params).copy()
        for d in self._inventory.values():
            if d['param'] in params_search:
                param_list_unsorted.append(d)
                del params_search[params_search.index(d['param'])]

        # Now, sort the list based on the params we've been given
        params_unsorted = [e['param'] for e in param_list_unsorted]
        param_list = []
        for param in params:
            param_list.append(
                param_list_unsorted[params_unsorted.index(param)])

        # Return results
        if len(params) > 1:
            return param_list
        else:
            return param_list[0]
