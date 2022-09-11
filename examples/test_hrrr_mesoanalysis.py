#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
from meteocre.fetchhrrr import HRRRProduct
from meteocre.fetchhrrr.mesoanalysis import hrrr_get_supercell_composite_parameter, hrrr_get_significant_tornado_parameter

# Load product from file
product = HRRRProduct.from_grib2(
    '/home/jon/Documents/meteocre_downloads/fetchhrrr/2022-04-30/hrrr.t01z.wrfsfcf00.grib2'
)

# Compute SCP / STP
scp = hrrr_get_supercell_composite_parameter(product)
stp = hrrr_get_significant_tornado_parameter(product)

# Plot the result
fig, ax = plt.subplots(1, 2, sharex=True, sharey=True)
ax[0].imshow(scp)  # type: ignore
ax[1].imshow(stp)  # type: ignore

plt.show()
