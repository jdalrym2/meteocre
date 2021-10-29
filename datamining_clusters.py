#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import scipy.cluster
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap as Basemap

matplotlib.use('Agg')
US_SHP_PATH = './data/cb_2018_us_state_5m/cb_2018_us_state_5m'


class USClusterPlot:
    def __init__(self):

        # Generate a plot
        self.fig, self.ax = plt.subplots()

        # Lambert Conformal map of lower 48 states.
        self.m = Basemap(llcrnrlon=-119,
                         llcrnrlat=22,
                         urcrnrlon=-64,
                         urcrnrlat=49,
                         projection='lcc',
                         lat_1=33,
                         lat_2=45,
                         lon_0=-95)

        # Draw the state boundaries from a shape file
        self.m.readshapefile(US_SHP_PATH, 'states', drawbounds=True)

    def add_cluster(self, lons, lats, centroid, radius, color='r'):
        x, y = self.m(lons, lats)
        self.m.scatter(x, y, marker='o', color=color, zorder=5)
        clon, clat = centroid
        self.m.tissot(clon,
                      clat,
                      np.rad2deg(radius / 6367.),
                      256,
                      color=color,
                      fill=False)


def haversine_np(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)

    All args must be of equal length.

    https://stackoverflow.com/questions/29545704/fast-haversine-approximation-python-pandas

    """
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(
        dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2

    c = 2 * np.arcsin(np.sqrt(a))
    km = 6367 * c
    return km


def optimize_k_means(locs, criterion, criterion_kwargs):
    locs_len = locs.shape[0]
    if locs_len > 1:
        for k in range(1, locs_len):
            # If we fail over 100 times in a row, just assign each point to its own cluster
            for _ in range(100):
                try:
                    centroids, labels = scipy.cluster.vq.kmeans2(
                        locs, k, minit='points')
                    if criterion(locs, centroids, labels,
                                 **dict(criterion_kwargs)):
                        return centroids, labels
                except ValueError:
                    # Happens when K-means init was sub-par
                    print('Re-running K-means')
                else:
                    pass
    return locs, np.arange(locs_len, dtype=int)


if __name__ == '__main__':

    import pickle
    import pathlib
    import numpy as np

    # Array of plot colors
    colors = ['r', 'b', 'g', 'm', 'y', 'o', 'p', 'k']

    # Threshold radius
    radius_km = 120

    def criterion(locs, centroids, labels, **kwargs):
        """ Criterion to tell if K-means clustering of our points
            is sufficient """

        # Loop through all the provided centroids
        # and obtain associated points
        crit = []
        for idx, centroid in enumerate(centroids):
            cur_locs = locs[labels == idx]
            if cur_locs.ndim == 1:
                cur_locs.reshape(1, -1)
            cur_locs_cm = np.repeat(centroid.reshape(1, -1),
                                    cur_locs.shape[0],
                                    axis=0)
            # Compute array of haversince distances from the points to
            # the determined centroid
            dist = haversine_np(cur_locs[:, 1], cur_locs[:, 0],
                                cur_locs_cm[:, 1], cur_locs_cm[:, 0])

            # If all of the distances are less than the threshold, our
            # solution is sufficient
            crit.append(np.max(dist) < kwargs.get('radius_km'))

        return all(crit)

    # Load locations
    with open('./data/positive_reports_holdout.pkl', 'rb') as f:
        pos = pickle.load(f)

    # Location to save plots
    plot_save_path = pathlib.Path('./data/holdout_cluster_plots').resolve()

    # Location to save new mapping
    clusters_save_path = pathlib.Path(
        './data/positive_clusters_holdout.pkl').resolve()
    clusters_map = {}

    # Loop through days with strong tornadoes
    for region_name, region_dict in pos.items():
        clusters_map[region_name] = {}
        for dt, locs in region_dict.items():
            dt = dt.replace(tzinfo=None)
            locs = np.array(locs)
            clusters_map[region_name][dt] = []

            # Find the optimal K-means solution for this day
            centroids, labels = optimize_k_means(locs, criterion,
                                                 [('radius_km', radius_km)])

            # Persist determined centroids
            for centroid in centroids:
                clusters_map[region_name][dt].append(tuple(centroid))

            # Generate plot of the solution
            us_map = USClusterPlot()
            for idx, (color, (k_c_lat,
                              k_c_lon)) in enumerate(zip(colors, centroids)):
                this_locs = locs[labels == idx]
                us_map.add_cluster(this_locs[:, 1],
                                   this_locs[:, 0], (k_c_lon, k_c_lat),
                                   radius_km,
                                   color=color)
            us_map.ax.set_title('%s: %s' %
                                (region_name, dt.strftime('%Y-%m-%d')))

            # Save plot
            output_plot_path = pathlib.Path(
                plot_save_path, '%s_%s.png' %
                (region_name.replace(' ', '-'), dt.strftime('%Y-%m-%d')))
            us_map.fig.savefig(str(output_plot_path))
            plt.close(us_map.fig)

    # Save cluster centroids
    with open(clusters_save_path, 'wb') as f:
        pickle.dump(clusters_map, f)