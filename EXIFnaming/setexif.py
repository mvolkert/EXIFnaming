#!/usr/bin/env python3
"""
Writes to Tags

dependencies: exiftool
"""
import csv
import datetime as dt
import os

from EXIFnaming.helpers import settings
from EXIFnaming.helpers.date import giveDatetime, dateformating
from EXIFnaming.helpers.decode import read_exiftags, call_exiftool, askToContinue, write_exiftags, count_files_in, \
    write_exiftag, has_not_keys, call_exiftool_direct, read_exiftag
from EXIFnaming.helpers.fileop import filterFiles, is_invalid_path
from EXIFnaming.helpers.measuring_tools import Clock, DirChangePrinter
from EXIFnaming.helpers.program_dir import get_gps_dir, get_setexif_dir, log, log_function_call
from EXIFnaming.helpers.tag_conversion import FileMetaData, Location, add_dict, FilenameAccessor
from EXIFnaming.helpers.tags import create_model, hasDateTime

__all__ = ["shift_time", "fake_date", "add_location", "location_to_keywords", "name_to_exif", "geotag", "geotag_single",
           "read_csv", "copy_exif_via_mainname"]


def shift_time(hours=0, minutes=0, seconds=0, is_video=False):
    """
    for example to adjust time zone by one: hours=-1
    """
    log_function_call(shift_time.__name__, hours, minutes, seconds, is_video)
    inpath = os.getcwd()
    delta_t = dt.timedelta(hours=hours, minutes=minutes, seconds=seconds)
    Tagdict = read_exiftags(inpath, settings.video_types if is_video else settings.image_types)
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Date/Time Original"]): return
    leng = len(list(Tagdict.values())[0])
    time_tags = ["DateTimeOriginal", "CreateDate", "ModifyDate"]
    time_tags_mp4 = ["TrackCreateDate", "TrackModifyDate", "MediaCreateDate", "MediaModifyDate"]
    dir_change_printer = DirChangePrinter(Tagdict["Directory"][0])
    for i in range(leng):
        model = create_model(Tagdict, i)
        time = giveDatetime(model.get_date())
        newtime = time + delta_t
        timestring = dateformating(newtime, "YYYY:MM:DD HH:mm:ss")
        outTagDict = {}
        for time_tag in time_tags:
            outTagDict[time_tag] = timestring
        if is_video:
            for time_tag in time_tags_mp4:
                outTagDict[time_tag] = timestring
        write_exiftags(outTagDict, model.dir, model.filename)
        dir_change_printer.update(model.dir)
    dir_change_printer.finish()


def fake_date(start='2000:01:01'):
    """
    each file in a directory is one second later
    each dir is one day later
    :param start: the date on which to start generate fake dates
    """
    log_function_call(fake_date.__name__, start)
    inpath = os.getcwd()
    start += ' 00:00:00.000'
    start_time = giveDatetime(start)
    dir_counter = -1
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath): continue
        filenames = filterFiles(filenames, settings.image_types + settings.video_types)
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
    deprecated: try to use read_csv() instead
    :param country: example:"Germany"
    :param city: example:"Nueremberg"
    :param location: additional location info
    """
    write_exiftags({"Country": country, "City": city, "Location": location})


def location_to_keywords():
    """
    import location exif information to put into Keywords

    deprecated: try to use read_csv() instead
    """
    inpath = os.getcwd()
    log().info("process %d Files in %s, subdir: %r", count_files_in(inpath, settings.image_types + settings.video_types, ""), inpath,
               settings.includeSubdirs)
    askToContinue()
    Tagdict = read_exiftags(inpath, ask=False)
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

    deprecated: try to use read_csv() instead
    """
    inpath = os.getcwd()
    clock = Clock()
    file_types = settings.image_types + settings.video_types
    log().info("process %d Files in %s, subdir: %r", count_files_in(inpath, file_types, ""), inpath,
               settings.includeSubdirs)
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
    log_function_call(geotag.__name__, offset, start_folder)
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
            log().info(dirname)
            call_exiftool(inpath, dirname, options=options)


def geotag_single(lat: float, lon: float):
    """
    adds gps information to all pictures in all sub directories of current directory
    :param lat: GPSLatitude
    :param lon: GPSLongitude

    deprecated: try to use read_csv() instead
    """
    inpath = os.getcwd()
    options = ["-GPSLatitudeRef=%f" % lat, "-GPSLatitude=%f" % lat, "-GPSLongitudeRef=%f" % lon,
               "-GPSLongitude=%f" % lon]
    call_exiftool(inpath, "*", options=options)


