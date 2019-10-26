#!/usr/bin/env python3
"""
Organizing fotos according to naming conventions definied by readexif.rename and external programs

dependencies: -
"""
import codecs
import csv
import datetime as dt
import os
import re
from typing import Optional, Match, Iterable, Any, IO, Tuple

import numpy as np
from EXIFnaming.helpers import settings
from EXIFnaming.helpers.constants import CameraModelShort
from EXIFnaming.helpers.date import dateformating
from EXIFnaming.helpers.fileop import renameInPlace, renameTemp, moveBracketSeries, moveSeries, move, removeIfEmtpy, \
    get_relpath_depth, move_media, copyFilesTo, writeToFile, is_invalid_path, get_plain_filenames, filterFiles, isfile, \
    file_has_ext, remove_ext
from EXIFnaming.helpers.misc import askToContinue
from EXIFnaming.helpers.program_dir import get_saves_dir, get_info_dir, get_setexif_dir, log, log_function_call
from EXIFnaming.helpers.tag_conversion import FilenameAccessor
from sortedcollections import OrderedSet

__all__ = ["filter_series", "filter_primary", "copy_subdirectories", "copy_files", "copy_new_files", "replace_in_file",
           "folders_to_main", "rename_HDR", "sanitize_filename", "rename_temp_back", "rename_back", "extract_tags",
           "extract_tags_per_dir", "create_example_csvs", "create_favorites_csv"]


def filter_series():
    """
    put each kind of series in its own directory
    """
    log_function_call(filter_series.__name__)
    inpath = os.getcwd()
    skipdirs = ["B" + str(i) for i in range(1, 8)]
    skipdirs += ["S", "SM", "TL", "mp4", "HDR", "single", "PANO", "others"] + [model for model in CameraModelShort.values() if model]

    log().info(inpath)
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, skipdirs): continue
        log().info("%s #dirs:%d #files:%d", dirpath, len(dirnames), len(filenames))
        filenames = moveBracketSeries(dirpath, filenames)
        filenames = moveSeries(dirpath, filenames, "S")
        filenames = moveSeries(dirpath, filenames, "SM")
        filenames = moveSeries(dirpath, filenames, "TL")
        filenames = move_media(dirpath, filenames, settings.video_types, "mp4")
        filenames = move_media(dirpath, filenames, ["HDR"], "HDR")
        move_media(dirpath, filenames, settings.image_types, "single")


def filter_primary():
    """
    put single and B1 in same directory
    """
    log_function_call(filter_primary.__name__)
    inpath = os.getcwd()
    skipdirs = ["S", "SM", "TL", "mp4", "HDR", "single", "PANO", "others"] + [model for model in CameraModelShort.values() if model]

    log().info(inpath)
    folders_to_main(False, False, False, False, ["B" + str(i) for i in range(1, 8)])
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, skipdirs): continue
        log().info("%s #dirs:%d #files:%d", dirpath, len(dirnames), len(filenames))
        filenames = moveSeries(dirpath, filenames, "S")
        filenames = moveSeries(dirpath, filenames, "SM")
        filenames = moveSeries(dirpath, filenames, "TL")
        filenames = move_media(dirpath, filenames, settings.video_types, "mp4")
        filenames = move_media(dirpath, filenames, ["HDR"], "HDR")
        filenames = moveSeries(dirpath, filenames, "B", "1")
        filenames = moveSeries(dirpath, filenames, "B")
        move_media(dirpath, filenames, settings.image_types, "primary")


def copy_subdirectories(dest: str, dir_names: []):
    """
    copy sub folders of specified names to dest without directory structure
    :param dest: copy destination
    :param dir_names: directory names to copy
    """
    inpath = os.getcwd()
    log().info(inpath)
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, whitelist=dir_names): continue
        copyFilesTo(filenames, dest, False)


def copy_files(dest: str, sub_name: str):
    """
    copy files which have names containing sub_name to dest without directory structure
    :param dest: copy destination
    :param sub_name: name part to search
    """
    inpath = os.getcwd()
    log().info(inpath)
    found_files = []
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        for filename in filenames:
            if sub_name in filename:
                found_files.append(os.path.join(dirpath, filename))
    copyFilesTo(found_files, dest, False)


