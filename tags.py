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

import datetime as dt
from collections import OrderedDict
import itertools as it

from tags_misc import *
from constants import TagNames, SceneToTag
from fileop import *
from decode import readTags, has_not_keys, callExiftool, askToContinue, writeTags, countFilesIn
from date import giveDatetime, newdate, dateformating, searchDirByTime
from cv2op import is_blurry, are_similar

# for reloading
from IPython import get_ipython

get_ipython().magic('reload_ext autoreload')
print('loaded collection of Tag operations')

includeSubdirs = True


def setIncludeSubdirs(toInclude=True):
    global includeSubdirs
    includeSubdirs = toInclude
    print("modifySubdirs:", includeSubdirs)


def printinfo(tagGroupNames=(), Fileext=".JPG"):
    inpath = os.getcwd()
    outdict = readTags(inpath, includeSubdirs, Fileext)
    for tagGroupName in TagNames:
        if not tagGroupNames == [] and not tagGroupName in tagGroupNames: continue
        outstring = ""
        for entry in ["File Name"] + TagNames[tagGroupName]:
            if not entry in outdict: continue
            if len(outdict[entry]) == len(outdict["File Name"]):
                outstring += "%-30s\t" % entry
            else:
                del outdict[entry]
        outstring += "\n"
        for i in range(len(outdict["File Name"])):

            outstring += "%-40s\t" % outdict["File Name"][i]
            for entry in TagNames[tagGroupName]:
                if not entry in outdict: continue
                val = outdict[entry]
                outstring += "%-30s\t" % val[i]
            outstring += "\n"

        dirname = concatPathToSave(inpath)
        writeToFile(dirname + "\\tags_" + tagGroupName + ".txt", outstring)


def rename_PM(Prefix="P", dateformat='YYMM-DD', name="", startindex=1, digits=3, easymode=False, onlyprint=False,
              postfix_stay=True, Fileext=".JPG", Fileext_video=".MP4", Fileext_Raw=".Raw"):
    rename(Prefix, dateformat, name, startindex, digits, easymode, onlyprint, postfix_stay, Fileext,
           Fileext_Raw)
    rename(Prefix, dateformat, name, 1, 2, easymode, onlyprint, postfix_stay, Fileext_video, Fileext_Raw)


