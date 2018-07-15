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

from EXIFnaming.getTags import printinfo, rename_PM, rename, order, searchByTagEquality, searchByTagInterval, rotate, \
    exifToName, print_timeinterval
from EXIFnaming.picture import detectBlurry, detectSimilar, filterSeries, renameBack, filterPrimary, renameHDR, \
    renameTempBackAll, foldersToMain
from EXIFnaming.setTags import adjustDate, addLocation, nameToExif, geotag
