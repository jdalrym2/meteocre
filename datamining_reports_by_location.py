#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# %% Imports
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

pio.renderers.default = 'browser'
import matplotlib.cm as cm
from matplotlib.colors import rgb2hex

from nwstools.stormevents import fetch_from_storm_events_archive

# %% Get set of all detailed reports from 2015-2020
all_reports = []
for query_year in range(2015, 2020 + 1):
    all_reports.extend(
        fetch_from_storm_events_archive(query_year, 'details')['details'])

# Filter reports based on whether or not it's an EF-2+ tornado
ef2_plus_reports = []
for report in all_reports:
    if report.is_tornado_event and report.tornado['f-scale'] in ('EF2', 'EF3',
                                                                 'EF4', 'EF5'):
        ef2_plus_reports.append(report)
del all_reports
# %% Generate bar chart of tornadoes by intensity

intensity_dict = dict(EF2=0, EF3=0, EF4=0, EF5=0)

for report in ef2_plus_reports:
    intensity_dict[report.tornado['f-scale']] += 1
labels, counts = list(intensity_dict.keys()), list(intensity_dict.values())

fig, ax = plt.subplots()
ax.set_title('Strong Tornadoes by Strength: 2015-2020')
ax.bar(labels, counts, color='darkslateblue')
ax.bar_label(ax.containers[0])
ax.set_ylim((0, 750))
ax.set_xlabel('Tornado Strength')
ax.set_ylabel('Count')

# %% Generate bar chart of strong tornadoes by year
year_dict = {
    2015: 0,
    2016: 0,
    2017: 0,
    2018: 0,
    2019: 0,
    2020: 0,
}
for report in ef2_plus_reports:
    year_dict[report.start_time.year] += 1
labels, counts = list(year_dict.keys()), list(year_dict.values())

fig, ax = plt.subplots()
ax.set_title('Strong Tornadoes by Year: 2015-2020')
ax.bar(labels, counts, color='darkslateblue')
ax.bar_label(ax.containers[0])
ax.set_ylim((0, 250))
ax.set_xlabel('Year')
ax.set_ylabel('Count')
plt.show()

# %% Generate geographic plot

cmap_lookup = {
    'EF2': rgb2hex(cm.get_cmap('jet')(0.5)),
    'EF3': rgb2hex(cm.get_cmap('jet')(0.7)),
    'EF4': rgb2hex(cm.get_cmap('jet')(0.9)),
    'EF5': rgb2hex(cm.get_cmap('jet')(1.0))
}

lat_ar = np.array([
    e.begin_location['lat'] for e in ef2_plus_reports if e.tornado['f-scale']
])
lon_ar = np.array([e.begin_location['lon'] for e in ef2_plus_reports])
ef_ar = np.array([e.tornado['f-scale'] for e in ef2_plus_reports])
color_ar = np.array([cmap_lookup[e] for e in ef_ar])

dfs = []
for s in ('EF2', 'EF3', 'EF4', 'EF5'):
    v = ef_ar == s
    df = pd.DataFrame(
        dict(lat=lat_ar[v],
             lon=lon_ar[v],
             ef=ef_ar[v],
             color=color_ar[v],
             name=s))
    dfs.append(
        go.Scattergeo(
            lon=df['lon'],
            lat=df['lat'],
            text=df['ef'],
            name=s,
            mode='markers',
            marker_color=df['color'],
        ))

fig = go.Figure(data=dfs)

fig.add_trace(
    go.Scattergeo(lon=[-102, -94.5, -94.5, -102, -102],
                  lat=[43, 43, 31, 31, 43],
                  fill='toself',
                  fillcolor='rgba(0.8, 0, 0, 0.3)',
                  mode='none',
                  name='Central / Southern Great Plains'))

fig.add_trace(
    go.Scattergeo(lon=[-94.5, -82, -82, -94.5, -94.5],
                  lat=[36.5, 36.5, 29, 29, 36.5],
                  fill='toself',
                  fillcolor='rgba(0, 0, 0.8, 0.3)',
                  mode='none',
                  name='Dixie Alley'))

fig.add_trace(
    go.Scattergeo(lon=[-94.5, -82, -82, -94.5, -94.5],
                  lat=[43, 43, 36.5, 36, 5, 43],
                  fill='toself',
                  fillcolor='rgba(0.8, 0.8, 0, 0.3)',
                  mode='none',
                  name='Midwest'))

