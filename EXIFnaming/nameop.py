#!/usr/bin/env python3
"""
Does not uses Tags at all
"""
import csv
import datetime as dt
import os
import re
from typing import Optional, Match

import numpy as np
from sortedcollections import OrderedSet

from EXIFnaming.helpers.constants import CameraModelShort
from EXIFnaming.helpers.date import dateformating
from EXIFnaming.helpers.fileop import renameInPlace, renameTemp, moveBracketSeries, \
    moveSeries, move, removeIfEmtpy, get_relpath_depth, move_media, copyFilesTo, writeToFile, is_invalid_path, \
    get_plain_filenames, \
    filterFiles
from EXIFnaming.helpers.misc import askToContinue
from EXIFnaming.helpers.program_dir import get_saves_dir, get_info_dir, get_setexif_dir, log
from EXIFnaming.helpers.settings import image_types
from EXIFnaming.helpers.tag_conversion import split_filename


def filter_series():
    """
    put each kind of series in its own directory
    """
    inpath = os.getcwd()
    skipdirs = ["B" + str(i) for i in range(1, 8)]
    skipdirs += ["S", "SM", "TL", "mp4", "HDR", "single", "Pano", "others"] + list(CameraModelShort.values())

    log().info(inpath)
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, skipdirs): continue
        log().info("%s #dirs:%d #files:%d", dirpath, len(dirnames), len(filenames))
        filenames = moveBracketSeries(dirpath, filenames)
        filenames = moveSeries(dirpath, filenames, "S")
        filenames = moveSeries(dirpath, filenames, "SM")
        filenames = moveSeries(dirpath, filenames, "TL")
        filenames = move_media(dirpath, filenames, ".MP4", "mp4")
        filenames = move_media(dirpath, filenames, "HDR", "HDR")
        move_media(dirpath, filenames, ".JPG", "single")


def filter_primary():
    """
    put single and B1 in same directory
    """
    inpath = os.getcwd()
    skipdirs = ["S", "SM", "TL", "mp4", "HDR", "single", "Pano", "others"] + list(CameraModelShort.values())

    log().info(inpath)
    folders_to_main(False, False, False, False, ["B" + str(i) for i in range(1, 8)])
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, skipdirs): continue
        log().info("%s #dirs:%d #files:%d", dirpath, len(dirnames), len(filenames))
        filenames = moveSeries(dirpath, filenames, "S")
        filenames = moveSeries(dirpath, filenames, "SM")
        filenames = moveSeries(dirpath, filenames, "TL")
        filenames = move_media(dirpath, filenames, ".MP4", "mp4")
        filenames = move_media(dirpath, filenames, "HDR", "HDR")
        filenames = moveSeries(dirpath, filenames, "B", "1")
        filenames = moveSeries(dirpath, filenames, "B")
        move_media(dirpath, filenames, ".JPG", "primary")


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
            if not filename[-4:] in (".JPG", ".jpg", ".MP4", ".mp4"): continue
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


def rename_to_front(mode="PANO", folder=r"HDR\w*"):
    """
    move the underscore entry matching the mode to the front after counter
    :param mode: name of underscore entry
    :param folder: only files in folders of this name are renamed
    """
    panoOut = r"^([-\w]+_[0-9]+[A-Z0-9]*)_(.*)_(%s[-0-9]*)(.*)" % mode
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, regex=folder): continue
        log().info("Folder: %s", dirpath)
        for filename in filenames:
            match = re.search(panoOut, filename)
            if match:
                filename_new = match.group(1) + "_" + match.group(3) + "_" + match.group(2) + match.group(4)
                if os.path.isfile(os.path.join(dirpath, filename_new)):
                    log().info("file already exists: %s", filename_new)
                else:
                    renameInPlace(dirpath, filename, filename_new)
            else:
                log().info("no match: %s", filename)


