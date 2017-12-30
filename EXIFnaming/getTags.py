import datetime as dt
from collections import OrderedDict
import shutil
import os
import numpy as np

from EXIFnaming.helpers.misc import tofloat, getPostfix
from EXIFnaming.helpers.tags import getPath, getSequenceNumber, getMode, getCameraModel, getDate, getRecMode, \
    getSequenceString, checkIntegrity, is_series, is_sun
import EXIFnaming.helpers.constants as c
from EXIFnaming.helpers.fileop import writeToFile, renameInPlace, changeExtension, moveFiles, renameTemp, move, \
    copyFilesTo, concatPathToSave
from EXIFnaming.helpers.decode import readTags, has_not_keys
from EXIFnaming.helpers.date import giveDatetime, newdate, dateformating, searchDirByTime

includeSubdirs = True


def setIncludeSubdirs(toInclude=True):
    global includeSubdirs
    includeSubdirs = toInclude
    print("modifySubdirs:", includeSubdirs)


def printinfo(tagGroupNames=(), allGroups=False, Fileext=".JPG"):
    """
    write tag info of tagGroupNames to a file in saves dir
    :param tagGroupNames: selectable groups (look into constants)
    :param allGroups: take all tagGroupNames
    :param Fileext: file extension
    :return:
    """
    inpath = os.getcwd()
    outdict = readTags(inpath, includeSubdirs, Fileext)
    if allGroups: tagGroupNames = c.TagNames.keys()
    for tagGroupName in c.TagNames:
        if not tagGroupNames == [] and not tagGroupName in tagGroupNames: continue
        outstring = ""
        for entry in ["File Name"] + c.TagNames[tagGroupName]:
            if not entry in outdict: continue
            if len(outdict[entry]) == len(outdict["File Name"]):
                outstring += "%-30s\t" % entry
            else:
                del outdict[entry]
        outstring += "\n"
        for i in range(len(outdict["File Name"])):

            outstring += "%-40s\t" % outdict["File Name"][i]
            for entry in c.TagNames[tagGroupName]:
                if not entry in outdict: continue
                val = outdict[entry]
                outstring += "%-30s\t" % val[i]
            outstring += "\n"

        dirname = concatPathToSave(inpath)
        writeToFile(dirname + "\\tags_" + tagGroupName + ".txt", outstring)


def rename_PM(Prefix="", dateformat='YYMM-DD', startindex=1, onlyprint=False, postfix_stay=True, name=""):
    """
    rename for JPG and MP4
    """
    rename(Prefix, dateformat, startindex, onlyprint, postfix_stay, ".JPG", name)
    rename(Prefix, dateformat, 1, onlyprint, postfix_stay, ".MP4", name)


