#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pathlib
import matplotlib

import matplotlib.pyplot as plt

from meteocre.fetchmrms import MRMSRotationProduct, MRMSReflectivityProduct, MRMSSevereHailIndexProduct, MRMSMaximumExpectedSizeOfHailProduct
from meteocre.fetchmrms.colormaps import mrms_rotation_cmap

bounds = (-102.0506, 36.9927, -94.6046, 40.0087)
grib2_path = pathlib.Path(
    '/home/jon/workspace/storm_router/case_studies/Andover_Tornado_042922/MRMS/raw/MergedBaseReflectivityQC/MRMS_MergedBaseReflectivityQC_00.50_20220430-055811.grib2.gz'
     #'/home/jon/git/meteocre/data/MRMS/2022043001/CONUS/MergedBaseReflectivityQC/MRMS_MergedBaseReflectivityQC_00.50_20220430-013004.grib2.gz'
     #'/home/jon/git/meteocre/data/MRMS/2022043001/CONUS/SHI/MRMS_SHI_00.50_20220430-013038.grib2.gz'
     #'/home/jon/git/meteocre/data/MRMS/2022043001/CONUS/MESH/MRMS_MESH_00.50_20220430-013038.grib2.gz'
)

p = MRMSReflectivityProduct.from_grib2(grib2_path)


# p_element = p.get_grib_metadata()['GRIB_ELEMENT']
# this_raster_path = raster_path / p_element
# this_raster_path.mkdir(exist_ok=True)
# this_plot_path = plot_path / p_element
# this_plot_path.mkdir(exist_ok=True)

# this_raster = this_raster_path / f'{grib2_path.stem}.tif'
# if this_raster.exists():
#     this_raster.unlink()
# this_plot = this_plot_path / f'{grib2_path.stem}.png'
# if this_plot.exists():
#     this_plot.unlink()

#fig, ax = p.plot_default(bounds=bounds, save_path=None)
#fig.set_size_inches((16, 6))
#plt.show()
#fig.savefig(str(this_plot))
#plt.close(fig)