def copy_new_files(dest: str, playlist: str):
    """
    sorting music files - FIXME maybe not the right place here
    :param dest: copy destination
    :param playlist: name part to search
    """
    csv.register_dialect('tab', delimiter='\t', lineterminator='\r\n')
    with codecs.open(playlist, "rb", "utf-16") as csvfile:
        reader = csv.DictReader(csvfile, dialect="tab")
        places = [remove_ext(row["Ort"]) for row in reader if row is not None]
        places = [os.path.basename(place) for place in places if place is not ""]
    inpath = os.getcwd()
    mp3_files = []
    m4a_files = []
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        for filename in filenames:
            fullname = os.path.join(dirpath, filename)
            if not remove_ext(filename) in places:
                if file_has_ext(filename, [".mp3"]):
                    mp3_files.append(fullname)
                if file_has_ext(filename, [".m4a"]):
                    m4a_files.append(fullname)
    copyFilesTo(mp3_files, os.path.join(dest, "mp3", remove_ext(playlist)), False)
    copyFilesTo(m4a_files, os.path.join(dest, "m4a", remove_ext(playlist)), False)


def replace_in_file(search: str, replace: str, fileext: str):
    """
    replace search with replace in files ending with fileext
    :param search: string to search for
    :param replace: string to replace
    :param fileext: type of file to search in
    """
    inpath = os.getcwd()
    log().info(inpath)
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        for filename in filenames:
            if filename.endswith(fileext):
                log().info(filename)
                fullfilename = os.path.join(dirpath, filename)
                content = ""
                with open(fullfilename, 'r') as file:
                    content = file.read()
                    content = content.replace(search, replace)
                with open(fullfilename, 'w') as file:
                    file.write(content)


def folders_to_main(all_folders=False, series=False, primary=False, blurry=False, dirs=None, one_level=True,
                    not_inpath=True):
    """
    reverses filtering/sorting into directories
    :param series: reverse filterSeries
    :param primary: reverse filterPrimary
    :param blurry: reverse detectBlurry
    :param all_folders: reverse all
    :param dirs: reverse other dirs
    :param one_level: reverse only one directory up
    :param not_inpath: leave all directories in inpath as they are, only change subdirectories
    """
    log_function_call(folders_to_main.__name__, all_folders, series, primary, blurry, dirs, one_level, not_inpath)
    inpath = os.getcwd()
    if dirs is None:
        reverseDirs = []
    else:
        reverseDirs = list(dirs)
    if series: reverseDirs += ["B" + str(i) for i in range(1, 8)] + ["S", "single"]
    if primary: reverseDirs += ["B", "S", "TL", "SM", "primary"]
    if blurry: reverseDirs += ["blurry"]

    deepest = 0
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        depth = get_relpath_depth(dirpath, inpath)
        deepest = max(deepest, depth)
    if all_folders and deepest > 1:
        log().warning("A folder structure with a depth of %2d will be flattened", deepest)
        askToContinue()
    elif deepest > 3:
        log().warning("The folder structure has a depth of %2d", deepest)
        log().info("chosen directory names: %r", reverseDirs)
        askToContinue()

    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not all_folders and not os.path.basename(dirpath) in reverseDirs: continue
        if dirpath == inpath: continue
        log().info("%s #dirs:%d #files:%d", dirpath, len(dirnames), len(filenames))
        for filename in filenames:
            if not file_has_ext(filename, settings.image_types + settings.video_types): continue
            if not_inpath and os.path.dirname(dirpath) == inpath: continue
            if one_level:
                destination = os.path.dirname(dirpath)
            else:
                destination = inpath
            move(filename, dirpath, destination)
        removeIfEmtpy(dirpath)


def rename_HDR(mode="HDRT", folder=r"HDR\w*"):
    """
    rename HDR pictures generated by FRANZIS HDR projects to a nicer form
    :param mode: name for HDR-Mode written to file
    :param folder: only files in folders of this name are renamed
    """
    log_function_call(rename_HDR.__name__, mode, folder)
    matchreg = r"^([-\w]+_[0-9]+)B\d(.*)_(?:\d+B)?\d\2"
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, regex=folder): continue
        log().info("Folder: %s", dirpath)
        for filename in filenames:
            if mode in filename: continue
            match = re.search(matchreg, filename)
            if match:
                _rename_match(dirpath, filename, mode, match)
            else:
                log().info("no match: %s", filename)
        for dirname in dirnames:
            match = re.search(matchreg, dirname)
            if match:
                _rename_match(dirpath, dirname, mode, match)


