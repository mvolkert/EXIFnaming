#!/usr/bin/env python3
"""
Just ideas
"""

import os
import shutil

from EXIFnaming import includeSubdirs
from EXIFnaming.helpers.date import giveDatetime
from EXIFnaming.helpers.decode import read_exiftags, has_not_keys
from EXIFnaming.helpers.tags import getPath, getSequenceNumber, getDate, is_series, is_sun


def _detect_3D():
    """
    not yet fully implemented
    """
    inpath = os.getcwd()
    Tagdict = read_exiftags(inpath, includeSubdirs)
    if has_not_keys(Tagdict,
                    keys=["Directory", "File Name", "Date/Time Original", "Burst Mode", "Sequence Number"]): return
    time_old = giveDatetime()
    filenames = []
    dir3D = "3D"
    for i in range(len(list(Tagdict.values())[0])):
        newDir = os.path.join(Tagdict["Directory"][i], dir3D)
        os.makedirs(newDir, exist_ok=True)
        SequenceNumber = getSequenceNumber(Tagdict, i)
        if is_series(Tagdict, i) or SequenceNumber > 1: continue
        time = giveDatetime(getDate(Tagdict, i))
        timedelta = time - time_old
        timedelta_sec = timedelta.days * 3600 * 24 + timedelta.seconds
        time_old = time
        if timedelta_sec < 10 or (SequenceNumber == 1 and timedelta_sec < 15) or filenames == []:
            filenames.append(getPath(Tagdict, i))
        elif len(filenames) > 1:
            for filename in filenames:
                if os.path.isfile(filename.replace(Tagdict["Directory"][i], newDir)): continue
                shutil.copy2(filename, newDir)
            filenames = []
            # shutil.copy2("filename","destdir")
    # exclude is_series and SequenceNumber>1
    # more than one picture within 10s


def _detect_sunset():
    """
    not yet fully implemented
    """
    inpath = os.getcwd()
    Tagdict = read_exiftags(inpath, includeSubdirs)
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Scene Mode"]): return
    for i in range(len(list(Tagdict.values())[0])):
        newDir = os.path.join(Tagdict["Directory"][i], "Sunset")
        os.makedirs(newDir, exist_ok=True)
        time = giveDatetime(getDate(Tagdict, i))
        if 23 < time.hour or time.hour < 17: continue
        if not is_sun(Tagdict, i): continue
        filename = getPath(Tagdict, i)
        if os.path.isfile(filename.replace(Tagdict["Directory"][i], newDir)): continue
        shutil.copy2(filename, newDir)
        # evening and Sun1 or Sun2 are used
