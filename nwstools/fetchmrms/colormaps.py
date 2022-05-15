#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inspired much by Brian Blaylock's pyBKB project, see here:
https://github.com/blaylockbk/pyBKB_v2/blob/master/BB_cmap/NWS_standard_cmap.py
"""

import numpy as np
import matplotlib as mpl


def mrms_rotation_cmap():
    """ Colormap for MRMS Rotation Rate """

    # Estimated rotation speed (0.001/sec)
    a = [1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20]

    # Normalize the bin between 0 and 1 (uneven bins are important here)
    norm = [(float(i) - min(a)) / (max(a) - min(a)) for i in a]

    # Color tuple for every bin
    rgb = np.array([(160, 160, 160), (120, 120, 120), (80, 80, 80),
                    (119, 119, 0), (153, 153, 0), (187, 187, 0), (221, 221, 0),
                    (255, 255, 0), (119, 0, 0), (153, 0, 0), (187, 0, 0),
                    (221, 0, 0), (255, 0, 0), (0, 187, 187), (0, 255, 255)])

    # Create the colormap
    cmap, norm = mpl.colors.from_levels_and_colors(
        a, rgb / 255., extend='max')     # type: ignore

    return cmap, norm


def mrms_refl_cmap():
    """ Colormap for MRMS Reflectivity """

    # Estimated reflectivity [dBZ]
    a = [
        -35, -30, -25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25, 30, 35, 40, 45,
        50, 55, 60, 65, 70
    ]

    # Normalize the bin between 0 and 1 (uneven bins are important here)
    norm = [(float(i) - min(a)) / (max(a) - min(a)) for i in a]

    # Color tuple for every bin
    rgb = np.array([(221, 254, 255), (216, 210, 233), (208, 175, 212),
                    (163, 127, 167), (115, 74, 119), (214, 212, 173),
                    (169, 168, 125), (119, 119, 119), (0, 236, 236),
                    (1, 160, 246), (0, 0, 246), (0, 255, 0), (0, 200, 0),
                    (0, 144, 0), (255, 255, 0), (231, 192, 0), (255, 144, 0),
                    (255, 0, 0), (220, 0, 0), (192, 0, 0), (255, 0, 255),
                    (153, 85, 201)])

    # Create the colormap
    cmap, norm = mpl.colors.from_levels_and_colors(
        a, rgb / 255., extend='max')     # type: ignore

    return cmap, norm


def mrms_shi_cmap():
    """ Colormap for MRMS Severe Hail Index (SHI) """

    # Severe Hail Index []
    a = [0, 0.5, 1, 2, 3, 4, 5, 6, 8, 10, 15, 25, 50, 150]

    # Normalize the bin between 0 and 1 (uneven bins are important here)
    norm = [(float(i) - min(a)) / (max(a) - min(a)) for i in a]

    # Color tuple for every bin
    rgb = np.array([(0, 236, 236), (1, 160, 246), (0, 0, 246), (0, 255, 0),
                    (0, 200, 0), (0, 144, 0), (255, 255, 0), (231, 192, 0),
                    (255, 144, 0), (255, 0, 0), (192, 0, 0), (255, 0, 255),
                    (190, 85, 220), (126, 50, 167)])

    # Create the colormap
    cmap, norm = mpl.colors.from_levels_and_colors(
        a, rgb / 255., extend='max')     # type: ignore

    return cmap, norm


def mrms_mesh_cmap():
    """ Colormap for MRMS Max Estimated Size of Hail [MESH] """

    # Max Estimated Size of Hail [,mm]
    a = [0, 1, 2, 4, 6, 8, 10, 15, 20, 30, 40, 50, 75, 100]

    # Normalize the bin between 0 and 1 (uneven bins are important here)
    norm = [(float(i) - min(a)) / (max(a) - min(a)) for i in a]

    # Color tuple for every bin
    rgb = np.array([(0, 236, 236), (1, 160, 246), (0, 0, 246), (0, 255, 0),
                    (0, 200, 0), (0, 144, 0), (255, 255, 0), (231, 192, 0),
                    (255, 144, 0), (255, 0, 0), (192, 0, 0), (255, 0, 255),
                    (190, 85, 220), (126, 50, 167)])

    # Create the colormap
    cmap, norm = mpl.colors.from_levels_and_colors(
        a, rgb / 255., extend='max')     # type: ignore

    return cmap, norm