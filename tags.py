#!/usr/bin/env python3

"""
collection of Tag tools
"""

import numpy as np
import constants as c
from decode import has_not_keys

def is_4KBurst(Tagdict,i):
    return Tagdict["Image Quality"][i] == "4k Movie" and Tagdict["Video Frame Rate"][i] == "29.97"
def is_4KFilm(Tagdict,i):
    return Tagdict["Image Quality"][i] == "4k Movie"
def is_HighSpeed(Tagdict,i):
    return Tagdict["Image Quality"][i] == "Full HD Movie" and Tagdict["Advanced Scene Mode"][i] == "HS"
def is_FullHD(Tagdict,i):
    return Tagdict["Image Quality"][i] == "Full HD Movie" and Tagdict["Advanced Scene Mode"][i] == "Off"
def is_series(Tagdict,i):
    return Tagdict["Burst Mode"][i] == "On"
def is_Bracket(Tagdict,i):
    return Tagdict["Bracket Settings"][i] and not Tagdict["Bracket Settings"][i] == "No Bracket"
def is_stopmotion(Tagdict,i):
    return Tagdict["Timer Recording"][i] == "Stop-motion Animation"
def is_timelapse(Tagdict,i):
    return  Tagdict["Timer Recording"][i] == "Time Lapse"
def is_4K(Tagdict,i):
    return Tagdict["Image Quality"][i] == '8.2'
def is_creative(Tagdict,i):
    return Tagdict["Scene Mode"][i] == "Creative Control" or Tagdict["Scene Mode"][i] == "Digital Filter"
def is_scene(Tagdict,i):
    return Tagdict["Scene Mode"][i] and not Tagdict["Scene Mode"][i] == "Off" and Tagdict["Advanced Scene Mode"][i] in c.SceneShort
def is_HDR(Tagdict,i):
    return Tagdict["HDR"][i] and not Tagdict["HDR"][i] == "Off"
def is_sun(Tagdict,i):
    return Tagdict["Scene Mode"][i] == "Sun1" or Tagdict["Scene Mode"][i] == "Sun2"

def getRecMode(Tagdict,i):
    if is_4KBurst(Tagdict,i):
        return "_4KB"
    elif is_4KFilm(Tagdict,i):
        return "_4K"
    elif is_HighSpeed(Tagdict,i):
        return "_HS"
    elif is_FullHD(Tagdict,i):
        return "_FHD"
    else:
        return ""

def getSequenceString(SequenceNumber,Tagdict,i):
    if is_Bracket(Tagdict,i): return "B%d" % SequenceNumber
    if is_series(Tagdict,i):  return "S%02d" % SequenceNumber
    if is_stopmotion(Tagdict,i): return "SM%03d" % SequenceNumber
    if is_timelapse(Tagdict,i): return "TL%03d" % SequenceNumber
    if is_4K(Tagdict,i): return "4KBSF"
    return ""

def getMode(Tagdict,i):
    if is_scene(Tagdict,i):
        return "_" + c.SceneShort[Tagdict["Advanced Scene Mode"][i]]
    elif is_creative(Tagdict,i):
        return "_" + c.KreativeShort[Tagdict["Advanced Scene Mode"][i]]
    elif is_HDR(Tagdict,i):
        return "_HDR"
    return ""

def getDate(Tagdict,i):
    dateTimeString = Tagdict["Date/Time Original"][i]
    if "Sub Sec Time Original" in Tagdict:
        subsec=Tagdict["Sub Sec Time Original"][i]
        if subsec: dateTimeString += "." + subsec
    return dateTimeString

def getSequenceNumber(Tagdict,i):
    """
    sequence starts with 1; 0 means no sequence
    """
    sequence_str = Tagdict["Sequence Number"][i]
    if np.chararray.isdigit(sequence_str): return int(sequence_str)
    return 0

def getCameraModel(Tagdict,i):
    if not 'Camera Model Name' in Tagdict: return ""
    model = Tagdict['Camera Model Name'][i]
    if model in c.CameraModelShort: model = c.CameraModelShort[model]
    if model: model = "_"+model
    return model


def getPath(Tagdict,i):
    if not all([x in Tagdict for x in ["Directory","File Name"]]):
        print("Directory or File Name is not in Tagdict")
        return ""
    return Tagdict["Directory"][i] + "\\" + Tagdict["File Name"][i]


def checkIntegrity(Tagdict, Fileext=".JPG"):
    """
    :return: None if not primary keys, false if not advanced keys
    """
    # check integrity
    if len(Tagdict) == 0: return
    keysPrim = ["Directory", "File Name", "Date/Time Original"]
    keysJPG = ["Image Quality", "HDR", "Advanced Scene Mode", "Scene Mode", "Bracket Settings", "Burst Mode",
               "Sequence Number", "Sub Sec Time Original"]
    keysMP4 = ["Image Quality", "HDR", "Advanced Scene Mode", "Scene Mode", "Video Frame Rate"]

    if has_not_keys(Tagdict, keys=keysPrim): return

    if any(Fileext == ext for ext in ['.jpg', '.JPG']):
        return has_not_keys(Tagdict, keys=keysJPG)
    elif any(Fileext == ext for ext in ['.mp4', '.MP4']):
        return has_not_keys(Tagdict, keys=keysMP4)
    else:
        print("unknown file extension")
        return