def rename_PANO(folder=r""):
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, regex=folder): continue
        log().info("Folder: %s", dirpath)
        for filename in filenames:
            if not "PANO" in filename: continue
            name, ext = filename.rsplit('.', 1)
            filename_dict = split_filename(name, ext)
            _sanitize_pano(filename_dict)
            filename_new = _get_new_filename_from_dict(filename_dict) + "." + ext
            renameInPlace(dirpath, filename, filename_new)


def sanitize_filename(folder=r""):
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, regex=folder): continue
        log().info("Folder: %s", dirpath)
        for filename in filenames:
            name, ext = filename.rsplit('.', 1)
            name = name.replace("panorama", "PANO")
            filename_dict = split_filename(name, ext)
            _sanitize_process_counter(filename_dict)
            _sanitize_pano(filename_dict)
            filename_new = _get_new_filename_from_dict(filename_dict) + "." + ext
            renameInPlace(dirpath, filename, filename_new)


def _sanitize_pano(filename_dict: dict):
    matches = [tag for tag in filename_dict["process"] if tag.startswith("PANO")]
    if not matches: return
    pano_name = matches[0]
    pano_split = pano_name.split("$")
    pano_newname = pano_split[0]
    pano_modi = ["blended", "fused", "hdr"]
    for pano_modus in pano_modi:
        if pano_modus in filename_dict["tags"]:
            pano_newname += "-" + pano_modus
            filename_dict["tags"].remove(pano_modus)
    if len(pano_split) > 0:
        pano_newname = "$".join([pano_newname] + pano_split[1:])
    filename_dict["process"].remove(matches[0])
    filename_dict["process"] = [pano_newname] + filename_dict["process"]


def _sanitize_process_counter(filename_dict: dict):
    processes_new = []
    for process_mode in filename_dict["process"]:
        if not "$" in process_mode:
            match = re.search(r'([^\d]+)(\d.*)', process_mode)
            if match:
                process_mode = match.group(1) + "$" + match.group(2)
        processes_new.append(process_mode)
    filename_dict["process"] = processes_new


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

    """
    inpath = os.getcwd()
    csv.register_dialect('semicolon', delimiter=';', lineterminator='\n')
    tag_set_names = OrderedSet()
    tags_places_file = open(get_info_dir("tags_places.csv"), "w")
    writer = csv.writer(tags_places_file, dialect="semicolon")
    writer.writerow(["directory", "name_part"])
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not inpath == dirpath: continue
        for dirname in dirnames:
            if dirname.startswith('.'): continue
            log().info("Folder: %s", dirname)
            tag_set = OrderedSet()
            plain_filenames = get_plain_filenames(inpath, dirname)
            for filename in plain_filenames:
                name, ext = filename.rsplit('.', 1)
                filename_dict = split_filename(name, ext)
                for tag in filename_dict["tags"]:
                    if not tag: continue
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
    inpath = os.getcwd()
    csv.register_dialect('semicolon', delimiter=';', lineterminator='\n')
    tag_set_names = OrderedSet()
    tags_places_file = open(get_info_dir("tags_places.csv"), "w")
    writer = csv.writer(tags_places_file, dialect="semicolon")
    writer.writerow(["directory", "name_part"])
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        tag_set = OrderedSet()
        for filename in filenames:
            name, ext = filename.rsplit('.', 1)
            filename_dict = split_filename(name, ext)
            for tag in filename_dict["tags"]:
                if not tag: continue
                tag_set.add(tag)
        writeToFile(get_info_dir("tags.txt"), location + "\n\t" + "\n\t".join(tag_set) + "\n")
        for tag in tag_set:
            if not tag[0].isupper(): continue
            tag_set_names.add((location, tag))
    writer.writerows(tag_set_names)
    tags_places_file.close()


def create_favorites_csv():
    inpath = os.getcwd()
    csv.register_dialect('semicolon', delimiter=';', lineterminator='\n')
    fav_file = open(get_setexif_dir("fav.csv"), "w")
    writer = csv.writer(fav_file, dialect="semicolon")
    writer.writerow(["name_part", "rating"])
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath): continue
        for filename in filterFiles(filenames, image_types):
            writer.writerow([filename, 4])
    fav_file.close()
