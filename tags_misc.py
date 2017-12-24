#!/usr/bin/env python3

"""
collection of Tag tools
"""

__author__ = "Marco Volkert"
__copyright__ = "Copyright 2017, Marco Volkert"
__email__ = "marco.volkert24@gmx.de"
__status__ = "Development"

import sys
import subprocess
import os
from collections import OrderedDict
import datetime as dt
import operator
import numpy as np

from constants import unknownTags,standardDir,savesDir


def getRecMode(filename="", Advanced_Scene_Mode="", Image_Quality="", Video_Frame_Rate=""):
    if any(ext in filename for ext in ['.mp4', '.MP4']):
        # print(Advanced_Scene_Mode,Image_Quality)
        if Image_Quality == "4k Movie" and Video_Frame_Rate == "29.97":
            return "4KB"
        elif Image_Quality == "4k Movie":
            return "4K"
        elif Image_Quality == "Full HD Movie" and Advanced_Scene_Mode == "HS":
            return "HS"
        elif Image_Quality == "Full HD Movie" and Advanced_Scene_Mode == "Off":
            return "FHD"
        else:
            return ""
    else:
        return ""


def giveDatetime(datestring="2000:01:01 00:00:00.000"):
    args = []
    for sub1 in datestring.split():
        for sub2 in sub1.split(":"):
            if "." in sub2:
                args.append(int(sub2.split(".")[0]))
                args.append(int(sub2.split(".")[1]) * 1000)
            else:
                args.append(int(sub2))
    time = dt.datetime(*args)
    return time


def newdate(time, time_old, use_day=True):
    # adjust datebreak at midnight
    timedelta = time - time_old
    timedelta_seconds = timedelta.days * 3600 * 24 + timedelta.seconds
    if not time_old.year == time.year or not time_old.month == time.month or (
            use_day and not time_old.day == time.day): newdate.dateswitch = True
    if timedelta_seconds > 3600. * 4 and newdate.dateswitch:
        newdate.dateswitch = False
        return True
    else:
        return False


newdate.dateswitch = False


def dateformating(time, dateformat):
    if dateformat.count('Y') > 4:
        yfirst = 0
    else:
        yfirst = 4 - dateformat.count('Y')
    y = dateformat.count('Y')
    m = dateformat.count('M')
    d = dateformat.count('D')
    n = dateformat.count('N')
    h = dateformat.count('H')
    min = dateformat.count('m')
    sec = dateformat.count('s')
    daystring = dateformat
    if y > 0: daystring = daystring.replace('Y' * y, str(time.year)[yfirst:])
    if m > 0: daystring = daystring.replace('M' * m, ("%0" + str(m) + "d") % time.month)
    if d > 0: daystring = daystring.replace('D' * d, ("%0" + str(d) + "d") % time.day)
    if n > 0:
        dateformating.numberofDates += 1
        daystring = daystring.replace('N' * n, ("%0" + str(n) + "d") % dateformating.numberofDates)
    if h > 0: daystring = daystring.replace('H' * h, ("%0" + str(h) + "d") % time.hour)
    if min > 0: daystring = daystring.replace('m' * min, ("%0" + str(min) + "d") % time.minute)
    if sec > 0: daystring = daystring.replace('s' * sec, ("%0" + str(sec) + "d") % time.second)
    return daystring


dateformating.numberofDates = 0


def renameTemp(DirectoryList, FileNameList):
    if not len(DirectoryList) == len(FileNameList):
        print("error in renameTemp: len(DirectoryList)!=len(FileNameList)")
        return ""
    temppostfix = "temp"
    for i in range(len(FileNameList)):
        os.rename(DirectoryList[i] + "\\" + FileNameList[i], DirectoryList[i] + "\\" + FileNameList[i] + temppostfix)
    return temppostfix


def renameEveryTemp(inpath):
    temppostfix = "temp"
    if not os.path.isdir(inpath):
        print('not found directory: ' + inpath)
        return
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        for filename in filenames:
            os.rename(dirpath + "\\" + filename, dirpath + "\\" + filename + temppostfix)
    return temppostfix


def sortDict(indict: OrderedDict, keys: list):
    """example:
    sort indict by keys
    indict={"foo": [1, 3, 2], "bar": [8, 7, 6]}
    keys=["foo"]
    """

    indictkeys = list(indict.keys())
    cols = [indictkeys.index(key) for key in keys]
    lists = []
    for i in range(len(list(indict.values())[0])):
        vals = []
        for key in indictkeys:
            try:
                vals.append(indict[key][i])
            except:
                print("sortDict_badkey", key)
        lists.append(vals)

    for col in reversed(cols):
        lists = sorted(lists, key=operator.itemgetter(col))
    outdict = dict()
    for key in indict:
        outdict[key] = []
    for vals in lists:
        for i, val in enumerate(vals):
            outdict[indictkeys[i]].append(val)
    return outdict


def has_not_keys(indict, keys):
    if not keys: return True
    notContains=[]
    for key in keys:
        if not key in indict:
            notContains.append(key)
            print(key + " not in dict")
            return True
    if notContains:         
        print("dictionary of tags doesn't contain ",notContains)
        return True        
    return False


def countFilesIn(inpath, subdir=False, Fileext=".JPG" ):
    NFiles = 0
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        for filename in filenames:
            if not Fileext.lower() == filename.lower()[filename.rfind("."):]: continue
            if not subdir and not inpath == dirpath: continue
            NFiles += 1
    return NFiles

def countFiles(filenames, Fileext=".JPG" ):
    return len([filename for filename in filenames if Fileext.lower() in filename.lower()])

