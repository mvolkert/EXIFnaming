#!/usr/bin/env python3
"""
collection of Tag operations
works with: www.sno.phy.queensu.ca/~phil/exiftool/
exiftool.exe has to be in the helpers folder
"""

__author__ = "Marco Volkert"
__copyright__ = "Copyright 2017, Marco Volkert"
__email__ = "marco.volkert24@gmx.de"
__status__ = "Development"

__all__ = ["readexif", "setexif", "nameop", "picture", "steps", "placeinfo"]

from EXIFnaming import readexif, setexif, nameop, picture, steps, placeinfo
from EXIFnaming.readexif import print_info, rename_pm, rename, order, searchby_exiftag_equality, \
    searchby_exiftag_interval, rotate, exif_to_name, print_timetable, better_gpx_via_timetable
from EXIFnaming.nameop import filter_series, rename_back, filter_primary, rename_HDR, rename_temp_back, folders_to_main, \
    copy_subdirectories
from EXIFnaming.picture import detectBlurry, detectSimilar
from EXIFnaming.setexif import shift_time, add_location, geotag, name_to_exif, fake_date, read_csv
from EXIFnaming.helpers.decode import read_exiftags, write_exiftags
from EXIFnaming.steps import step1_prepare, step2_rename, step3_filter, step4_sanitize, step5_write_exif, make_fav
