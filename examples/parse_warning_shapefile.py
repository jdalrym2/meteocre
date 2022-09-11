#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from osgeo import ogr

from meteocre.fetchwwa import WWAPolygon

if __name__ == '__main__':
    warning_path = '/home/jon/git/meteocre/data/2021_tsmf/wwa_202101010000_202112312359.shp'

    ds = ogr.Open(warning_path)
    layer = ds.GetLayer(0)

    for idx in range(layer.GetFeatureCount()):
        f = layer.GetFeature(idx)
        p = WWAPolygon.from_ogr_feature(f)
        if not p.is_thunderstorm_related:
            continue
        print(p.phenom_text, p.poly_begin_time)