def rename(Prefix="", dateformat='YYMM-DD', startindex=1, onlyprint=False,
           postfix_stay=True, Fileext=".JPG", Fileext_Raw=".Raw", name=""):
    """
    Rename into Format: [Prefix][dateformat](_[name])_[Filenumber][SeriesType][SeriesSubNumber]_[FotoMode]
    :param Prefix:
    :param dateformat: Y:Year,M:Month,D:Day,N:DayCounter; Number of occurrences determine number of digits
    :param startindex: minimal counter
    :param onlyprint: do not rename; only output file of proposed renaming into saves directory
    :param postfix_stay: if you put a postfix after FotoMode with an other program and call this function again, the postfix will be preserved
    :param Fileext: file extension
    :param Fileext_Raw: file extension for raw image that is to get same name as the normal one
    :param name: optional name between date and filenumber, seldom used
    :return:
    """
    inpath = os.getcwd()
    Tagdict = readTags(inpath, includeSubdirs, Fileext, ["HDR"])

    # check integrity
    easymode = checkIntegrity(Tagdict, Fileext)
    if easymode is None: return

    # rename temporary
    if not onlyprint:
        temppostfix = renameTemp(Tagdict["Directory"], Tagdict["File Name"])
    else:
        temppostfix = ""

    # initialize
    if name: name = "_" + name
    outstring = ""
    lastnewname = ""
    Tagdict["File Name new"] = []
    time_old = giveDatetime()
    counter = startindex - 1
    digits = _countFilesForEachDate(Tagdict, startindex, dateformat)
    number_of_files = len(list(Tagdict.values())[0])

    for i in range(number_of_files):
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
                if SequenceNumber < 2 and not time == time_old: counter += 1
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
                Tagdict["Directory"][i] + "\\" + newname + postfix, "already exists - counted further up - time:",
                time,
                "time_old: ", time_old)
            counter += 1
            newname = NamePrefix + ("_%0" + digits + "d") % counter + sequenceString + newpostfix

        time_old = time
        lastnewname = newname

        newname += filename[filename.rfind("."):]
        Tagdict["File Name new"].append(newname)
        outstring += _write(Tagdict["Directory"][i], filename, temppostfix, newname, onlyprint)
        filename_Raw = changeExtension(filename, Fileext_Raw)
        if not Fileext_Raw == "" and os.path.isfile(Tagdict["Directory"][i] + "\\" + filename_Raw):
            outstring += _write(Tagdict["Directory"][i], filename_Raw, temppostfix,
                                changeExtension(newname, Fileext_Raw), onlyprint)

    dirname = concatPathToSave(inpath)
    timestring = dateformating(dt.datetime.now(), "_MMDDHHmmss")
    np.savez_compressed(dirname + "\\Tags" + Fileext + timestring, Tagdict=Tagdict)
    writeToFile(dirname + "\\newnames" + Fileext + timestring + ".txt", outstring)


def _write(directory, filename, temppostfix, newname, onlyprint):
    if not onlyprint: renameInPlace(directory, filename + temppostfix, newname)
    return "%-50s\t %-50s\n" % (filename, newname)


def _countFilesForEachDate(Tagdict, startindex, dateformat):
    leng = len(list(Tagdict.values())[0])
    counter = startindex - 1
    time_old = giveDatetime()
    maxCounter = 0
    print("number of photos for each date:")
    for i in range(leng):
        time = giveDatetime(getDate(Tagdict, i))
        if not i == 0 and newdate(time, time_old, 'D' in dateformat or 'N' in dateformat):
            print(time_old.date(), counter)
            if maxCounter < counter: maxCounter = counter
            counter = startindex - 1
        if getSequenceNumber(Tagdict, i) < 2: counter += 1
        time_old = time
    print(time_old.date(), counter)
    if maxCounter < counter: maxCounter = counter
    return str(len(str(maxCounter)))


def order():
    inpath = os.getcwd()

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
            moveFiles(filenames, inpath + "\\" + daystring + "%02d" % dircounter)
            moveFiles(filenames_S, inpath + "\\" + daystring + "%02d_S" % dircounter)

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
    moveFiles(filenames, inpath + "\\" + daystring + "%02d" % dircounter)
    moveFiles(filenames_S, inpath + "\\" + daystring + "%02d_S" % dircounter)

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
            move(Tagdict_mp4["File Name"][i], Tagdict_mp4["Directory"][i], inpath + "\\" + dirName + "_mp4")


def _detect3D():
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


def _detectSunset():
    """
    not yet fully implemented
    """
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


def searchByTagEquality(TagName, Value, Fileext=".JPG"):
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


def searchByTagInterval(TagName, min, max, Fileext=".JPG"):
    """
    """
    inpath = os.getcwd()
    Tagdict = readTags(inpath, includeSubdirs, Fileext)
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Date/Time Original", TagName]): return
    leng = len(list(Tagdict.values())[0])
    files = []
    for i in range(leng):
        value = tofloat(Tagdict[TagName][i])
        if not (value and min < value < max): continue
        files.append(getPath(Tagdict, i))
    copyFilesTo(files, inpath + "\\matches")
