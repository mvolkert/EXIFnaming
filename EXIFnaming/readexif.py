#!/usr/bin/env python3
"""
Reads Tags to use them, but not write to them
"""

import datetime as dt
import os
import re
from collections import OrderedDict

import numpy as np

import EXIFnaming.helpers.constants as c
from EXIFnaming.helpers.date import giveDatetime, newdate, dateformating, print_firstlast_of_dirname, \
    find_dir_with_closest_time
from EXIFnaming.helpers.decode import read_exiftags, has_not_keys, read_exiftag
from EXIFnaming.helpers.fileop import writeToFile, renameInPlace, changeExtension, moveFiles, renameTemp, move, \
    copyFilesTo, getSavesDir, isfile, get_info_dir, get_filename_sorted_dirfiletuples, get_gps_dir
from EXIFnaming.helpers.measuring_tools import Clock, TimeJumpDetector
from EXIFnaming.helpers.misc import tofloat, getPostfix
from EXIFnaming.helpers.settings import includeSubdirs, image_types, video_types, file_types
from EXIFnaming.helpers.tags import getPath, getSequenceNumber, getMode, getCameraModel, getDate, get_recMode, \
    get_sequence_string, checkIntegrity


def print_info(tagGroupNames=(), allGroups=False, fileext=".JPG"):
    """
    write tag info of tagGroupNames to a file in saves dir
    :param tagGroupNames: selectable groups (look into constants)
    :param allGroups: take all tagGroupNames
    :param fileext: file extension
    """
    inpath = os.getcwd()
    outdict = read_exiftags(inpath, fileext)
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

        dirname = getSavesDir()
        writeToFile(os.path.join(dirname, "tags_" + tagGroupName + ".txt"), outstring)


def rename_pm(Prefix="", dateformat='YYMM-DD', startindex=1, onlyprint=False, postfix_stay=True, name=""):
    """
    rename for JPG and MP4
    """
    rename(Prefix, dateformat, startindex, onlyprint, postfix_stay, ".JPG", name)
    rename(Prefix, dateformat, 1, onlyprint, postfix_stay, ".MP4", name)


def rename(Prefix="", dateformat='YYMM-DD', startindex=1, onlyprint=False,
           postfix_stay=True, fileext=".JPG", fileext_Raw=".Raw", name=""):
    """
    Rename into Format: [Prefix][dateformat](_[name])_[Filenumber][SeriesType][SeriesSubNumber]_[PhotoMode]
    :param Prefix: prefix has to fulfil regex [-a-zA-Z]*
    :param dateformat: Y:Year,M:Month,D:Day,N:DayCounter; Number of occurrences determine number of digits
    :param startindex: minimal counter
    :param onlyprint: do not rename; only output file of proposed renaming into saves directory
    :param postfix_stay: if you put a postfix after PhotoMode with an other program and call this function again, the postfix will be preserved
    :param fileext: file extension
    :param fileext_Raw: file extension for raw image that is to get same name as the normal one
    :param name: optional name between date and filenumber, seldom used
    """
    inpath = os.getcwd()
    Tagdict = read_exiftags(inpath, fileext)

    # check integrity
    easymode = checkIntegrity(Tagdict, fileext)
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
    digits = _count_files_for_each_date(Tagdict, startindex, dateformat)
    number_of_files = len(list(Tagdict.values())[0])
    NamePrefix = ""

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

        if fileext in image_types:
            if easymode:
                counter += 1
            else:
                # SequenceNumber
                SequenceNumber = getSequenceNumber(Tagdict, i)
                if SequenceNumber < 2 and not time == time_old: counter += 1
                if not "HDR" in filename: sequenceString = get_sequence_string(SequenceNumber, Tagdict, i)

            counterString = ("_%0" + digits + "d") % counter

        elif fileext in video_types:
            counter += 1
            counterString = "_M" + "%02d" % counter
            if not easymode:
                newpostfix += get_recMode(Tagdict, i)

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
            print(os.path.join(Tagdict["Directory"][i], newname + postfix),
                  "already exists - counted further up - time:", time, "time_old: ", time_old)
            counter += 1
            newname = NamePrefix + ("_%0" + digits + "d") % counter + sequenceString + newpostfix

        time_old = time
        lastnewname = newname

        newname += filename[filename.rfind("."):]
        Tagdict["File Name new"].append(newname)
        outstring += _write(Tagdict["Directory"][i], filename, temppostfix, newname, onlyprint)
        filename_Raw = changeExtension(filename, fileext_Raw)
        if not fileext_Raw == "" and isfile(Tagdict["Directory"][i], filename_Raw):
            outstring += _write(Tagdict["Directory"][i], filename_Raw, temppostfix,
                                changeExtension(newname, fileext_Raw), onlyprint)

    dirname = getSavesDir()
    timestring = dateformating(dt.datetime.now(), "_MMDDHHmmss")
    np.savez_compressed(os.path.join(dirname, "Tags" + fileext + timestring), Tagdict=Tagdict)
    writeToFile(os.path.join(dirname, "newnames" + fileext + timestring + ".txt"), outstring)


