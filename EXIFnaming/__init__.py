#!/usr/bin/env python3
"""
Tools for organizing and tagging photos

works with exiftool: www.sno.phy.queensu.ca/~phil/exiftool/
exiftool.exe has to be in the helpers folder or path to it configured in settings
"""

__author__ = "Marco Volkert"
__copyright__ = "Copyright 2017, Marco Volkert"
__email__ = "marco.volkert24@gmx.de"
__status__ = "Development"

__all__ = ["readexif", "setexif", "nameop", "picture", "steps", "placeinfo"]

from EXIFnaming import readexif, setexif, nameop, picture, steps, placeinfo
from EXIFnaming.helpers import settings
from EXIFnaming.helpers.decode import read_exiftags, write_exiftags
from EXIFnaming.nameop import filter_series, rename_back, filter_primary, rename_HDR, rename_temp_back, folders_to_main, \
    copy_subdirectories
from EXIFnaming.nameop import filter_series, filter_primary, copy_subdirectories, copy_files, copy_new_files, \
    replace_in_file, folders_to_main, rename_HDR, sanitize_filename, rename_temp_back, rename_back, \
    create_tags_csv, create_tags_csv_per_dir, create_counters_csv, create_counters_csv_per_dir, \
    create_names_csv_per_dir, create_example_csvs, create_rating_csv, move_each_pretag_to_folder
from EXIFnaming.picture import detect_blurry, detect_similar, resize
from EXIFnaming.readexif import print_info, rename, order, searchby_exiftag_equality, \
    searchby_exiftag_interval, rotate, rename_from_exif, print_timetable, better_gpx_via_timetable
from EXIFnaming.setexif import shift_time, geotag, fake_date, write_exif_using_csv, copy_exif_via_mainname
from EXIFnaming.steps import step1_prepare, step2_rename, step3_filter, step4_sanitize, step5_write_exif, make_fav
