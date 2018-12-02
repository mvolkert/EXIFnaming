#!/usr/bin/env python3

"""
collection of Tag tools
"""

import os

from EXIFnaming.helpers.decode import has_not_keys
from EXIFnaming.models import *
from EXIFnaming.models.ModelBase import ModelBase

def getPath(Tagdict, i: int):
    if not all([x in Tagdict for x in ["Directory", "File Name"]]):
        print("Directory or File Name is not in Tagdict")
        return ""
    return os.path.join(Tagdict["Directory"][i], Tagdict["File Name"][i])


def checkIntegrity(Tagdict, fileext=".JPG"):
    """
    :return: None if not primary keys, false if not advanced keys
    """
    # check integrity
    if len(Tagdict) == 0: return
    keysPrim = ["Directory", "File Name", "Date/Time Original"]
    keysJPG = ["Image Quality", "HDR", "Advanced Scene Mode", "Scene Mode", "Bracket Settings", "Burst Mode",
               "Sequence Number", "Sub Sec Time Original"]
    keysMP4 = ["Image Quality", "HDR", "Advanced Scene Mode", "Scene Mode", "Video Frame Rate"]

    if not Tagdict: return
    if has_not_keys(Tagdict, keys=keysPrim): return

    if any(fileext == ext for ext in ['.jpg', '.JPG']):
        return has_not_keys(Tagdict, keys=keysJPG)
    elif any(fileext == ext for ext in ['.mp4', '.MP4']):
        return has_not_keys(Tagdict, keys=keysMP4)
    else:
        print("unknown file extension")
        return


def create_model(Tagdict, i: int):
    if not 'Camera Model Name' in Tagdict: return ""
    model = Tagdict['Camera Model Name'][i]
    if model == "DMC_TZ101":
        return DMC_TZ101(Tagdict, i)
    return ModelBase(Tagdict, i)