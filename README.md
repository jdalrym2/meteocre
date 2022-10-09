# Meteocre

`meteocre` is a Python library I wrote for meteorological data fetching and processing, so I can pretend to be a meteorologist. The goal of this library is to provide a quick interface to several meteorological data sources, and basic tools to process them to mine useful data.

Currently added meteorological data sources are:
- HRRR Products
- MRMS Products
- SPC Storm Reports
- Watches / Warnings Archive
- Storm Events Archive

This project is the amalgamation of many smaller tools I've written to do meteorological data processing for various projects, both for school and for fun. The goal for this project is to provide these interfaces so others don't need to reinvent the wheel. Much of NOAA's data is public domain, but the means of accessing this data changes per data source. This is an attempt to make this process simple and entirely contained within Python.

## Installation & Setup

[ TODO ]

## Examples

See demo notebooks.

## Similar Projects

`metpy` - 

## Credits

[ Credits for stuff I borrowed ]

## TODO List

Features:
- [ ] Broader NetCDF support

Data Sources:
- [ ] GOES Imagery + reprojection of imagery to Web Mercator

## License

MIT &copy; 2022 Jon Dalrymple