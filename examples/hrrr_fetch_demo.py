#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime

import pytz

from meteocre.fetchhrrr import HRRRProduct
from meteocre.fetchhrrr.visualize.nws_standard_colormaps import cm_dpt

if __name__ == '__main__':

    run_time = datetime(2018, 5, 1, 18, 0, 0).replace(tzinfo=pytz.UTC)
    forecast_hour = 6
    product_id = 'sfc'

    product = HRRRProduct.from_archive(run_time, forecast_hour, product_id)

    ds = product.get_ds_for_product_idx([57])
    im = ds.GetRasterBand(1).ReadAsArray()

    import matplotlib.pyplot as plt
    plt.imshow(im, **cm_dpt())
    plt.show()
