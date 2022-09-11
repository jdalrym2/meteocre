#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from meteocre.fetchmrms.probsevere import ProbSevereProductCollection
from meteocre.fetchmrms.probsevere.plots import panel_plot_for_track

path = '/home/jon/git/meteocre/data/MRMS/2022043001/ProbSevere/'

# ds = gdal.OpenEx(path, open_options=['NATIVE_DATA=YES'])
# l = ds.GetLayer(0)
# f = l.GetFeature(0)
# print(f.ExportToJson())

# Read in MRMS ProbSevere data
col = ProbSevereProductCollection.from_directory(path)

# Compute feature tracks
tracks = col.compute_feature_tracks()

# For each track, compute max probtor [%]
track_max_probtor = {
    track_id: max(track.probtor_trend)
    for track_id, track in tracks.items()
}

# Find ID of track that has the max probtor value
max_probtor_track_id = max(track_max_probtor,
                           key=track_max_probtor.get)     # type: ignore

print(max_probtor_track_id)

import matplotlib.pyplot as plt

panel_plot_for_track(tracks[max_probtor_track_id])
plt.show()