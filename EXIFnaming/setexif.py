#!/usr/bin/env python3
"""
Writes to Tags

dependencies: exiftool
"""
import csv
import datetime as dt
import os
from typing import Union, List, Iterable

from EXIFnaming.helpers import settings
from EXIFnaming.helpers.date import giveDatetime, dateformating
from EXIFnaming.helpers.decode import read_exiftags, call_exiftool, askToContinue, write_exiftags, count_files_in, \
    write_exiftag, has_not_keys, call_exiftool_direct, read_exiftag
from EXIFnaming.helpers.fileop import filterFiles, is_invalid_path
from EXIFnaming.helpers.measuring_tools import Clock, DirChangePrinter
from EXIFnaming.helpers.program_dir import get_gps_dir, get_setexif_dir, log, log_function_call
from EXIFnaming.helpers.tag_conversion import FileMetaData, Location, add_dict, FilenameAccessor
from EXIFnaming.helpers.tags import create_model, hasDateTime

__all__ = ["shift_time", "fake_date", "geotag", "write_exif_using_csv", "copy_exif_via_mainname"]


def shift_time(hours: int = 0, minutes: int = 0, seconds: int = 0, is_video: bool = False):
    """
    shift DateTimeOriginal to correct for wrong camera time setting

    :example: to adjust time zone by one, set hours=-1

    :param hours: hours to shift
    :param minutes: minutes to shift
    :param seconds: seconds to shift
    :param is_video: whether to modify videos, if false modifies pictures
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
        write_exiftag(outTagDict, model.dir, model.filename)
        dir_change_printer.update(model.dir)
    dir_change_printer.finish()


def fake_date(start='2000:01:01', write=True):
    """
    each file in a directory is one second later
    each dir is one day later
    :param start: the date on which to start generate fake dates
    :param write: whether should write or only print
    """
    log_function_call(fake_date.__name__, start)
    inpath = os.getcwd()
    start += ' 06:00:00.000'
    start_time = giveDatetime(start)
    dir_counter = -1
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath): continue
        filenames = filterFiles(filenames, settings.image_types + settings.video_types)
        if not filenames: continue
        dir_counter += 1
        time = start_time + dt.timedelta(days=dir_counter)
        log().info(time)
        for filename in filenames:
            time += dt.timedelta(seconds=1)
            time_string = dateformating(time, "YYYY:MM:DD HH:mm:ss")
            if write:
                # CreateDate is sometimes set and google fotos gives it precedence over DateTimeOriginal
                write_exiftag({"DateTimeOriginal": time_string}, dirpath, filename,
                              ["-DateCreated=", "-CreateDate=", "-Artist=", "-DigitalCreationDate=", "-ModifyDate="])


def geotag(timezone: int = 2, offset: str = "", start_folder: str = ""):
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


def write_exif_using_csv(csv_filenames: Union[str, List[str]] = "*", folder: str = r"", start_folder: str = "",
                         csv_folder: str = None, csv_restriction: str = "", import_filename: bool = True,
                         import_exif: bool = True,
                         only_when_changed: bool = False, overwrite_gps: bool = False, is_video: bool = False):
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
    :param is_video: wheter video types should be written - video types might not handle tags right
    """
    if not csv_folder:
        csv_folder = get_setexif_dir()

    log_function_call(write_exif_using_csv.__name__, csv_filenames, folder, start_folder, csv_folder, csv_restriction,
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

    filetypes = settings.video_types if is_video else settings.image_types

    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, regex=folder, start=start_folder): continue
        for filename in filterFiles(filenames, filetypes):
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


def _passes_restrictor(meta_data: FileMetaData, csv_restriction: str):
    if not csv_restriction:
        return True
    with open(csv_restriction, "r") as csvfile:
        reader = csv.DictReader(csvfile, dialect='semicolon')
        for row in reader:
            if meta_data.passes_restrictions(row):
                return True
    return False


def copy_exif_via_mainname(origin: str, target: str, overwriteDateTime: bool = False,
                           file_types: Iterable = settings.image_types):
    """
    copy exif information from files in directory origin to target
    files are matched via main name -> processed files can get exif information of original files
    :param overwriteDateTime: whether to overwrite already exiting "Date/Time Original"
    :param origin: where exif infos should be read
    :param target: where exif infos should be written to
    :param file_types: of target files, default: all image types
    """
    log_function_call(copy_exif_via_mainname.__name__, origin, target)
    inpath = os.getcwd()
    target_dict = {}
    exclusion_tags = ["--PreviewImage", "--ThumbnailImage", "--Rating"]
    command = "-TagsFromFile"
    for (dirpath, dirnames, filenames) in os.walk(os.path.join(inpath, target)):
        if is_invalid_path(dirpath): continue
        filenames = filterFiles(filenames, file_types)
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
            if filename in [os.path.basename(target_file) for target_file in target_dict[main]]: continue
            orgin_file = os.path.join(dirpath, filename)
            for target_file in target_dict[main]:
                commands = [command, orgin_file, target_file]
                call_exiftool_direct(exclusion_tags + commands)
            del target_dict[main]