def read_csv(csv_filenames=(), folder=r"", start_folder="", csv_folder: str = None, csv_restriction="",
             import_filename=True, import_exif=True, only_when_changed=False, overwrite_gps=False):
    """
    csv files are used for setting tags
    the csv files have to be separated by semicolon
    empty values in a column or not present columns are not evaluated
    each '' in the following is a possible column name

    can also be used without csv files at all just to import filename to tags

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
    :param overwrite_gps: modifier for import_exif, overwrites gps data with information of csv
    :param only_when_changed: when true filename is not imported to tags for files without matching entries in csv
        useless if csv_restriction is set
    :return:
    """
    if not csv_folder:
        csv_folder = get_setexif_dir()

    log_function_call(read_csv.__name__, csv_filenames, folder, start_folder, csv_folder, csv_restriction,
                      import_filename, import_exif, only_when_changed, overwrite_gps)
    inpath = os.getcwd()
    clock = Clock()
    csv.register_dialect('semicolon', delimiter=';', lineterminator='\r\n')

    if csv_filenames == "*":
        csv_filenames = filterFiles(os.listdir(csv_folder), [".csv"])
    elif csv_filenames:
        csv_filenames = [csv_filename + ".csv" for csv_filename in csv_filenames]
    csv_filenames = [os.path.join(csv_folder, csv_filename) for csv_filename in csv_filenames]
    if csv_restriction:
        csv_restriction = os.path.join(csv_folder, csv_restriction) + ".csv"

    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, regex=folder, start=start_folder): continue
        for filename in filterFiles(filenames, settings.image_types):
            meta_data = FileMetaData(dirpath, filename)
            if not _passes_restrictor(meta_data, csv_restriction): continue
            if import_filename: meta_data.import_filename()
            if import_exif: meta_data.import_exif(overwrite_gps)

            for csv_filename in csv_filenames:
                with open(csv_filename, "r") as csvfile:
                    reader = csv.DictReader(csvfile, dialect='semicolon')
                    for row in reader:
                        meta_data.update(row)

            if not only_when_changed or meta_data.has_changed:
                write_exiftag(meta_data.to_tag_dict(), meta_data.directory, meta_data.filename)

    clock.finish()


def _passes_restrictor(meta_data, csv_restriction):
    if not csv_restriction:
        return True
    with open(csv_restriction, "r") as csvfile:
        reader = csv.DictReader(csvfile, dialect='semicolon')
        for row in reader:
            if meta_data.passes_restrictions(row):
                return True
    return False


def copy_exif_via_mainname(origin: str, target: str, overwriteDateTime=False):
    """
    copy exif information from files in directory origin to target
    files are matched via main name -> processed files can get exif information of original files
    :param overwriteDateTime: whether to overwrite already exiting "Date/Time Original"
    :param origin:
    :param target:
    """
    log_function_call(copy_exif_via_mainname.__name__, origin, target)
    inpath = os.getcwd()
    target_dict = {}
    exclusion_tags = ["--PreviewImage", "--ThumbnailImage", "--Rating"]
    command = "-TagsFromFile"
    for (dirpath, dirnames, filenames) in os.walk(os.path.join(inpath, target)):
        if is_invalid_path(dirpath): continue
        filenames = filterFiles(filenames, settings.image_types)
        for filename in filenames:
            if not overwriteDateTime:
                tagDict = read_exiftag(dirpath, filename)
                if hasDateTime(tagDict): continue
            main = FilenameAccessor(filename).mainname()
            target_dict.setdefault(main, []).append(os.path.join(dirpath, filename))
    for (dirpath, dirnames, filenames) in os.walk(os.path.join(inpath, origin)):
        if is_invalid_path(dirpath): continue
        filenames = filterFiles(filenames, settings.image_types)
        for filename in filenames:
            main = FilenameAccessor(filename).mainname()
            if not main in target_dict: continue
            orgin_file = os.path.join(dirpath, filename)
            for target_file in target_dict[main]:
                commands = [command, orgin_file, target_file]
                call_exiftool_direct(exclusion_tags + commands)
            del target_dict[main]
