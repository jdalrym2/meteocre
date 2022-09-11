#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Tools for performing mesoanalysis with HRRR products """

from typing import Optional, Tuple

import numpy as np
from .hrrr_product import HRRRProduct


def hrrr_get_supercell_composite_parameter(
        product: HRRRProduct,
        bounds: Optional[Tuple[float, float, float,
                               float]] = None) -> np.ndarray:
    """
    For a given HRRR product, compute the supercell composite parameter (SCP).

    Args:
        product (HRRRProduct): HRRR product object
        bounds (Optional[Tuple[float, float, float, float]], optional): Optional bounding box: (lon_min, lat_min, lon_max, lat_max). Defaults to None.

    Returns:
        np.ndarray: SCP array
    """
    # Get needed product indices from the product's inventory
    mucape_idx = product.inventory.get_product_by_param(
        'CAPE', levels=['25500-0-SPDL'])[0]['idx']
    u_shear_rate_idx = product.inventory.get_product_by_param(
        'VUCSH', levels=['0-6000-HTGL'])[0]['idx']
    v_shear_rate_idx = product.inventory.get_product_by_param(
        'VVCSH', levels=['0-6000-HTGL'])[0]['idx']
    srh_3km_idx = product.inventory.get_product_by_param(
        'HLCY', levels=['3000-0-HTGL'])[0]['idx']

    # Fetch raster data for each product
    idx_list = [mucape_idx, u_shear_rate_idx, v_shear_rate_idx, srh_3km_idx]
    full_ar = product.to_numpy_ar(idx_list, proj='world', bounds=bounds)
    mucape_ar = full_ar[:, :, 0]
    u_shear_rate_ar = full_ar[:, :, 1]
    v_shear_rate_ar = full_ar[:, :, 2]
    srh_3km_ar = full_ar[:, :, 3]

    # Computer the bulk wind difference by taking the shear vector norm
    bwd_6km = 1.0 * np.linalg.norm(
        (u_shear_rate_ar, v_shear_rate_ar), axis=0)     # units: ms^-1

    # Compute SCP!
    scp_ar = (mucape_ar / 1000.0) * (bwd_6km / 40.0) * (srh_3km_ar / 100.0)
    scp_ar[scp_ar < 0] = 0

    return scp_ar


def hrrr_get_significant_tornado_parameter(
        product: HRRRProduct,
        bounds: Optional[Tuple[float, float, float,
                               float]] = None) -> np.ndarray:
    """
    For a given HRRR product, compute the significant tornado parameter (STP).

    Args:
        product (HRRRProduct): HRRR product object
        bounds (Optional[Tuple[float, float, float, float]], optional): Optional bounding box: (lon_min, lat_min, lon_max, lat_max). Defaults to None.

    Returns:
        np.ndarray: STP array
    """
    # Get needed product indices from the product's inventory
    sbcape_idx = product.inventory.get_product_by_param('CAPE',
                                                        levels=['0-SFC'
                                                                ])[0]['idx']
    u_shear_rate_idx = product.inventory.get_product_by_param(
        'VUCSH', levels=['0-6000-HTGL'])[0]['idx']
    v_shear_rate_idx = product.inventory.get_product_by_param(
        'VVCSH', levels=['0-6000-HTGL'])[0]['idx']
    lcl_hgt_idx = product.inventory.get_product_by_param('HGT',
                                                         levels=['0-ADCL'
                                                                 ])[0]['idx']
    srh_1km_idx = product.inventory.get_product_by_param(
        'HLCY', levels=['1000-0-HTGL'])[0]['idx']

    # Get rasters for all of the idxs
    idx_list = [
        sbcape_idx, u_shear_rate_idx, v_shear_rate_idx, lcl_hgt_idx,
        srh_1km_idx
    ]

    # Fetch raster data for each product
    full_ar = product.to_numpy_ar(idx_list, proj='world', bounds=bounds)
    sbcape_ar = full_ar[:, :, 0]
    u_shear_rate_ar = full_ar[:, :, 1]
    v_shear_rate_ar = full_ar[:, :, 2]
    lcl_hgt_ar = full_ar[:, :, 3]
    srh_1km_ar = full_ar[:, :, 4]

    # Computer the bulk wind difference by taking the shear vector norm
    bwd_6km = 1.0 * np.linalg.norm(
        (u_shear_rate_ar, v_shear_rate_ar), axis=0)     # units: ms^-1

    # Calculate STP!
    lcl_term = (2000.0 - lcl_hgt_ar) / 1000.0
    lcl_term[lcl_hgt_ar < 1000.0] = 1.0
    bwd_term = bwd_6km / 20.0
    bwd_term[bwd_6km > 30.0] = 1.5
    bwd_term[bwd_6km < 12.5] = 0.0
    stp_ar = (sbcape_ar / 1500.0) * lcl_term * (srh_1km_ar / 150.0) * bwd_term
    stp_ar[stp_ar < 0.0] = 0.0

    return stp_ar