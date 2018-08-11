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
    time_tags = ["DateTimeOriginal", "CreateDate", "ModifyDate"]
    time_tags_pm4 = ["TrackCreateDate", "TrackModifyDate", "MediaCreateDate", "MediaModifyDate"]
    # time_tags_mp4_subsec = ["SubSecCreateDate","SubSecDateTimeOriginal", "SubSecModifyDate"]
    dir_change_printer = Dir_change_printer(Tagdict["Directory"][0])
    for i in range(leng):
        time = giveDatetime(Tagdict["Date/Time Original"][i])
        newtime = time + delta_t
        timestring = dateformating(newtime, "YYYY:MM:DD HH:mm:ss")
        options = []
        for time_tag in time_tags:
            options.append("-%s=%s" % (time_tag, timestring))
        if Fileext in (".MP4", ".mp4"):
            for time_tag in time_tags_pm4:
                options.append("-%s=%s" % (time_tag, timestring))
            # not working:
            # if "Sub Sec Time Original" in Tagdict:
            #     subsec = Tagdict["Sub Sec Time Original"][i]
            #     print(subsec)
            #     for time_tag in time_tags_mp4_subsec:
            #         options.append("-%s=%s.%s" % (time_tag, timestring, subsec))
        callExiftool(Tagdict["Directory"][i], Tagdict["File Name"][i], options, True)
        dir_change_printer.update(Tagdict["Directory"][i])
    dir_change_printer.finish()


def fake_date(start='2000:01:01'):
    '''
    each file in a directory is one second later
    each dir is one day later
    :param start:
    :return:
    '''
    inpath = os.getcwd()
    start += ' 00:00:00.000'
    start_time = giveDatetime(start)
    dir_counter = -1
    extensions = ['.jpg', '.JPG']
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: break
        filenames = [filename for filename in filenames if filename[-4:] in extensions]
        if not filenames: continue
        print(dirpath)
        dir_counter += 1
        time = start_time + dt.timedelta(days=dir_counter)
        for filename in filenames:
            time += dt.timedelta(seconds=1)
            time_string = dateformating(time, "YYYY:MM:DD HH:mm:ss")
            options = ["-DateTimeOriginal=" + time_string]
            callExiftool(dirpath, filename, options, True)


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


def name_to_exif(artist="Marco Volkert", additional_tags=[], startdir=None):
    """
    extract title, description and mode from name and write them to exif
    """
    inpath = os.getcwd()
    clock = Clock()
    print("process", countFilesIn(inpath, includeSubdirs, ""), "Files in ", inpath, "subdir:", includeSubdirs)
    askToContinue()
    file_extensions = ["JPG", "jpg", "MP4", "mp4"]
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: break
        print(dirpath)
        for filename in filenames:
            name, ext = filename.rsplit(".", 1)
            if ext not in file_extensions: continue
            if startdir:
                image_id, image_tags = _fullname_to_tag(dirpath, name, startdir)
            else:
                image_id, image_tags = _split_name(name)
            image_tags += additional_tags
            options = ["-Title=" + name, "-Label=" + name]
            if image_id: options.append("-Identifier=" + image_id)
            for image_tag in image_tags:
                options.append("-Keywords=" + image_tag)
            if artist: options.append("-Artist=" + artist)
            callExiftool(dirpath, filename, options, True)
    clock.finish()


def _split_name(filename: str):
    def is_lastpart_of_id(subname: str) -> bool:
        starts_and_ends_with_digit = (np.chararray.isdigit(subname[0]) and np.chararray.isdigit(subname[-1]))
        return starts_and_ends_with_digit or subname[0] == "M" or "HDR" in subname

    filename_splited = filename.split('_')
    if len(filename_splited) == 0: return
    image_id = ""
    image_tags = []
    counter_complete = False
    for subname in filename_splited:
        if counter_complete:
            image_tags.append(subname)
            if subname.isupper():
                image_id += subname + "_"
                image_tag = scene_to_tag(subname)
                if image_tag: image_tags.append(image_tag)
        else:
            image_id += subname + "_"
            if is_lastpart_of_id(subname): counter_complete = True
    image_id = image_id[:-1]
    return image_id, image_tags


def _fullname_to_tag(dirpath: str, filename: str, startdir=""):
    relpath = os.path.relpath(dirpath, startdir)
    if relpath == ".": relpath = ""
    dirpath_split = relpath.split(os.sep)
    filename_prim = filename.split("_")[0]
    image_id = filename
    image_tags = dirpath_split + [filename_prim]
    return image_id, image_tags


def geotag(timezone=2, offset=""):
    """
    adds gps information to all pictures in all sub directories of current directory
    the gps information is obtained from gpx files, that are expected to be in a folder called ".gps"
    :param timezone: number of hours offset
    :param offset: offset in minutes and seconds, has to be in format +/-mm:ss e.g. -03:02
    """
    inpath = os.getcwd()
    gpxDir = inpath + r"\.gps"
    options = ["-r", "-geotime<${DateTimeOriginal}%+03d:00" % timezone]
    if offset:
        options.append("-geosync=" + offset)
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
            print(dirname)
            callExiftool(inpath, dirname, options=options)
