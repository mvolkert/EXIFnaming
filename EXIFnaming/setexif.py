#!/usr/bin/env python3
"""
Writes to Tags
"""
import csv
import datetime as dt

from EXIFnaming.helpers.date import giveDatetime, dateformating
from EXIFnaming.helpers.decode import read_exiftags, call_exiftool, askToContinue, write_exiftags, count_files_in, \
    write_exiftag
from EXIFnaming.helpers.fileop import filterFiles
from EXIFnaming.helpers.measuring_tools import Clock, DirChangePrinter
from EXIFnaming.helpers.settings import includeSubdirs, file_types, photographer
from EXIFnaming.helpers.tag_wrappers import FileMetaData
from EXIFnaming.helpers.tags import *


def shift_time(hours=0, minutes=0, seconds=0, fileext=".JPG"):
    """
    for example to adjust time zone by one: hours=-1
    """
    inpath = os.getcwd()
    delta_t = dt.timedelta(hours=hours, minutes=minutes, seconds=seconds)
    Tagdict = read_exiftags(inpath, fileext)
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Date/Time Original"]): return
    leng = len(list(Tagdict.values())[0])
    time_tags = ["DateTimeOriginal", "CreateDate", "ModifyDate"]
    time_tags_mp4 = ["TrackCreateDate", "TrackModifyDate", "MediaCreateDate", "MediaModifyDate"]
    dir_change_printer = DirChangePrinter(Tagdict["Directory"][0])
    for i in range(leng):
        time = giveDatetime(Tagdict["Date/Time Original"][i])
        newtime = time + delta_t
        timestring = dateformating(newtime, "YYYY:MM:DD HH:mm:ss")
        outTagDict = {}
        for time_tag in time_tags:
            outTagDict[time_tag] = timestring
        if fileext in (".MP4", ".mp4"):
            for time_tag in time_tags_mp4:
                outTagDict[time_tag] = timestring
        write_exiftags(outTagDict, Tagdict["Directory"][i], Tagdict["File Name"][i])
        dir_change_printer.update(Tagdict["Directory"][i])
    dir_change_printer.finish()


def fake_date(start='2000:01:01'):
    """
    each file in a directory is one second later
    each dir is one day later
    :param start: the date on which to start generate fake dates
    """
    inpath = os.getcwd()
    start += ' 00:00:00.000'
    start_time = giveDatetime(start)
    dir_counter = -1
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: break
        filenames = filterFiles(filenames, file_types)
        if not filenames: continue
        print(dirpath)
        dir_counter += 1
        time = start_time + dt.timedelta(days=dir_counter)
        for filename in filenames:
            time += dt.timedelta(seconds=1)
            time_string = dateformating(time, "YYYY:MM:DD HH:mm:ss")
            write_exiftag({"DateTimeOriginal": time_string}, dirpath, filename)


def add_location(country="", city="", location=""):
    """
    :param country: example:"Germany"
    :param city: example:"Nueremberg"
    :param location: additional location info
    """
    write_exiftags({"Country": country, "City": city, "Location": location})


def location_to_keywords():
    inpath = os.getcwd()
    print("process", count_files_in(inpath, file_types, ""), "Files in ", inpath, "subdir:", includeSubdirs)
    askToContinue()
    Tagdict = read_exiftags(inpath, ask=False)
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Date/Time Original"]): return
    leng = len(list(Tagdict.values())[0])
    for i in range(leng):
        dirpath = Tagdict["Directory"][i]
        filename = Tagdict["File Name"][i]
        image_tags = Tagdict["Keywords"][i].split(', ')
        outTagDict = {'Keywords': image_tags, 'Subject': image_tags}
        tagnames = ["Country", "City", "Location"]
        for tagname in tagnames:
            if tagname in Tagdict:
                outTagDict[tagname] = Tagdict[tagname][i]
        write_exiftag(outTagDict, dirpath, filename)


def name_to_exif(artist=photographer, additional_tags=(), startdir=None):
    """
    extract title, description and mode from name and write them to exif
    """
    inpath = os.getcwd()
    clock = Clock()
    print("process", count_files_in(inpath, file_types, ""), "Files in ", inpath, "subdir:", includeSubdirs)
    askToContinue()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: break
        filenames = filterFiles(filenames, file_types)
        print(dirpath)
        for filename in filenames:
            name, ext = filename.rsplit(".", 1)
            if startdir:
                image_id, image_tags = _fullname_to_tag(dirpath, name, startdir)
            else:
                image_id, image_tags = _split_name(name)
            image_tags += additional_tags
            outTagDict = {'Title': name, 'Label': name}
            if image_id: outTagDict["Identifier"] = image_id
            outTagDict["Keywords"] = image_tags
            outTagDict["Subject"] = image_tags
            if artist: outTagDict["Artist"] = artist
            write_exiftag(outTagDict, dirpath, filename)
    clock.finish()


def _split_name(filename: str):
    def is_lastpart_of_id(name) -> bool:
        starts_and_ends_with_digit = (np.chararray.isdigit(name[0]) and np.chararray.isdigit(name[-1]))
        return starts_and_ends_with_digit or name[0] == "M" or "HDR" in name

    filename_splited = filename.split('_')
    if len(filename_splited) == 0: return
    image_id = ""
    image_tags = []
    counter_complete = False
    for subname in filename_splited:
        if counter_complete:
            if subname.isupper():
                image_id += subname + "_"
                image_tags.extend(scene_to_tag(subname))
            else:
                image_tags.append(subname)
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
            call_exiftool(inpath, dirname, options=options)


def geotag_single(lat: float, lon: float):
    """
        adds gps information to all pictures in all sub directories of current directory
        :param lat: GPSLatitude
        :param lon: GPSLongitude
        """
    inpath = os.getcwd()
    options = ["-GPSLatitudeRef=%f" % lat, "-GPSLatitude=%f" % lat, "-GPSLongitudeRef=%f" % lon,
               "-GPSLongitude=%f" % lon]
    call_exiftool(inpath, "*", options=options)


def read_csv(main_csv: str, processing_csv =""):
    inpath = os.getcwd()
    clock = Clock()
    fileMetaDataList = [FileMetaData(dirpath, filename) for (dirpath, dirnames, filenames) in os.walk(inpath) for
                        filename in filterFiles(filenames, file_types)]

    csv.register_dialect('semicolon', delimiter=';', lineterminator='\r\n')
    with open(main_csv) as csvfile:
        spamreader = csv.DictReader(csvfile, dialect='semicolon')
        for row in spamreader:
            for fileMetaData in fileMetaDataList:
                fileMetaData.update(row)

    if processing_csv:
        with open(processing_csv) as csvfile:
            spamreader = csv.DictReader(csvfile, dialect='semicolon')
            for row in spamreader:
                for fileMetaData in fileMetaDataList:
                    fileMetaData.update_processing(row)

    for fileMetaData in fileMetaDataList:
        write_exiftag(fileMetaData.toTagDict(), fileMetaData.directory, fileMetaData.filename)

    clock.finish()