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
    return not Tagdict["Bracket Settings"][i] == "No Bracket"
def is_stopmotion(Tagdict,i):
    return Tagdict["Timer Recording"][i] == "Stop-motion Animation"
def is_timelapse(Tagdict,i):
    return  Tagdict["Timer Recording"][i] == "Time Lapse"
def is_4K(Tagdict,i):
    return Tagdict["Image Quality"][i] == '8.2'
def is_creative(Tagdict,i):
    return Tagdict["Scene Mode"][i] == "Creative Control" or Tagdict["Scene Mode"][i] == "Digital Filter"
def is_scene(Tagdict,i):
    return not Tagdict["Scene Mode"][i] == "Off" and Tagdict["Advanced Scene Mode"][i] in SceneShort
def is_HDR(Tagdict,i):
    return not Tagdict["HDR"][i] == "Off"
def is_sun(Tagdict,i):
    return Tagdict["Scene Mode"][i] == "Sun1" or Tagdict["Scene Mode"][i] == "Sun2"

def getSequenceString(SequenceNumber,Tagdict,i):
    if is_Bracket(Tagdict,i): return "B%d" % SequenceNumber
    if is_series(Tagdict,i):  return "S%02d" % SequenceNumber
    if is_stopmotion(Tagdict,i): return "SM%03d" % SequenceNumber
    if is_timelapse(Tagdict,i): return "TL%03d" % SequenceNumber
    if is_4K(Tagdict,i): return "4KBSF"
    return ""

def getMode(Tagdict,i):
    if is_scene(Tagdict,i):
        return "_" + SceneShort[Tagdict["Advanced Scene Mode"][i]]
    elif is_creative(Tagdict,i):
        return "_" + KreativeShort[Tagdict["Advanced Scene Mode"][i]]
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
    sequence_str = Tagdict["Sequence Number"][i]
    if np.chararray.isdigit(sequence_str): return int(sequence_str)
    return 0


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

def changeExtension(filename,ext):
    return filename[:filename.rfind(".")] + ext