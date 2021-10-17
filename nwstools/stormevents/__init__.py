import pathlib

from .. import get_logger as _get_logger
from .. import get_download_dir as _get_download_dir


def get_logger():
    return _get_logger()


def get_download_dir():
    d = pathlib.Path(_get_download_dir(), 'stormevents')
    d.mkdir(parents=False, exist_ok=True)
    return d


from .storm_event_detailed_report import StormEventDetailedReport
from .storm_event_fatality_report import StormEventFatalityReport
from .storm_event_location import StormEventLocation
from .fetch import fetch_from_storm_events_archive