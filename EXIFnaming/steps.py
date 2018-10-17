#!/usr/bin/env python3
"""
Steps combine multiple functions
"""

import os

from EXIFnaming.readexif import order, rename, rotate
from EXIFnaming.nameop import filter_series, rename_HDR
from EXIFnaming.setexif import name_to_exif, geotag

def step1_prepare():
    order()
    os.mkdir('.gps')
    os.mkdir('.info')

def step2_rename(Prefix="", dateformat='YYMMDD', startindex=1, onlyprint=False, postfix_stay=True, name=""):
    """
    rename for JPG and MP4
    """
    rename(Prefix, dateformat, startindex, onlyprint, postfix_stay, ".JPG", name)
    rename(Prefix, dateformat, 1, onlyprint, postfix_stay, ".MP4", name)

def step3_filter():
    filter_series()

def step4_sanitzeHDR(subname="HDRT", folder="HDR"):
    rotate(subname=subname, folder=folder, sign=1, override=True)
    rename_HDR(mode=subname, folder=folder)

def step5_write_exif():
    name_to_exif(artist="Marco Volkert", additional_tags=(), startdir=None)
    geotag(timezone=2, offset="")