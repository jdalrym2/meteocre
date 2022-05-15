#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" ProbSevere plotting convenience functions """

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as dates

from .feature_track import ProbSevereFeatureTrack


def panel_plot_for_track(track: ProbSevereFeatureTrack):
    """
    Create a simple plot of probability trends for a given track

    Args:
        track (ProbSevereFeatureTrack): Input track
    """

    def set_locator(_ax):
        _ax.xaxis.set_minor_locator(dates.MinuteLocator(interval=2))
        _ax.xaxis.set_major_locator(dates.MinuteLocator(interval=10))
        _ax.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))

    ax: np.ndarray
    fig, ax = plt.subplots(2, 2, sharex=True, sharey=False)     # type: ignore

    fig.suptitle('Track ID: %d' % track.feat_id)

    set_locator(ax[0][0])
    ax[0][0].plot(track.valid_times, track.probsevere_trend)
    ax[0][0].set_xlabel('Time (UTC)')
    ax[0][0].set_ylabel('ProbSevere [%]')
    ax[0][0].grid()

    set_locator(ax[0][1])
    ax[0][1].plot(track.valid_times, track.probtor_trend)
    ax[0][1].set_xlabel('Time (UTC)')
    ax[0][1].set_ylabel('ProbTor [%]')
    ax[0][1].grid()

    set_locator(ax[1][0])
    ax[1][0].plot(track.valid_times, track.probhail_trend)
    ax[1][0].set_xlabel('Time (UTC)')
    ax[1][0].set_ylabel('ProbHail [%]')
    ax[1][0].grid()

    set_locator(ax[1][1])
    ax[1][1].plot(track.valid_times, track.probwind_trend)
    ax[1][1].set_xlabel('Time (UTC)')
    ax[1][1].set_ylabel('ProbWind [%]')
    ax[1][1].grid()