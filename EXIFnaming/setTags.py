#!/usr/bin/env python3
"""
Writes to Tags
"""

import datetime as dt

from EXIFnaming.helpers.date import giveDatetime, dateformating
from EXIFnaming.helpers.decode import readTags, callExiftool, askToContinue, writeTags, countFilesIn
from EXIFnaming.helpers.measuring_tools import Clock, Dir_change_printer
from EXIFnaming.helpers.tags import *

includeSubdirs = True


def setIncludeSubdirs(toInclude=True):
    global includeSubdirs
    includeSubdirs = toInclude
    print("modifySubdirs:", includeSubdirs)


def adjustDate(hours=0, minutes=0, seconds=0, Fileext=".JPG"):
    """
    for example to adjust time zone by one: hours=-1
    """
    inpath = os.getcwd()
    delta_t = dt.timedelta(hours=hours, minutes=minutes, seconds=seconds)
    Tagdict = readTags(inpath, includeSubdirs, Fileext)
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Date/Time Original"]): return
    leng = len(list(Tagdict.values())[0])
    mp4_additional_time_tags = ["TrackCreateDate", "TrackModifyDate", "MediaCreateDate", "MediaModifyDate",
                                "CreateDate", "ModifyDate"]
    dir_change_printer = Dir_change_printer(Tagdict["Directory"][0])
    for i in range(leng):
        time = giveDatetime(Tagdict["Date/Time Original"][i])
        newtime = time + delta_t
        timestring = dateformating(newtime, "YYYY:MM:DD HH:mm:ss")
        options = ["-DateTimeOriginal=" + timestring]
        if Fileext in (".MP4", ".mp4"):
            for time_tag in mp4_additional_time_tags:
                options.append("-%s=%s" % (time_tag, timestring))
            # TODO:  To print the tag names instead instead of descriptions, use the -s option when extracting information
            # subSec_time = giveDatetime(Tagdict["SubSecDateTimeOriginal"][i])
            # subSec_newtime = subSec_time + delta_t
            # subSec_timestring = dateformating(subSec_newtime, "YYYY:MM:DD HH:mm:ss.SSS")
            # print(subSec_timestring)
            # options.append("-SubSecCreateDate=" + subSec_timestring)
            # options.append("-SubSecDateTimeOriginal=" + subSec_timestring)
            # options.append("-SubSecModifyDate=" + subSec_timestring)

        callExiftool(Tagdict["Directory"][i], Tagdict["File Name"][i], options, True)
        dir_change_printer.update(Tagdict["Directory"][i])
    dir_change_printer.finish()


def addLocation(country="", city="", location=""):
    """
    :param country: example:"Germany"
    :param city: example:"Nueremberg"
    :param location: additional location info
    """
    inpath = os.getcwd()
    options = []
    if country: options.append("-Country=" + country)
    if city: options.append("-City=" + city)
    if location: options.append("-Location=" + location)
    if not options: return
    writeTags(inpath, options, includeSubdirs, ".JPG")


def nameToExif():
    """
    extract title, description and mode from name and write them to exif
    """
    inpath = os.getcwd()
    clock = Clock()
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
                    if subname in c.SceneToTag:
                        if c.SceneToTag[subname]: state += c.SceneToTag[subname] + "_"
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
            callExiftool(dirpath, filename + ext, options, True)
    clock.finish()


def geotag(timezone=2, offset_min=0, offset_sec=0):
    """
    adds gps information to all pictures in all sub directories of current directory
    the gps information is obtained from gpx files, that are expected to be in a folder called ".gps"
    """
    inpath = os.getcwd()
    gpxDir = inpath + r"\.gps"
    options = ["-r", "-geotime<${DateTimeOriginal}%+03d:00" % timezone]
    if not offset_min == 0 or not offset_sec == 0:
        options.append("-geosync=%+03d:%02d" % (offset_min, offset_sec))
    for (dirpath, dirnames, filenames) in os.walk(gpxDir):
        if not gpxDir == dirpath: break
        for filename in filenames:
            if not filename.endswith(".gpx"): continue
            options.append("-geotag")
            options.append(os.path.join(gpxDir, filename))
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not inpath == dirpath: break
        for dirname in dirnames:
            if dirname.startswith("."): continue
            callExiftool(inpath, dirname, options=options)
