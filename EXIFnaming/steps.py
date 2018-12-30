#!/usr/bin/env python3
"""
Steps combine multiple functions
"""
from EXIFnaming.nameop import filter_series, rename_HDR, sanitize_filename, create_example_csvs
from EXIFnaming.readexif import order, rename, rotate
from EXIFnaming.setexif import geotag, read_csv


def step1_prepare():
    create_example_csvs()
    order()


def step2_rename(Prefix="", dateformat='YYMMDD', startindex=1, onlyprint=False, postfix_stay=True, name=""):
    """
    rename for JPG and MP4
    """
    rename(Prefix, dateformat, startindex, onlyprint, postfix_stay, False, name)
    rename(Prefix, dateformat, 1, onlyprint, postfix_stay, True, name)


def step3_filter():
    """
    filter Series
    """
    filter_series()


def step4_sanitize(subname="HDRT", folder="HDR"):
    """
    sanitize postprocessing
    :param subname: name of HDR
    :param folder: name of HDR folder
    :return:
    """
    rename_HDR(mode=subname, folder=folder)
    rotate(subname=subname, folder=folder, sign=1, override=True)
    sanitize_filename()


def step5_write_exif(csv_restriction="fav"):
    """
    write exif via csv, filename and gpx files
    """
    read_csv("*", csv_restriction=csv_restriction)
    geotag(timezone=2, offset="")