fig.update_layout(title=go.layout.Title(text=(
    'Strong Tornado Reports: 2015-2020<br>'
    '<sup>(Source: NOAA NCEI Storm Events Database)</sup>'),
                                        x=0.5))

fig.update_geos(visible=False,
                resolution=110,
                scope="usa",
                showcountries=True,
                countrycolor="Black",
                showsubunits=True,
                subunitcolor="Blue")
fig.show()

#%% Generate climatology histogram by region

import matplotlib.dates as mdates
from datetime import datetime

GREAT_PLAINS_REGION = [31, -102, 43, -94.5]
DIXIE_ALLEY_REGION = [29, -94.5, 36.5, -82]
MIDWEST_REGION = [36.5, -94.5, 43, -82]


def rolling_sum(ar, n):
    assert n >= 2
    c_ar = np.concatenate((ar[-(n - 1):], ar))
    cs = np.cumsum(c_ar)
    cs_2 = np.pad(cs[:-n], (n, 0))
    return (cs - cs_2)[(n - 1):]


bins = [
    mdates.date2num(datetime(2000, 1, 1)),
    mdates.date2num(datetime(2000, 1, 15)),
    mdates.date2num(datetime(2000, 2, 1)),
    mdates.date2num(datetime(2000, 2, 15)),
    mdates.date2num(datetime(2000, 3, 1)),
    mdates.date2num(datetime(2000, 3, 15)),
    mdates.date2num(datetime(2000, 4, 1)),
    mdates.date2num(datetime(2000, 4, 15)),
    mdates.date2num(datetime(2000, 5, 1)),
    mdates.date2num(datetime(2000, 5, 15)),
    mdates.date2num(datetime(2000, 6, 1)),
    mdates.date2num(datetime(2000, 6, 15)),
    mdates.date2num(datetime(2000, 7, 1)),
    mdates.date2num(datetime(2000, 7, 15)),
    mdates.date2num(datetime(2000, 8, 1)),
    mdates.date2num(datetime(2000, 8, 15)),
    mdates.date2num(datetime(2000, 9, 1)),
    mdates.date2num(datetime(2000, 9, 15)),
    mdates.date2num(datetime(2000, 10, 1)),
    mdates.date2num(datetime(2000, 10, 15)),
    mdates.date2num(datetime(2000, 11, 1)),
    mdates.date2num(datetime(2000, 11, 15)),
    mdates.date2num(datetime(2000, 12, 1)),
    mdates.date2num(datetime(2000, 12, 15)),
]

fig, ax_o = plt.subplots()
dates = []
seasons = []
print('Seasons:\n')
for region, region_name in zip(
    (GREAT_PLAINS_REGION, DIXIE_ALLEY_REGION, MIDWEST_REGION),
    ('Great Plains', 'Dixie Alley', 'Midwest')):
    lat_min, lon_min, lat_max, lon_max = region
    dates.append([])
    for report in ef2_plus_reports:
        report_lat = report.begin_location['lat']
        report_lon = report.begin_location['lon']

        if (lat_min <= report_lat <= lat_max
                and lon_min <= report_lon <= lon_max):
            dates[-1].append(report.start_time.replace(year=2000))
    fig, ax = plt.subplots()
    vals, _, _ = ax.hist(dates[-1],
                         bins=bins,
                         color='darkslateblue',
                         density=True)
    ax.set_title('Strong Tornado Reports by Two Week Period: %s' % region_name)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    n = 4
    rolling = rolling_sum(vals, n=n)
    season_start_date = bins[np.argmax(rolling) - (n - 1)]
    season_end_date = bins[np.argmax(rolling) + 1]
    seasons.append((season_start_date, season_end_date))
    print(region_name, mdates.num2date(season_start_date),
          mdates.num2date(season_end_date))
    ax.vlines([season_start_date, season_end_date],
              0,
              np.max(vals),
              linestyles='dotted',
              color='r')

vals, _, _ = ax_o.hist(dates,
                       bins=bins,
                       stacked=True,
                       color=('lightcoral', 'lightgreen', 'cornflowerblue'),
                       label=('Great Plains', 'Dixie Alley', 'Midwest'))
ax_o.set_title('Strong Tornado Reports by Two Week Period')
ax_o.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
ax_o.legend()
plt.show()