def rename(Prefix="P", dateformat='YYMM-DD', name="", startindex=1, digits=3, easymode=False, onlyprint=False,
           postfix_stay=True, Fileext=".JPG", Fileext_Raw=".Raw"):
    inpath = os.getcwd()
    Tagdict = readTags(inpath, includeSubdirs, Fileext, ["HDR"])

    # check integrity
    if len(Tagdict) == 0: return
    keysPrim = ["Directory", "File Name", "Date/Time Original"]
    keysJPG = ["Image Quality", "HDR", "Advanced Scene Mode", "Scene Mode", "Bracket Settings", "Burst Mode",
               "Sequence Number", "Sub Sec Time Original"]
    keysMP4 = ["Image Quality", "HDR", "Advanced Scene Mode", "Scene Mode", "Video Frame Rate"]
    if easymode:
        keysImportant = keysPrim
    elif any(Fileext == ext for ext in ['.jpg', '.JPG']):
        keysImportant = keysPrim + keysJPG
    elif any(Fileext == ext for ext in ['.mp4', '.MP4']):
        keysImportant = keysPrim + keysMP4
    else:
        print("unknown file extension")
        return
    if has_not_keys(Tagdict, keys=keysImportant): return

    # rename temporary
    if not onlyprint:
        temppostfix = renameTemp(Tagdict["Directory"], Tagdict["File Name"])
    else:
        temppostfix = ""

    # initialize
    if name: name = "_" + name
    leng = len(list(Tagdict.values())[0])
    counter = startindex - 1
    digits = str(digits)
    time_old = giveDatetime()
    outstring = ""
    lastnewname = ""
    last_SequenceNumber = 1e4
    Tagdict["File Name new"] = []

    for i in range(leng):
        time = giveDatetime(getDate(Tagdict, i))

        if newdate(time, time_old, 'D' in dateformat or 'N' in dateformat):
            daystring = dateformating(time, dateformat)
            NamePrefix = Prefix + daystring + getCameraModel(Tagdict, i) + name
            if not i == 0: counter = 0

        filename = Tagdict["File Name"][i]
        postfix = getPostfix(filename, postfix_stay)
        counterString = ""
        sequenceString = ""
        newpostfix = ""

        if any(Fileext == ext for ext in ['.jpg', '.JPG']):
            if easymode:
                counter += 1
            else:
                # SequenceNumber
                SequenceNumber = getSequenceNumber(Tagdict, i)
                if last_SequenceNumber >= SequenceNumber and not time == time_old: counter += 1
                if SequenceNumber > 0:
                    last_SequenceNumber = SequenceNumber
                else:
                    last_SequenceNumber = 1e4  # SequenceNumber==0 -> no sequence -> high possible value such that even sequences with deleted first pictures can be registered

                sequenceString = getSequenceString(SequenceNumber, Tagdict, i)

            counterString = ("_%0" + digits + "d") % counter

        elif any(Fileext == ext for ext in ['.mp4', '.MP4']):
            counter += 1
            counterString = "_M" + "%02d" % counter
            if not easymode:
                newpostfix += getRecMode(Tagdict, i)

        if not easymode:
            # Name Scene Modes
            newpostfix += getMode(Tagdict, i)
            if newpostfix in postfix:
                newpostfix = postfix
            else:
                newpostfix += postfix

        newname = NamePrefix + counterString + sequenceString + newpostfix
        if newname == lastnewname: newname = NamePrefix + counterString + sequenceString + "_K" + newpostfix

        if newname in Tagdict["File Name new"]:
            print(
                Tagdict["Directory"][i] + "\\" + newname + postfix, "already exsists - counted further up - time:",
                time,
                "time_old: ", time_old)
            counter += 1
            newname = NamePrefix + ("_%0" + digits + "d") % counter + sequenceString + newpostfix

        time_old = time
        lastnewname = newname

        newname += filename[filename.rfind("."):]
        Tagdict["File Name new"].append(newname)
        outstring += "%-50s\t %-50s\n" % (filename, newname)
        if not onlyprint: renameInPlace(Tagdict["Directory"][i], filename + temppostfix, newname)
        filename_Raw = changeExtension(filename, Fileext_Raw)
        if not Fileext_Raw == "" and os.path.isfile(Tagdict["Directory"][i] + "\\" + filename_Raw):
            newname_Raw = changeExtension(newname, Fileext_Raw)
            outstring += "%-50s\t %-50s\n" % (filename, newname)
            if not onlyprint: renameInPlace(Tagdict["Directory"][i], filename_Raw + temppostfix, newname_Raw)

    dirname = concatPathToSave(inpath)
    timestring = dateformating(dt.datetime.now(), "_MMDDHHmmss")
    np.savez_compressed(dirname + "\\Tags" + Fileext + timestring, Tagdict=Tagdict)
    writeToFile(dirname + "\\newnames" + Fileext + timestring + ".txt", outstring)


def renameBack(Fileext=".JPG"):
    inpath = os.getcwd()
    dirname = concatPathToSave(inpath)
    Tagdict = np.load(dirname + "\\Tags" + Fileext + ".npz")["Tagdict"].item()
    temppostfix = renameTemp(Tagdict["Directory"], Tagdict["File Name"])
    for i in range(len(list(Tagdict.values())[0])):
        filename = Tagdict["File Name new"][i]
        if not os.path.isfile(Tagdict["Directory"][i] + "\\" + filename): continue
        filename_old = Tagdict["File Name"][i]
        renameInPlace(Tagdict["Directory"][i], filename + temppostfix, filename_old)
        Tagdict["File Name new"][i], Tagdict["File Name"][i] = Tagdict["File Name"][i], Tagdict["File Name new"][i]