def _rename_match(dirpath: str, filename: str, mode: str, match: Optional[Match[str]]):
    extension = filename[filename.rfind("."):]
    filename_new_part1 = match.group(1) + "_" + mode
    filename_new_part2 = match.group(2) + extension
    filename_new = filename_new_part1 + filename_new_part2
    i = 2
    while os.path.isfile(os.path.join(dirpath, filename_new)):
        filename_new = filename_new_part1 + "%d" % i + filename_new_part2
        i += 1
    renameInPlace(dirpath, filename, filename_new)


def sanitize_filename(folder=r""):
    """
    sanitize order of Scene and Process tags
    sanitize counter to be split by $
    sanitize sub process names added by a external program to by concat to main processname (only Hugin)
    :param folder:
    :return:
    """
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, regex=folder): continue
        log().info("Folder: %s", dirpath)
        for filename in filenames:
            filename = filename.replace("panorama", "PANO")
            filenameAccessor = FilenameAccessor(filename)
            _sanitize_process_counter(filenameAccessor)
            _sanitize_pano(filenameAccessor)
            filename_new = filenameAccessor.sorted_filename()
            renameInPlace(dirpath, filename, filename_new)


def _sanitize_pano(filenameAccessor: FilenameAccessor):
    matches = [tag for tag in filenameAccessor.processes if tag.startswith("PANO")]
    if not matches: return
    pano_name = matches[0]
    pano_split = pano_name.split("$")
    pano_newname = pano_split[0]
    pano_modi = ["blended", "fused", "hdr"]
    for pano_modus in pano_modi:
        if pano_modus in filenameAccessor.posttags:
            pano_newname += "-" + pano_modus
            filenameAccessor.posttags.remove(pano_modus)
    if len(pano_split) > 0:
        pano_newname = "$".join([pano_newname] + pano_split[1:])
    filenameAccessor.processes.remove(matches[0])
    filenameAccessor.processes = [pano_newname] + filenameAccessor.processes


def _sanitize_process_counter(filenameAccessor: FilenameAccessor):
    processes_new = []
    for process_mode in filenameAccessor.processes:
        if not "$" in process_mode:
            match = re.search(r'([^\d]+)(\d.*)', process_mode)
            if match:
                process_mode = match.group(1) + "$" + match.group(2)
        processes_new.append(process_mode)
        filenameAccessor.processes = processes_new


def _get_new_filename_from_dict(filename_dict: dict):
    filename_new_list = filename_dict["main"] + filename_dict["scene"] + \
                        filename_dict["process"] + filename_dict["tags"]
    return "_".join(filename_new_list)


def rename_temp_back():
    """
    rename temporary renamed files back
    """
    inpath = os.getcwd()
    matchreg = 'temp$'
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        for filename in filenames:
            match = re.search(matchreg, filename)
            if not match: continue
            newFilename = re.sub(matchreg, '', filename)
            renameInPlace(dirpath, filename, newFilename)


def rename_back(timestring="", fileext=".JPG"):
    """
    rename back using backup in saves; change to directory you want to rename back
    :param timestring: time of backup
    :param fileext: file extension
    :return:
    """
    log_function_call(rename_back.__name__)
    dirname = get_saves_dir()
    tagFile = os.path.join(dirname, "Tags" + fileext + "_" + timestring + ".npz")
    if not timestring or os.path.isfile(tagFile):
        tagFiles = [x for x in os.listdir(dirname) if ".npz" in x]
        tagFile = os.path.join(dirname, tagFiles[-1])
    Tagdict = np.load(tagFile)["Tagdict"].item()
    temppostfix = renameTemp(Tagdict["Directory"], Tagdict["File Name new"])
    log().debug("length of Tagdict: %d", len(list(Tagdict.values())[0]))
    for i in range(len(list(Tagdict.values())[0])):
        filename = Tagdict["File Name new"][i] + temppostfix
        if not os.path.isfile(os.path.join(Tagdict["Directory"][i], filename)): continue
        filename_old = Tagdict["File Name"][i]
        renameInPlace(Tagdict["Directory"][i], filename, filename_old)
        Tagdict["File Name new"][i], Tagdict["File Name"][i] = Tagdict["File Name"][i], Tagdict["File Name new"][i]
    timestring = dateformating(dt.datetime.now(), "_MMDDHHmmss")
    np.savez_compressed(os.path.join(dirname, "Tags" + fileext + timestring), Tagdict=Tagdict)


