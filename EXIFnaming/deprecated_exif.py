#!/usr/bin/env python3
"""
Old functions do not use them anymore
"""
import os

from EXIFnaming.helpers import settings
from EXIFnaming.helpers.decode import read_exiftags, call_exiftool, askToContinue, write_exiftags, count_files_in, \
    write_exiftag
from EXIFnaming.helpers.fileop import filterFiles, is_invalid_path
from EXIFnaming.helpers.measuring_tools import Clock
from EXIFnaming.helpers.program_dir import log
from EXIFnaming.helpers.tag_conversion import FileMetaData, Location, add_dict


def add_location(country="", city="", location=""):
    """
    deprecated: try to use write_exif_using_csv() instead
    :param country: example:"Germany"
    :param city: example:"Nueremberg"
    :param location: additional location info
    """
    write_exiftags({"Country": country, "City": city, "Location": location})


def location_to_keywords():
    """
    import location exif information to put into Keywords

    deprecated: try to use write_exif_using_csv() instead
    """
    inpath = os.getcwd()
    log().info("process %d Files in %s, subdir: %r",
               count_files_in(inpath, settings.image_types + settings.video_types, ""), inpath, settings.includeSubdirs)
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

    deprecated: try to use write_exif_using_csv() instead
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


def geotag_single(lat: float, lon: float):
    """
    adds gps information to all pictures in all sub directories of current directory

    :deprecated: try to use :func:`write_exif_using_csv` instead
    :param lat: GPSLatitude
    :param lon: GPSLongitude
    """
    inpath = os.getcwd()
    options = ["-GPSLatitudeRef=%f" % lat, "-GPSLatitude=%f" % lat, "-GPSLongitudeRef=%f" % lon,
               "-GPSLongitude=%f" % lon]
    call_exiftool(inpath, "*", options=options)
