#!/usr/bin/env python3
"""
Writes to Tags
"""
import csv
import datetime as dt

from EXIFnaming.helpers.date import giveDatetime, dateformating
from EXIFnaming.helpers.decode import read_exiftags, call_exiftool, askToContinue, write_exiftags, count_files_in, \
    write_exiftag
from EXIFnaming.helpers.fileop import filterFiles, get_gps_dir, is_invalid_path, get_setexif_dir, get_logger
from EXIFnaming.helpers.measuring_tools import Clock, DirChangePrinter
from EXIFnaming.helpers.settings import includeSubdirs, file_types
from EXIFnaming.helpers.tag_conversion import FileMetaData, Location, add_dict
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
        if is_invalid_path(dirpath): continue
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
        outTagDict = {'Keywords': image_tags, 'Subject': list(image_tags)}
        location = Location(Tagdict, i)
        add_dict(outTagDict, location.to_tag_dict())
        write_exiftag(outTagDict, dirpath, filename)


def name_to_exif(folder=r"", additional_tags=(), startdir=None):
    """
    extract title, description and mode from name and write them to exif
    """
    inpath = os.getcwd()
    clock = Clock()
    print("process", count_files_in(inpath, file_types, ""), "Files in ", inpath, "subdir:", includeSubdirs)
    askToContinue()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, regex=folder): continue
        filenames = filterFiles(filenames, file_types)
        for filename in filenames:
            meta_data = FileMetaData(dirpath, filename)
            if startdir:
                meta_data.import_fullname(startdir)
            else:
                meta_data.import_filename()
            meta_data.update({'tags': additional_tags})
            write_exiftag(meta_data.to_tag_dict(), dirpath, filename)
    clock.finish()


def geotag(timezone=2, offset="", start_folder=""):
    """
    adds gps information to all pictures in all sub directories of current directory
    the gps information is obtained from gpx files, that are expected to be in a folder called ".gps"
    :param timezone: number of hours offset
    :param offset: offset in minutes and seconds, has to be in format +/-mm:ss e.g. -03:02
    :param start_folder: directories before this name will be ignored, does not needs to be a full directory name
    """
    inpath = os.getcwd()
    gpxDir = get_gps_dir()
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
            if dirname < start_folder: continue
            get_logger().info(dirname)
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


def read_csv(csv_filenames=(), folder=r"", start_folder="", csv_folder=get_setexif_dir(), csv_restriction="",
             import_filename=True, import_exif=True, only_when_changed=False):
    """
    csv files are used for setting tags
    the csv files have to be separated by semicolon
    empty values in a column or not present columns are not evaluated
    each '' in the following is a possible column name

    following restrictions to files are possible:
        'directory': checks if value is part of directory
        'name_main': checks if value is the first part of filename
        'first': int counter min
        'last': int counter max
        'name_part': checks if value is part of filename

    :param csv_filenames:
        can be either "*" for all files in directory or a iterable of filenames

        can set follow exif information: ['title', 'tags', 'tags2', 'tags3', 'rating', 'description', 'gps']
            tags are expected to be separated by ', '
            rating is expected to be in interval [0,5]
            gps is expected to be 'lat, long' in decimal notation
        can set Location via ['Country', 'State', 'City', 'Location']

        sets also structured description for image processing like HDR and Panorama
        columns starting with
            'HDR' are evaluated as HDR description
            'TM' are evaluated as HDR Tone Mapping description
            'PANO' are evaluated as Panorama description
    :param csv_folder: location of csv files - standard is the .EXIFnaming/info
    :param csv_restriction: files that do not pass any of the restriction in this file are not modified at all
    :param folder: process only folders matching this regex
    :param start_folder: directories before this name will be ignored, does not needs to be a full directory name
    :param import_filename: whether to extract tags from filename
    :param import_exif: whether to extract tags from exif
    :param only_when_changed: whether to update only when csv entry changes it
    :return:
    """
    inpath = os.getcwd()
    clock = Clock()
    csv.register_dialect('semicolon', delimiter=';', lineterminator='\r\n')

    if csv_filenames == "*":
        csv_filenames = filterFiles(os.listdir(csv_folder), [".csv"])
    elif csv_filenames:
        csv_filenames = [csv_filename + ".csv" for csv_filename in csv_filenames]
    csv_filenames = [os.path.join(csv_folder, csv_filename) for csv_filename in csv_filenames]
    csv_restriction = os.path.join(csv_folder, csv_restriction) + ".csv"

    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, regex=folder, start=start_folder): continue
        for filename in filterFiles(filenames, file_types):
            meta_data = FileMetaData(dirpath, filename)
            if not _passes_restrictor(meta_data, csv_restriction): continue
            if import_filename: meta_data.import_filename()
            if import_exif: meta_data.import_exif()

            for csv_filename in csv_filenames:
                with open(csv_filename, "r") as csvfile:
                    spamreader = csv.DictReader(csvfile, dialect='semicolon')
                    for row in spamreader:
                        meta_data.update(row)

            if not only_when_changed or meta_data.has_changed:
                write_exiftag(meta_data.to_tag_dict(), meta_data.directory, meta_data.filename)

    clock.finish()


def _passes_restrictor(meta_data, csv_restriction):
    if not csv_restriction:
        return True
    with open(csv_restriction, "r") as csvfile:
        spamreader = csv.DictReader(csvfile, dialect='semicolon')
        for row in spamreader:
            if meta_data.passes_restrictions(row):
                return True
    return False
