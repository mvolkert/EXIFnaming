import datetime as dt
from collections import OrderedDict
import shutil

from misc import tofloat, getPostfix
from tags import *
from constants import TagNames
from fileop import writeToFile, renameInPlace, changeExtension, moveFiles, renameTemp, move, copyFilesTo
from decode import readTags, has_not_keys
from date import giveDatetime, newdate, dateformating, searchDirByTime

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