def order(outpath=None):
    inpath = os.getcwd()
    if outpath is None:
        outpath = inpath
    else:
        outpath = concatPathToStandard(outpath)
    if not os.path.isdir(outpath): return

    Tagdict = readTags(inpath, includeSubdirs)
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Date/Time Original"]): return
    lowJump = 1200.
    bigJump = 3600.
    time_old = giveDatetime()
    dircounter = 1
    daystring = dateformating(giveDatetime(Tagdict["Date/Time Original"][0]), "YYMMDD_")
    filenames = []
    filenames_S = []
    leng = len(list(Tagdict.values())[0])
    dirNameDict_firsttime = OrderedDict()
    dirNameDict_lasttime = OrderedDict()
    print('Number of JPG: %d' % leng)
    for i in range(leng):
        time = giveDatetime(Tagdict["Date/Time Original"][i])
        timedelta = time - time_old
        timedelta_seconds = timedelta.days * 3600 * 24 + timedelta.seconds

        if i > 0 and (timedelta_seconds > bigJump or (
                timedelta_seconds > lowJump and len(filenames) + len(filenames_S) > 100) or newdate(time, time_old)):
            dirNameDict_lasttime[time_old] = daystring + "%02d" % dircounter
            moveFiles(filenames, outpath + "\\" + daystring + "%02d" % dircounter)
            moveFiles(filenames_S, outpath + "\\" + daystring + "%02d_S" % dircounter)

            filenames = []
            filenames_S = []
            if newdate(time, time_old):
                daystring = dateformating(time, "YYMMDD_")
                dircounter = 1
            else:
                dircounter += 1
            dirNameDict_firsttime[time] = daystring + "%02d" % dircounter
        if Tagdict["Burst Mode"][i] == "On":
            filenames_S.append((Tagdict["Directory"][i], Tagdict["File Name"][i]))
        else:
            filenames.append((Tagdict["Directory"][i], Tagdict["File Name"][i]))

        time_old = time

    dirNameDict_lasttime[time_old] = daystring + "%02d" % dircounter
    moveFiles(filenames, outpath + "\\" + daystring + "%02d" % dircounter)
    moveFiles(filenames_S, outpath + "\\" + daystring + "%02d_S" % dircounter)

    Tagdict_mp4 = readTags(inpath, includeSubdirs, Fileext=".MP4")
    if has_not_keys(Tagdict_mp4, keys=["Directory", "File Name", "Date/Time Original"]): return
    leng = len(list(Tagdict_mp4.values())[0])
    print('Number of mp4: %d' % leng)
    for i in range(leng):
        time = giveDatetime(Tagdict_mp4["Date/Time Original"][i])
        dirName = searchDirByTime(dirNameDict_lasttime, time, bigJump)
        if not dirName:
            dirName = searchDirByTime(dirNameDict_firsttime, time, bigJump)

        if dirName:
            move(Tagdict_mp4["File Name"][i], Tagdict_mp4["Directory"][i], outpath + "\\" + dirName + "_mp4")


def detect3D():
    """
    not yet fully implemented
    """
    inpath = os.getcwd()
    Tagdict = readTags(inpath, includeSubdirs)
    if has_not_keys(Tagdict,
                    keys=["Directory", "File Name", "Date/Time Original", "Burst Mode", "Sequence Number"]): return
    time_old = giveDatetime()
    filenames = []
    dir3D = "\\3D"
    for i in range(len(list(Tagdict.values())[0])):
        newDir = Tagdict["Directory"][i] + dir3D
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


def detectSunsetLig():
    inpath = os.getcwd()
    Tagdict = readTags(inpath, includeSubdirs)
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Scene Mode"]): return
    for i in range(len(list(Tagdict.values())[0])):
        newDir = Tagdict["Directory"][i] + "\\Sunset"
        os.makedirs(newDir, exist_ok=True)
        time = giveDatetime(getDate(Tagdict, i))
        if 23 < time.hour or time.hour < 17: continue
        if not is_sun(Tagdict, i): continue
        filename = getPath(Tagdict, i)
        if os.path.isfile(filename.replace(Tagdict["Directory"][i], newDir)): continue
        shutil.copy2(filename, newDir)
        # evening and Sun1 or Sun2 are used


def detectBlurry():
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: continue
        print(dirpath, len(dirnames), len(filenames))
        for filename in filenames:
            if not ".JPG" in filename: continue
            if not is_blurry(dirpath + "\\" + filename, 30): continue
            moveToSubpath(filename, dirpath, "blurry")