def _write(directory, filename, temppostfix, newname, onlyprint):
    if not onlyprint: renameInPlace(directory, filename + temppostfix, newname)
    return "%-50s\t %-50s\n" % (filename, newname)


def _count_files_for_each_date(Tagdict, startindex, dateformat):
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

    Tagdict = read_exiftags(inpath)
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Date/Time Original"]): return
    timeJumpDetector = TimeJumpDetector()
    time_old = giveDatetime()
    dircounter = 1
    filenames = []
    leng = len(list(Tagdict.values())[0])
    dirNameDict_firsttime = OrderedDict()
    dirNameDict_lasttime = OrderedDict()
    time = giveDatetime(Tagdict["Date/Time Original"][0])
    daystring = dateformating(time, "YYMMDD_")
    dirName = daystring + "%02d" % dircounter
    dirNameDict_firsttime[time] = dirName
    print('Number of JPG: %d' % leng)
    for i in range(leng):
        time = giveDatetime(Tagdict["Date/Time Original"][i])

        if timeJumpDetector.isJump(time, len(filenames)):
            dirNameDict_lasttime[time_old] = dirName
            moveFiles(filenames, os.path.join(inpath, dirName))

            filenames = []
            if newdate(time, time_old):
                daystring = dateformating(time, "YYMMDD_")
                dircounter = 1
            else:
                dircounter += 1
            dirName = daystring + "%02d" % dircounter
            dirNameDict_firsttime[time] = dirName
        filenames.append((Tagdict["Directory"][i], Tagdict["File Name"][i]))
        time_old = time

    dirNameDict_lasttime[time_old] = dirName
    moveFiles(filenames, os.path.join(inpath, dirName))

    print_firstlast_of_dirname(dirNameDict_firsttime, dirNameDict_lasttime)

    Tagdict_mp4 = read_exiftags(inpath, fileext=".MP4")
    if has_not_keys(Tagdict_mp4, keys=["Directory", "File Name", "Date/Time Original"]): return
    leng = len(list(Tagdict_mp4.values())[0])
    print('Number of mp4: %d' % leng)
    for i in range(leng):
        time = giveDatetime(Tagdict_mp4["Date/Time Original"][i])
        dirName = find_dir_with_closest_time(dirNameDict_firsttime, dirNameDict_lasttime, time)

        if dirName:
            move(Tagdict_mp4["File Name"][i], Tagdict_mp4["Directory"][i], os.path.join(inpath, dirName, "mp4"))


def searchby_exiftag_equality(tag_name: str, value: str, fileext=".JPG"):
    """
    searches for files where the value of the exiftag equals the input value
    :param tag_name: exiftag key
    :param value: exiftag value
    :param fileext: file extension
    """
    inpath = os.getcwd()
    Tagdict = read_exiftags(inpath, fileext)
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Date/Time Original", tag_name]): return
    leng = len(list(Tagdict.values())[0])
    files = []
    for i in range(leng):
        if not Tagdict[tag_name][i] == value: continue
        files.append(getPath(Tagdict, i))
    copyFilesTo(files, os.path.join(inpath, "matches"))


def searchby_exiftag_interval(tag_name: str, min_value: float, max_value: float, fileext=".JPG"):
    """
    searches for files where the value of the exiftag is in the specified interval
    :param tag_name: exiftag key
    :param min_value: interval start
    :param max_value: interval end
    :param fileext: file extension
    """
    inpath = os.getcwd()
    Tagdict = read_exiftags(inpath, fileext)
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Date/Time Original", tag_name]): return
    leng = len(list(Tagdict.values())[0])
    files = []
    for i in range(leng):
        value = tofloat(Tagdict[tag_name][i])
        if not (value and min_value < value < max_value): continue
        files.append(getPath(Tagdict, i))
    copyFilesTo(files, os.path.join(inpath, "matches"))


def rotate(subname="HDR", folder=r"HDR\w*", sign=1, override=True, ask=True):
    """
    rotate back according to tag information (Rotate 90 CW or Rotate 270 CW)
    :param subname: only files that contain this name are rotated, empty string: no restriction
    :param sign: direction of rotation
    :param folder: only files in directories that match this regex are rotated, empty string: no restriction
    :param override: override file with rotated one
    :param ask: if should ask for user confirmation
    """

    from PIL import Image

    NFiles = 0
    clock = Clock()
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: continue
        if not folder == "" and not re.search(folder, os.path.basename(dirpath)): continue
        if len(filenames) == 0: continue
        print(dirpath)
        Tagdict = read_exiftags(dirpath, ".jpg", ask=ask)
        if has_not_keys(Tagdict, keys=["Directory", "File Name", "Rotation"]): return
        leng = len(list(Tagdict.values())[0])
        for i in range(leng):
            # Load the original image:
            if not subname in Tagdict["File Name"][i]: continue
            if Tagdict["Rotation"][i] == "Horizontal (normal)":
                continue
            else:
                name = os.path.join(Tagdict["Directory"][i], Tagdict["File Name"][i])
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
    clock.finish()


