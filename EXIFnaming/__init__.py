#!/usr/bin/env python3
"""
collection of Tag operations
works with: www.sno.phy.queensu.ca/~phil/exiftool/
exiftool.exe has to be in the same folder
"""

__author__ = "Marco Volkert"
__copyright__ = "Copyright 2017, Marco Volkert"
__email__ = "marco.volkert24@gmx.de"
__status__ = "Development"

from EXIFnaming.readexif import print_info, rename_pm, rename, order, searchby_exiftag_equality, searchby_exiftag_interval, rotate, \
    exif_to_name, print_timeinterval
from EXIFnaming.nameop import filter_series, rename_back, filter_primary, rename_HDR, \
    rename_temp_back, folders_to_main, copy_subdirectories
from EXIFnaming.picture import detectBlurry, detectSimilar
from EXIFnaming.setexif import shift_time, add_location, geotag, name_to_exif, fake_date

includeSubdirs = True


def set_includeSubdirs(toInclude=True):
    global includeSubdirs
    includeSubdirs = toInclude
    print("modifySubdirs:", includeSubdirs)