def detectSimilar():
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: continue
        print(dirpath, len(dirnames), len(filenames))
        dircounter = 0
        filenames = [filename for filename in filenames if ".JPG" in filename]
        for filenameA, filenameB in it.combinations(filenames, 2):
            print(filenameA, filenameB)
            if not are_similar(dirpath + "\\" + filenameA, dirpath + "\\" + filenameB, 0.9): continue
            dircounter += 1
            moveToSubpath(filenameA, dirpath, "%2d" % dircounter)
            moveToSubpath(filenameB, dirpath, "%2d" % dircounter)


def filterSeries():
    '''
    '''
    inpath = os.getcwd()
    skipdirs = ["B" + str(i) for i in range(1, 8)] + ["S", "single", "HDR", ".git", "tags"]

    print(inpath)
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: continue
        if os.path.basename(dirpath) in skipdirs: continue
        print(dirpath, len(dirnames), len(filenames))
        moveBracketSeries(dirpath, filenames)
        moveSeries(dirpath, filenames)
        for filename in filenames:
            if not ".JPG" in filename: continue
            moveToSubpath(filename, dirpath, "single")
    return


def filterSeries_back():
    inpath = os.getcwd()
    reverseDirs = ["B" + str(i) for i in range(1, 8)] + ["S", "single", "blurry"]

    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not os.path.basename(dirpath) in reverseDirs: continue
        print(dirpath, len(dirnames), len(filenames))
        for filename in filenames:
            if not ".JPG" in filename: continue
            move(filename, dirpath, os.path.dirname(dirpath))
        removeIfEmtpy(dirpath)


def renameHDR(mode="HDRT", ext=".jpg", folder="HDR"):
    import re

    matchreg = r"^([-\w]+)_([0-9]+)B1([-\w\s'&]*)_2\3"
    matchreg2 = r"^([-a-zA-Z0-9]+)[-a-zA-Z_]*_([0-9]+)([-\w\s'&]*)_([0-9]+)\3"
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        print("Folder: " + dirpath)
        if not includeSubdirs and not inpath == dirpath: continue
        if not folder == "" and not folder == dirpath.split("\\")[-1]: continue
        print("Folder: " + dirpath)
        for filename in filenames:
            if mode in filename: continue
            match = re.search(matchreg, filename)
            if not match:
                print("use reg2:", filename)
                match = re.search(matchreg2, filename)
            if match:
                filename_new = match.group(1) + "_" + match.group(2) + "_" + mode + match.group(3) + ext
                if os.path.isfile(dirpath + "\\" + filename_new):
                    i = 2
                    while os.path.isfile(dirpath + "\\" + filename_new):
                        filename_new = match.group(1) + "_" + match.group(2) + "_" + mode
                        filename_new += "%d" % i + match.group(3) + ext
                        i += 1
                        # print(filename_new)
                renameInPlace(dirpath, filename, filename_new)
            else:
                print("no match:", filename)


def rotate(mode="HDRT", sign=1, folder="HDR", override=True):
    """
    Rotation: Rotate 90 CW or Rotate 270 CW
    Rotate back
    """

    from PIL import Image

    NFiles = 0
    timebegin = dt.datetime.now()
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: continue
        if not folder == "" and not folder == dirpath.split("\\")[-1]: continue
        print(dirpath)
        Tagdict = readTags(dirpath, includeSubdirs)
        if has_not_keys(Tagdict, keys=["Directory", "File Name", "Rotation"]): return
        leng = len(list(Tagdict.values())[0])
        for i in range(leng):
            # Load the original image:
            if not mode in Tagdict["File Name"][i]: continue
            if Tagdict["Rotation"][i] == "Horizontal (normal)":
                continue
            else:
                name = Tagdict["Directory"][i] + "\\" + Tagdict["File Name"][i]
                print(Tagdict["File Name"][i])
                img = Image.open(name)
                if Tagdict["Rotation"][i] == "Rotate 90 CW":
                    img_rot = img.rotate(90 * sign, expand=True)
                elif Tagdict["Rotation"][i] == "Rotate 270 CW":
                    img_rot = img.rotate(-90 * sign, expand=True)
                else:
                    continue
                NFiles += 1
                if not override: name = name[:name.rfind(".")] + "_rot" + name[name.rfind("."):]
                img_rot.save(name, 'JPEG', quality=99, exif=img.info['exif'])

    timedelta = dt.datetime.now() - timebegin
    print("rotated %3d files in %2d min, %2d sec" % (NFiles, int(timedelta.seconds / 60), timedelta.seconds % 60))