def askToContinue():
    response = input("Do you want to continue ?")
    print(response)
    if 'n' in response:
        sys.exit('aborted')

def readTags(inpath=os.getcwd(), subdir=False, Fileext=".JPG"):
    date_org_name = "Date/Time Original"
    inpath = concatPathToStandard(inpath)

    print("process", countFilesIn(inpath,subdir,Fileext), "Files in ", inpath, "subdir:", subdir)
    askToContinue()

    timebegin = dt.datetime.now()
    ListOfDicts = []
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not subdir and not inpath == dirpath: break
        if countFiles(filenames,Fileext) == 0:
            print("  No matching files in ", dirpath.replace(inpath + "\\", ""))
            continue
        out = callExiftool(dirpath + "\\*" + Fileext, [], False)
        out = out[out.find("ExifTool Version Number"):]
        out_split = out.split("========")
        print("%4d tags extracted in " % len(out_split), dirpath.replace(inpath + "\\", ""))
        for tags in out_split:
            ListOfDicts.append(decodeTags(tags))

    outdict = listsOfDictsToDictOfLists(ListOfDicts)
    outdict = sortDict(outdict, [date_org_name])
    for i in range(len(outdict["Directory"])):
        outdict["Directory"][i].replace("/", "\\")
    timedelta = dt.datetime.now() - timebegin
    print("elapsed time: %2d min, %2d sec" % (int(timedelta.seconds / 60), timedelta.seconds % 60))
    return outdict

def decodeTags(tags):
    date_org_name = "Date/Time Original"
    tagDict = OrderedDict()
    for tag in tags.split("\\r\\n"):
        keyval = tag.split(": ")
        if not len(keyval) == 2: continue
        key = keyval[0].strip()
        val = keyval[1].strip()
        if key in tagDict: continue
        if (key, val) in unknownTags: val = unknownTags[(key, val)]
        tagDict[key] = val
    if not date_org_name in tagDict:
        print("error:", date_org_name, "not in", tagDict)
    return tagDict


def listsOfDictsToDictOfLists(ListOfDicts):
    """

    :type ListOfDicts: list
    """
    essential= ["File Name","Directory","Date/Time Original"]
    if not ListOfDicts or not ListOfDicts[0] or not ListOfDicts[0].keys(): return {}
    if has_not_keys(ListOfDicts[0],essential): return {}

    DictOfLists=OrderedDict()
    for key in ListOfDicts[0]:
        val=ListOfDicts[0][key]
        DictOfLists[key] = [val]

    badkeys=OrderedDict()
    for i,subdict in enumerate(ListOfDicts[1:],start=1):
        for key in subdict:
            if not key in DictOfLists:
                badkeys[key] = i
                DictOfLists[key] = [""]*i
            DictOfLists[key].append(subdict[key])
        for key in DictOfLists:
            if not key in subdict:
                if not key in badkeys: badkeys[key]=0
                badkeys[key] += 1
                DictOfLists[key].append("")

    if badkeys:
        for key in essential:
            if key in badkeys:
                raise AssertionError(key + ' is essential but not in one of the files')
        print("Following keys did not occur in every file. Number of not occurrences is listed in following dictionary:", badkeys)
        askToContinue()

    return DictOfLists


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


def moveFiles(filenames: str, path: str):
    if os.path.isdir(path):
        print("directory already exists: ", path)
        return
    if len(filenames) == 0: return
    os.makedirs(path)
    for filename in filenames:
        os.rename(filename[0] + "\\" + filename[1], path + "\\" + filename[1])


def moveFilesToSubpath(filenames, dirpath, subpath):
    if len(filenames) == 0: return
    os.makedirs(dirpath + "\\" + subpath, exist_ok=True)
    for filename in filenames:
        os.rename(dirpath + "\\" + filename, dirpath + "\\" + subpath + "\\" + filename)


def moveToSubpath(filename, dirpath, subpath):
    os.makedirs(dirpath + "\\" + subpath, exist_ok=True)
    os.rename(dirpath + "\\" + filename, dirpath + "\\" + subpath + "\\" + filename)


def move(filename, oldpath, newpath):
    os.makedirs(newpath, exist_ok=True)
    os.rename(oldpath + "\\" + filename, newpath + "\\" + filename)


def renameInPlace(dirpath, oldFilename, newFilename):
    os.rename(dirpath + "\\" + oldFilename, dirpath + "\\" + newFilename)


def searchDirByTime(dirDict, time, jump):
    timedelta = dt.timedelta(seconds=jump)
    for lasttime in list(dirDict.keys()):
        timedelta_new = time - lasttime
        timedelta_new_sec = timedelta_new.days * 3600 * 24 + timedelta_new.seconds
        if timedelta_new_sec < timedelta.seconds:
            return dirDict[lasttime]
    return None


def callExiftool(name, options=[], override=True):
    args = ["exiftool", name] + options
    if override: args.append("-overwrite_original_in_place")
    proc = subprocess.Popen(args, stdout=subprocess.PIPE)  # , shell=True
    (out, err) = proc.communicate()
    return str(out)


def concatPathToStandard(path):
    if ":\\" not in path: path = standardDir + path
    if not os.path.isdir(path):
        print(path, "is not a valid path")
        return None
    print(path)
    return path


def concatPathToSave(path):
    path = savesDir + os.path.basename(path)
    os.makedirs(path, exist_ok=True)
    return path

def writeToFile(path,content):
    ofile = open(path, 'a')
    ofile.write(content)
    ofile.close()

def removeIfEmtpy(dirpath):
    if not os.listdir(dirpath): os.rmdir(dirpath)