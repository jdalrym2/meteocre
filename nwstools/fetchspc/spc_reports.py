#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import abc
import csv
import requests
from datetime import datetime

import pytz


class SPCReport(abc.ABC):
    """ Abstract class to describe an SPC report """
    __slots__ = [
        'time', 'location', 'county', 'state', 'lat', 'lon', 'comments'
    ]

    def __init__(self, date, time, location, county, state, lat, lon,
                 comments):
        self.time = date.replace(hour=int(time[0:2]),
                                 minute=int(time[2:4])).astimezone(pytz.UTC)
        self.location = location
        self.county = county
        self.state = state
        self.lat = float(lat)
        self.lon = float(lon)
        self.comments = comments

    def __str__(self):
        return '(%s: Time: %s, Lat: %.3f, Lon: %.3f)' % (
            self.__class__.__name__, self.time.strftime('%Y-%m-%d %H:%M UTC'),
            self.lat, self.lon)

    def __repr__(self):
        return self.__str__()


class SPCTornadoReport(SPCReport):
    """ Class to describe an SPC tornado report """

    __slots__ = ['f_scale']

    def __init__(self, date, time, f_scale, location, county, state, lat, lon,
                 comments):
        super().__init__(date, time, location, county, state, lat, lon,
                         comments)
        self.f_scale = f_scale


class SPCHailReport(SPCReport):
    """ Class to describe an SPC hail report """

    __slots__ = ['size']

    def __init__(self, date, time, size, location, county, state, lat, lon,
                 comments):
        super().__init__(date, time, location, county, state, lat, lon,
                         comments)
        self.size = size


class SPCWindReport(SPCReport):
    """ Class to describe an SPC wind report """

    __slots__ = ['speed']

    def __init__(self, date, time, speed, location, county, state, lat, lon,
                 comments):
        super().__init__(date, time, location, county, state, lat, lon,
                         comments)
        self.speed = speed


class SPCReportFactory():
    """ Factory class to generate an SPC report object from an input string """
    TORNADO_HEADER = [
        'Time', 'F_Scale', 'Location', 'County', 'State', 'Lat', 'Lon',
        'Comments'
    ]
    WIND_HEADER = [
        'Time', 'Speed', 'Location', 'County', 'State', 'Lat', 'Lon',
        'Comments'
    ]
    HAIL_HEADER = [
        'Time', 'Size', 'Location', 'County', 'State', 'Lat', 'Lon', 'Comments'
    ]

    @classmethod
    def from_csv_line(cls, date, header, line) -> SPCReport:
        """ Return SPC report object from a CSV line """
        assert len(header) == len(line)
        if header == cls.TORNADO_HEADER:
            return SPCTornadoReport(date, *line)
        elif header == cls.WIND_HEADER:
            return SPCWindReport(date, *line)
        elif header == cls.HAIL_HEADER:
            return SPCHailReport(date, *line)
        else:
            return ValueError('Unrecognized header: %s' % repr(header))


class SPCReportsProduct():
    """ Class to hold a set of SPC reports """

    __slots__ = ['_reports']

    def __init__(self, reports):
        self.reports = reports

    @property
    def reports(self):
        return self._reports

    @reports.setter
    def reports(self, v):
        self._reports = [e for e in v if issubclass(e.__class__, SPCReport)]

    @property
    def tornado_reports(self):
        return [e for e in self.reports if e.__class__ == SPCTornadoReport]

    @property
    def wind_reports(self):
        return [e for e in self.reports if e.__class__ == SPCWindReport]

    @property
    def hail_reports(self):
        return [e for e in self.reports if e.__class__ == SPCHailReport]

    def __len__(self):
        return len(self.reports)

    @classmethod
    def fetch_for_date(cls, fetch_date: datetime):
        """ Fetch a set of SPC reports for a given date """

        reports = []

        # Build fetch URL for the date
        url = cls.build_url_for_date(fetch_date)

        # Load the data, and save it to a temp BytesIO object
        with io.BytesIO() as temp_bytes:

            # Download the CSV file
            with requests.get(url) as r:
                temp_bytes.write(r.content)
            temp_bytes.seek(0)

            # Read the CSV file
            with io.TextIOWrapper(temp_bytes) as f:
                reader = csv.reader(f)
                header = None
                for line in reader:
                    # Line's that start with 'Time' are headers, otherwise it's a report
                    if line[0] == 'Time':
                        header = line
                    else:
                        # Generate the corresponding report and append it to the lsit
                        report = SPCReportFactory.from_csv_line(
                            fetch_date, header, line)
                        reports.append(report)

        # Return the instantiated class with the reports
        return cls(reports)

    @staticmethod
    def build_url_for_date(d: datetime) -> str:
        return 'https://www.spc.noaa.gov/climo/reports/%s_rpts_filtered.csv' % d.strftime(
            r'%y%m%d')


if __name__ == '__main__':

    storm_reports = SPCReportsProduct.fetch_for_date(datetime(2019, 5, 17))

    import pdb
    pdb.set_trace()