def adjustDate(hours=-1, minutes=0, seconds=0, Fileext=".JPG"):
    inpath = os.getcwd()
    delta_t = dt.timedelta(hours=hours, minutes=minutes, seconds=seconds)
    Tagdict = readTags(inpath, includeSubdirs, Fileext)
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Date/Time Original"]): return
    leng = len(list(Tagdict.values())[0])
    for i in range(leng):
        time = giveDatetime(Tagdict["Date/Time Original"][i])
        newtime = time + delta_t
        timestring = dateformating(newtime, "YYYY:MM:DD HH:mm:ss")
        callExiftool(getPath(Tagdict, i), ["-DateTimeOriginal=" + timestring], True)


def addLocation(country="", city="", location=""):
    """
    country="Germany", city="Nueremberg", location="Location"
    """
    inpath = os.getcwd()
    options = []
    if country: options.append("-Country=" + country)
    if city: options.append("-City=" + city)
    if location: options.append("-Location=" + location)
    if not options: return
    writeTags(inpath, options, includeSubdirs, ".JPG")


def nameToExif():
    inpath = os.getcwd()
    timebegin = dt.datetime.now()
    print("process", countFilesIn(inpath, includeSubdirs, ""), "Files in ", inpath, "subdir:", includeSubdirs)
    askToContinue()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: break
        print(dirpath)
        for filename in filenames:
            filename, ext = filename.rsplit(".", 1)
            ext = "." + ext
            if ext not in [".JPG", ".jpg", ".MP4", ".mp4"]: continue
            filename_splited = filename.split('_')
            if len(filename_splited) == 0: continue
            id = ''
            title = ''
            state = ''
            found = False
            for subname in filename_splited:
                if found:
                    if subname in SceneToTag:
                        if SceneToTag[subname]: state += SceneToTag[subname] + "_"
                    else:
                        title += subname + "_"
                else:
                    id += subname + "_"
                    if (np.chararray.isdigit(subname[0]) and np.chararray.isdigit(subname[-1])) or \
                            subname[0] == "M" or "HDR" in subname: found = True
            options = []
            if id: options.append("-ImageDescription=" + id[:-1])
            if title: options.append("-Title=" + title[:-1])
            if state: options.append("-State=" + state[:-1])
            if not options: continue
            callExiftool(dirpath + "\\" + filename + ext, options, True)
    timedelta = dt.datetime.now() - timebegin
    print("elapsed time: %2d min, %2d sec" % (int(timedelta.seconds / 60), timedelta.seconds % 60))


def searchFileByTagEquality(TagName, Value, Fileext=".JPG"):
    """
    """
    inpath = os.getcwd()
    Tagdict = readTags(inpath, includeSubdirs, Fileext)
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Date/Time Original", TagName]): return
    leng = len(list(Tagdict.values())[0])
    files = []
    for i in range(leng):
        if not Tagdict[TagName][i] == Value: continue
        files.append(getPath(Tagdict, i))
    copyFilesTo(files, inpath + "\\matches")


def searchFileByTagInterval(TagName, min, max, Fileext=".JPG"):
    """
    """
    inpath = os.getcwd()
    Tagdict = readTags(inpath, includeSubdirs, Fileext)
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Date/Time Original", TagName]): return
    leng = len(list(Tagdict.values())[0])
    files = []
    for i in range(leng):
        value = _float(Tagdict[TagName][i])
        if not (value and min < value < max): continue
        files.append(getPath(Tagdict, i))
    copyFilesTo(files, inpath + "\\matches")


def _float(string):
    import re

    if string.isdigit(): return float(string)

    matchreg = r"^([0-9]+)[.]([0-9]+)"
    match = re.match(matchreg, string)
    if match:
        return float(match.group(0))

    matchreg = r"^([0-9]+)[/]([0-9]+)"
    match = re.match(matchreg, string)
    if match:
        print(match)
        nominator = float(match.group(1))
        denominator = float(match.group(2))
        return nominator / denominator
