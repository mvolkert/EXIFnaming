#!/usr/bin/env python3
"""
Steps combine multiple functions
"""
from EXIFnaming.nameop import filter_series, rename_HDR, sanitize_filename, create_example_csvs, create_rating_csv
from EXIFnaming.readexif import order, rename, rotate
from EXIFnaming.setexif import geotag, write_exif_using_csv

__all__ = ["step1_prepare", "step2_rename", "step3_filter", "step4_sanitize", "step5_write_exif", "make_fav"]


def step1_prepare():
    create_example_csvs()
    order()


def step2_rename(Prefix="", dateformat='YYMMDD', startindex=1, onlyprint=False, keeptags=True, name=""):
    """
    rename for JPG and MP4
    """
    rename(Prefix, dateformat, startindex, onlyprint, keeptags, False, name)
    rename(Prefix, dateformat, 1, onlyprint, keeptags, True, name)


def step3_filter():
    """
    filter Series
    """
    filter_series()


def step4_sanitize(subname: str = "HDR", folder: str = ""):
    """
    sanitize postprocessing
    :param subname: name of HDR
    :param folder: name of HDR folder
    """
    rename_HDR(mode=subname, folder=folder)
    rotate(subname=subname, folder=folder, sign=1, override=True, ask=False)
    sanitize_filename(folder=r"", posttags_to_end=None, onlyprint=False)


def step5_write_exif(timezone: int, csv_restriction: str = ""):
    """
    write exif using csv, filename and gpx files
    :param timezone: number of hours offset for geotag
    :param csv_restriction: files that do not pass any of the restriction in this file are not modified at all.
        if empty: no restriction
    """
    write_exif_using_csv("*", csv_restriction=csv_restriction)
    geotag(timezone=timezone, offset="")


def make_fav(timezone: int):
    """
    easy way to finalize just the favorites
    :param timezone: number of hours offset for geotag
    """
    sanitize_filename(folder=r"", posttags_to_end=None, onlyprint=False)
    create_rating_csv(rating=4, subdir="")
    geotag(timezone=timezone, offset="")
    write_exif_using_csv("*", csv_restriction="", import_exif=False, overwrite_gps=False)