def exif_to_name():
    """
    reverse exif_to_name()
    """
    inpath = os.getcwd()
    for fileext in file_types:
        Tagdict = read_exiftags(inpath, includeSubdirs, fileext)
        if has_not_keys(Tagdict, keys=["Directory", "File Name", "Label"]): return
        temppostfix = renameTemp(Tagdict["Directory"], Tagdict["File Name"])
        leng = len(list(Tagdict.values())[0])
        for i in range(leng):
            renameInPlace(Tagdict["Directory"][i], Tagdict["File Name"][i] + temppostfix, Tagdict["Label"][i] + fileext)


def print_timetable():
    """
    print the time of the first and last picture in a directory to a file
    """
    inpath = os.getcwd()
    ofile = open(get_info_dir("timetable.txt"), 'a')
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not inpath == dirpath: continue
        for dirname in dirnames:
            if dirname.startswith('.'): continue
            print("Folder: " + dirname)
            fotos = get_filename_sorted_dirfiletuples(image_types, inpath, dirname)
            if not fotos: continue
            first = _get_time(fotos[0])
            last = _get_time(fotos[-1])
            ofile.write("%-55s; %12s; %12s\n" % (dirname, first, last))
    ofile.close()


def _get_time(dirfile: tuple) -> str:
    tags = read_exiftag(dirfile[0], dirfile[1])
    if not "Date/Time Original" in tags: return ""
    time = giveDatetime(tags["Date/Time Original"])
    return time.strftime(_read_timetable.timeformat)


def order_with_timetable(timefile=get_info_dir("timetable.txt"), fileexts=(".JPG", ".MP4")):
    inpath = os.getcwd()
    dirNameDict_firsttime, dirNameDict_lasttime = _read_timetable(timefile)
    for fileext in fileexts:
        Tagdict = read_exiftags(inpath, fileext=fileext)
        if has_not_keys(Tagdict, keys=["Directory", "File Name", "Date/Time Original"]): return
        leng = len(list(Tagdict.values())[0])
        print('Number of jpg: %d' % leng)
        for i in range(leng):
            time = giveDatetime(Tagdict["Date/Time Original"][i])
            dirName = find_dir_with_closest_time(dirNameDict_firsttime, dirNameDict_lasttime, time)

            if dirName:
                move(Tagdict["File Name"][i], Tagdict["Directory"][i], os.path.join(inpath, dirName))


def _read_timetable(filename=get_info_dir("timetable.txt")):
    file = open(filename, 'r')
    dirNameDict_firsttime = OrderedDict()
    dirNameDict_lasttime = OrderedDict()
    for line in file:
        dir_name, start, end = [entry.strip(' ').strip('\r\n') for entry in line.split(';')]
        if not start or not end: continue
        start = dt.datetime.strptime(start, _read_timetable.timeformat)
        end = dt.datetime.strptime(end, _read_timetable.timeformat)
        dirNameDict_firsttime[start] = dir_name
        dirNameDict_lasttime[end] = dir_name
    file.close()
    return dirNameDict_firsttime, dirNameDict_lasttime


_read_timetable.timeformat = "%y%m%d %H:%M"


def better_gpx_via_timetable(gpxfilename="London.gpx"):
    def write(dirName_last, gpxfile_out):
        if dirName != dirName_last:
            if not dirName_last == "": gpxfile_out.write("</trkseg></trk>\r\n")
            gpxfile_out.write("<trk><name>" + dirName + "</name><trkseg>\r\n")
        gpxfile_out.write(line)
    timefile = get_info_dir("timetable.txt")
    gpxfilename = get_gps_dir(gpxfilename)
    dirNameDict_firsttime, dirNameDict_lasttime = _read_timetable(timefile)
    timeregex = re.compile("(.*<time>)([^<]*)(</time>.*)")
    gpxfilename_out, ext = gpxfilename.rsplit('.', 1)
    dirName_last1 = ""
    dirName_last2 = ""
    gpxfile_out1 = open(gpxfilename_out + "_new1." + ext, "w")
    gpxfile_out2 = open(gpxfilename_out + "_new2." + ext, "w")
    with open(gpxfilename, "r") as gpxfile:
        for line in gpxfile:
            match = timeregex.match(line)
            if not match:
                if "</gpx>" in line:
                    gpxfile_out1.write("</trkseg></trk>\r\n")
                    gpxfile_out2.write("</trkseg></trk>\r\n")
                gpxfile_out1.write(line)
                gpxfile_out2.write(line)
                continue
            line = line.replace("wpt", "trkpt")
            time = match.group(2)
            time = dt.datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
            dirName = find_dir_with_closest_time(dirNameDict_firsttime, dirNameDict_lasttime, time, 3600)
            if "unrelated" in dirName:
                write(dirName_last2, gpxfile_out2)
                dirName_last2 = dirName
            else:
                write(dirName_last1, gpxfile_out1)
                dirName_last1 = dirName
    gpxfile_out1.close()
    gpxfile_out2.close()