def extract_tags_per_dir():
    """
    extract tags from the file name
    write a csv file with those tags and group them by toplevel directory
    """
    log_function_call(extract_tags_per_dir.__name__)
    inpath = os.getcwd()
    tag_set_names = OrderedSet()
    out_filename = get_info_dir("tags_places.csv")
    tags_places_file, writer = _create_writer(out_filename, ["directory", "name_part"])
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not inpath == dirpath: continue
        for dirname in dirnames:
            if dirname.startswith('.'): continue
            log().info("Folder: %s", dirname)
            tag_set = OrderedSet()
            plain_filenames = get_plain_filenames(inpath, dirname)
            for filename in plain_filenames:
                fileNameAccessor = FilenameAccessor(filename)
                for tag in fileNameAccessor.tags():
                    tag_set.add(tag)
            writeToFile(get_info_dir("tags.txt"), dirname + "\n\t" + "\n\t".join(tag_set) + "\n")

            dirname_split = dirname.split("_")
            subnames = [subname for subname in dirname_split if not subname.isnumeric()]
            dirname = "_".join(subnames)
            for tag in tag_set:
                if not tag[0].isupper(): continue
                tag_set_names.add((dirname, tag))
    writer.writerows(tag_set_names)
    tags_places_file.close()


def extract_tags(location=""):
    """
    extract tags from the file name
    write a csv file with those tags
    :param location: optional content of directory column
    :return:
    """
    inpath = os.getcwd()
    tag_set = OrderedSet()
    tag_set_names = OrderedSet()
    out_filename = get_info_dir("tags_places.csv")
    tags_places_file, writer = _create_writer(out_filename, ["directory", "name_part"])
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        for filename in filenames:
            fileNameAccessor = FilenameAccessor(filename)
            for tag in fileNameAccessor.tags():
                tag_set.add(tag)
    writeToFile(get_info_dir("tags.txt"), "\n\t".join(tag_set) + "\n")
    for tag in tag_set:
        if tag[0].isupper(): continue
        tag_set_names.add((location, tag))
    writer.writerows(tag_set_names)
    tags_places_file.close()


def _create_writer(filename: str, titles: Iterable) -> Tuple[IO, Any]:
    file = open(filename, "w")
    csv.register_dialect('semicolon', delimiter=';', lineterminator='\n')
    writer = csv.writer(file, dialect="semicolon")
    writer.writerow(titles)
    return file, writer


def create_favorites_csv():
    """
    creates a csv file with all files in the directory
    the rating column is filled with "4"
    """
    inpath = os.getcwd()
    out_filename = get_setexif_dir("fav.csv")
    fav_file, writer = _create_writer(out_filename, ["name_part", "rating"])
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath): continue
        for filename in filterFiles(filenames, settings.image_types):
            writer.writerow([filename, 4])
    fav_file.close()


def create_example_csvs():
    """
    creates some examples for csv files
    """
    _create_empty_csv("fav", ["name_part", "rating"])
    _create_empty_csv("gps", ["directory", "name_part", "Location", "gps", "City", "State", "Country", "tags3"])
    _create_empty_csv("tags", ["name_main", "first", "last", "tags", "tags3"])
    _create_empty_csv("processing", ["directory", "name_part", "tags2", "HDR-ghosting", "HDR-strength"])


def _create_empty_csv(name: str, columns: Iterable):
    filename = get_setexif_dir(name + ".csv")
    if isfile(filename): return
    csv_file, writer = _create_writer(filename, columns)
    csv_file.close()
