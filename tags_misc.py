#!/usr/bin/env python3

"""
collection of Tag tools
"""

__author__ = "Marco Volkert"
__copyright__ = "Copyright 2017, Marco Volkert"
__email__ = "marco.volkert24@gmx.de"
__status__ = "Development"

import os
import numpy as np
from fileop import concatPathToSave
from constants import SceneShort, KreativeShort


def getRecMode(filename, Tagdict,i):
    if any(ext in filename for ext in ['.mp4', '.MP4']):
        # print(Advanced_Scene_Mode,Image_Quality)
        if Tagdict["Image Quality"][i] == "4k Movie" and Tagdict["Video Frame Rate"][i] == "29.97":
            return "4KB"
        elif Tagdict["Image Quality"][i] == "4k Movie":
            return "4K"
        elif Tagdict["Image Quality"][i] == "Full HD Movie" and Tagdict["Advanced Scene Mode"][i] == "HS":
            return "HS"
        elif Tagdict["Image Quality"][i] == "Full HD Movie" and Tagdict["Advanced Scene Mode"][i] == "Off":
            return "FHD"
        else:
            return ""
    else:
        return ""


def getSequenceString(SequenceNumber,Tagdict,i):
    is_series = Tagdict["Burst Mode"][i] == "On"
    is_Bracket = not Tagdict["Bracket Settings"][i] == "No Bracket"
    is_stopmotion = Tagdict["Timer Recording"][i] == "Stop-motion Animation"
    is_timelapse = Tagdict["Timer Recording"][i] == "Time Lapse"
    is_4K = Tagdict["Image Quality"][i] == '8.2'

    if is_Bracket: return "B%d" % SequenceNumber
    if is_series:  return "S%02d" % SequenceNumber
    if is_stopmotion: return "SM%03d" % SequenceNumber
    if is_timelapse: return "TL%03d" % SequenceNumber
    if is_4K: return "4KBSF"
    return ""

def getMode(Tagdict,i):
    is_creative = Tagdict["Scene Mode"][i] == "Creative Control" or Tagdict["Scene Mode"][i] == "Digital Filter"
    is_scene = not is_creative and not Tagdict["Scene Mode"][i] == "Off" and Tagdict["Advanced Scene Mode"][
        i] in SceneShort
    is_HDR = not Tagdict["HDR"][i] == "Off"
    if is_scene:
        return "_" + SceneShort[Tagdict["Advanced Scene Mode"][i]]
    elif is_creative:
        return "_" + KreativeShort[Tagdict["Advanced Scene Mode"][i]]
    elif is_HDR:
        return "_HDR"
    return ""



def readTag_fromFile(inpath=os.getcwd(), Fileext=".JPG"):
    """not tested"""
    Tagdict = np.load(concatPathToSave(inpath) + "\\Tags" + Fileext)["Tagdict"].item()
    if os.path.isfile(Tagdict["Directory"][0] + "\\" + Tagdict["File Name"][0]):
        print("load")
    elif os.path.isfile(Tagdict["Directory"][0] + "\\" + Tagdict["File Name new"][0]):
        Tagdict["File Name"] = list(Tagdict["File Name new"])
        Tagdict["File Name new"] = []
        print("switch")
    else:
        print("load again")
    return Tagdict


def getPostfix(filename, postfix_stay=True):
    postfix = ''
    filename = filename[:filename.rfind(".")]
    filename_splited = filename.split('_')
    if postfix_stay and len(filename_splited) > 1:
        found = False
        for subname in filename_splited:
            if found:
                postfix += "_" + subname
            elif np.chararray.isdigit(subname[0]) and np.chararray.isdigit(subname[-1]):
                found = True

    return postfix


def getPath(Tagdict,i):
    if not all([x in Tagdict for x in ["Directory","File Name"]]):
        print("Directory or File Name is not in Tagdict")
        return ""
    return Tagdict["Directory"][i] + "\\" + Tagdict["File Name"][i]