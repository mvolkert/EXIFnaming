#!/usr/bin/env python3
"""
Reads Tags to use them, but not write to them

dependencies: exiftool, Pillow
"""

import datetime as dt
import os
import re
from collections import OrderedDict

import numpy as np

from EXIFnaming.helpers import settings
from EXIFnaming.helpers.date import giveDatetime, newdate, dateformating, print_firstlast_of_dirname, \
    find_dir_with_closest_time
from EXIFnaming.helpers.decode import read_exiftags, has_not_keys, read_exiftag
from EXIFnaming.helpers.fileop import writeToFile, renameInPlace, moveFiles, renameTemp, move, \
    copyFilesTo, get_filename_sorted_dirfiletuples, is_invalid_path
from EXIFnaming.helpers.measuring_tools import Clock, TimeJumpDetector
from EXIFnaming.helpers.misc import tofloat
from EXIFnaming.helpers.program_dir import get_saves_dir, get_gps_dir, get_info_dir, log, log_function_call
from EXIFnaming.helpers.tag_conversion import FilenameBuilder
from EXIFnaming.helpers.tags import create_model, getPath

__all__ = ["print_info", "rename", "rename_pm", "order", "order_with_timetable", "searchby_exiftag_equality",
           "searchby_exiftag_interval", "rotate", "exif_to_name", "print_timetable", "better_gpx_via_timetable"]


def print_info(tagGroupNames=(), allGroups=False):
    """
    write tag info of tagGroupNames to a file in saves dir
    :param tagGroupNames: selectable groups (look into constants)
    :param allGroups: take all tagGroupNames
    """
    tagdict = read_exiftags()
    model = create_model(tagdict, 0)
    tagnames = model.TagNames
    if allGroups: tagGroupNames = tagnames.keys()
    for tagGroupName in tagnames:
        if not tagGroupNames == [] and not tagGroupName in tagGroupNames: continue
        outstring = "%-80s\t" % "File Name"
        for entry in tagnames[tagGroupName]:
            if not entry in tagdict: continue
            outstring += "%-30s\t" % entry
        outstring += "\n"

        for i in range(len(tagdict["File Name"])):
            outstring += "%-80s\t" % tagdict["File Name"][i]
            for entry in tagnames[tagGroupName]:
                if not entry in tagdict: continue
                val = tagdict[entry]
                outstring += "%-30s\t" % val[i]
            outstring += "\n"

        dirname = get_saves_dir()
        writeToFile(os.path.join(dirname, "tags_" + tagGroupName + ".txt"), outstring)


def rename_pm(Prefix="", dateformat='YYMM-DD', startindex=1, onlyprint=False, keeptags=True, name=""):
    """
    rename for JPG and MP4
    """
    rename(Prefix, dateformat, startindex, onlyprint, keeptags, False, name)
    rename(Prefix, dateformat, 1, onlyprint, keeptags, True, name)


def rename(Prefix="", dateformat='YYMM-DD', startindex=1, onlyprint=False, keeptags=True, is_video=False, name=""):
    """
    Rename into Format: [Prefix][dateformat](_[name])_[Filenumber][SeriesType][SeriesSubNumber]_[PhotoMode]
    :param Prefix: prefix has to fulfil regex [-a-zA-Z]*
    :param dateformat: Y:Year,M:Month,D:Day,N:DayCounter; Number of occurrences determine number of digits
    :param startindex: minimal counter
    :param onlyprint: do not rename; only output file of proposed renaming into saves directory
    :param keeptags: any tags - name or postfixes will be preserved
    :param is_video: is video file extension
    :param name: optional name between date and filenumber, seldom used
    """
    log_function_call(rename.__name__, Prefix, dateformat, startindex, onlyprint, keeptags, is_video, name)
    Tagdict = read_exiftags(file_types=settings.video_types if is_video else settings.image_types)
    if not Tagdict: return

    # rename temporary
    if not onlyprint:
        temppostfix = renameTemp(Tagdict["Directory"], Tagdict["File Name"])
    else:
        temppostfix = ""

    # initialize
    outstring = ""
    Tagdict["File Name new"] = []
    time_old = giveDatetime()
    counter = startindex - 1
    digits = _count_files_for_each_date(Tagdict, startindex, dateformat)
    number_of_files = len(list(Tagdict.values())[0])
    daystring = ""

    for i in range(number_of_files):
        model = create_model(Tagdict, i)
        time = giveDatetime(model.get_date())
        filename = model.filename

        if newdate(time, time_old, 'D' in dateformat or 'N' in dateformat):
            daystring = dateformating(time, dateformat)
            if not i == 0: counter = 0

        filenameBuilder = FilenameBuilder(filename)
        filenameBuilder.add_main(Prefix + daystring)
        filenameBuilder.add_main(model.get_model_abbr())
        filenameBuilder.add_main(name)

        if is_video:
            counter += 1
            counterString = "M%02d" % counter
            filenameBuilder.add_post(model.get_recMode())
        else:
            # SequenceNumber
            sequence_number = model.get_sequence_number()
            if sequence_number < 2 and not time == time_old or model.ignore_same_date():
                counter += 1
            counterString = ("%0" + digits + "d") % counter
            if not "HDR" in filename: counterString += model.get_sequence_string()

        filenameBuilder.add_main(counterString)
        filenameBuilder.add_post(model.get_mode())
        if keeptags: filenameBuilder.use_old_tags()

        newname = filenameBuilder.build()

        # handle already exiting filename - its ok when they are in different directories
        if len(Tagdict["File Name new"]) > 0:
            if newname == Tagdict["File Name new"][-1] and Tagdict["Directory"][i] == Tagdict["Directory"][i - 1]:
                log().warning("%s already exists - assume it is an unknown creative mode",
                              os.path.join(model.dir, newname))
                newname = filenameBuilder.set_version("CRTV").build()

            for version in range(2, 100):
                if newname in Tagdict["File Name new"]:
                    index = Tagdict["File Name new"].index(newname)
                    if Tagdict["Directory"][i] == Tagdict["Directory"][index]:
                        log().warning("%s already exists - postfix it with V%d", os.path.join(model.dir, newname),
                                      version)
                        newname = filenameBuilder.set_version("V%d" % version).build()
                    else:
                        break
                else:
                    break

        time_old = time
        Tagdict["File Name new"].append(newname)
        outstring += _write(model.dir, filename, temppostfix, newname, onlyprint)

    dirname = get_saves_dir()
    timestring = dateformating(dt.datetime.now(), "_MMDDHHmmss")
    video_str = "_video" if is_video else ""
    np.savez_compressed(os.path.join(dirname, "Tags" + video_str + timestring), Tagdict=Tagdict)
    writeToFile(os.path.join(dirname, "newnames" + video_str + timestring + ".txt"), outstring)


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
        model = create_model(Tagdict, i)
        time = giveDatetime(model.get_date())
        if not i == 0 and newdate(time, time_old, 'D' in dateformat or 'N' in dateformat):
            print(time_old.date(), counter)
            if maxCounter < counter: maxCounter = counter
            counter = startindex - 1
        if model.get_sequence_number() < 2: counter += 1
        time_old = time
    print(time_old.date(), counter)
    if maxCounter < counter: maxCounter = counter
    return str(len(str(maxCounter)))


def order():
    """
    order by date using exif info
    """
    log_function_call(order.__name__)
    inpath = os.getcwd()

    Tagdict = read_exiftags(file_types=settings.image_types)
    timeJumpDetector = TimeJumpDetector()
    time_old = giveDatetime()
    dircounter = 1
    filenames = []
    leng = len(list(Tagdict.values())[0])
    dirNameDict_firsttime = OrderedDict()
    dirNameDict_lasttime = OrderedDict()
    time = giveDatetime(create_model(Tagdict, 0).get_date())
    daystring = dateformating(time, "YYMMDD_")
    dirName = daystring + "%02d" % dircounter
    dirNameDict_firsttime[time] = dirName
    print('Number of JPG: %d' % leng)
    for i in range(leng):
        model = create_model(Tagdict, i)
        time = giveDatetime(model.get_date())

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
        filenames.append((model.dir, model.filename))
        time_old = time

    dirNameDict_lasttime[time_old] = dirName
    moveFiles(filenames, os.path.join(inpath, dirName))

    print_firstlast_of_dirname(dirNameDict_firsttime, dirNameDict_lasttime)

    Tagdict_mp4 = read_exiftags(file_types=settings.video_types)
    leng = len(list(Tagdict_mp4.values())[0])
    print('Number of mp4: %d' % leng)
    for i in range(leng):
        model = create_model(Tagdict_mp4, i)
        time = giveDatetime(model.get_date())
        dirName = find_dir_with_closest_time(dirNameDict_firsttime, dirNameDict_lasttime, time)

        if dirName:
            move(model.filename, model.dir, os.path.join(inpath, dirName, "mp4"))
        else:
            log().warning("Did not move %s to %s" % (model.filename, dirName))


def searchby_exiftag_equality(tag_name: str, value: str):
    """
    searches for files where the value of the exiftag equals the input value
    :param tag_name: exiftag key
    :param value: exiftag value
    """
    Tagdict = read_exiftags()
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Date/Time Original", tag_name]): return
    leng = len(list(Tagdict.values())[0])
    files = []
    for i in range(leng):
        if not Tagdict[tag_name][i] == value: continue
        files.append(getPath(Tagdict, i))
    copyFilesTo(files, os.path.join(os.getcwd(), "matches"))


def searchby_exiftag_interval(tag_name: str, min_value: float, max_value: float):
    """
    searches for files where the value of the exiftag is in the specified interval
    :param tag_name: exiftag key
    :param min_value: interval start
    :param max_value: interval end
    """
    inpath = os.getcwd()
    Tagdict = read_exiftags(inpath)
    if has_not_keys(Tagdict, keys=[tag_name]): return
    leng = len(list(Tagdict.values())[0])
    files = []
    for i in range(leng):
        value = tofloat(Tagdict[tag_name][i])
        if not (value and min_value < value < max_value): continue
        files.append(getPath(Tagdict, i))
    copyFilesTo(files, os.path.join(inpath, "matches"))


def rotate(subname="", folder=r"", sign=1, override=True, ask=True):
    """
    rotate back according to tag information (Rotate 90 CW or Rotate 270 CW)
    Some programs like franzis hdr projects rotate the resolution of the picture -> picture gets upward resolution and
    shown as rotated two times. This function reverses the resolution rotation according to exif info.
    Pictures that either have no rotation according to exif or have a normal resolution ratio are not modified.
    So calling it a second time wont change anything.
    :param subname: only files that contain this name are rotated, empty string: no restriction
    :param sign: direction of rotation
    :param folder: only files in directories that match this regex are rotated, empty string: no restriction
    :param override: override file with rotated one
    :param ask: if should ask for user confirmation
    """
    log_function_call(rotate.__name__, subname, folder, sign, override, ask)
    from PIL import Image

    NFiles = 0
    clock = Clock()
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, regex=folder): continue
        if len(filenames) == 0: continue
        Tagdict = read_exiftags(dirpath, settings.image_types, ask=ask)
        if has_not_keys(Tagdict, keys=["Rotation"]): continue
        leng = len(list(Tagdict.values())[0])
        for i in range(leng):
            # Load the original image:
            model = create_model(Tagdict, i)
            if not subname in model.filename: continue
            if model.is_rotated_by(0) or not model.is_upward():
                continue
            name = model.get_path()
            log().info("rotate %s", model.filename)
            img = Image.open(name)
            if model.is_rotated_by(90):
                img_rot = img.rotate(90 * sign, expand=True)
            elif model.is_rotated_by(-90):
                img_rot = img.rotate(-90 * sign, expand=True)
            else:
                continue
            NFiles += 1
            if not override: name = name[:name.rfind(".")] + "_ROTATED" + name[name.rfind("."):]
            img_rot.save(name, 'JPEG', quality=99, exif=img.info['exif'])
    clock.finish()


def exif_to_name():
    """
    reverse exif_to_name()
    """
    Tagdict = read_exiftags()
    if has_not_keys(Tagdict, keys=["Label"]): return

    temppostfix = renameTemp(Tagdict["Directory"], Tagdict["File Name"])
    leng = len(list(Tagdict.values())[0])
    for i in range(leng):
        filename = Tagdict["File Name"][i]
        ext = filename[filename.rfind('.'):]
        renameInPlace(Tagdict["Directory"][i], filename + temppostfix, Tagdict["Label"][i] + ext)


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
            fotos = get_filename_sorted_dirfiletuples(settings.image_types, inpath, dirname)
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


def order_with_timetable(timefile: str = None):
    """
    use timetable to create folder structure
    :param timefile: timetable file
    :param fileexts: extensions
    :return:
    """
    if not timefile:
        timefile = get_info_dir("timetable.txt")

    log_function_call(order_with_timetable.__name__, timefile)

    dirNameDict_firsttime, dirNameDict_lasttime = _read_timetable(timefile)
    Tagdict = read_exiftags()
    leng = len(list(Tagdict.values())[0])
    print('Number of jpg: %d' % leng)
    for i in range(leng):
        model = create_model(Tagdict, i)
        time = giveDatetime(model.get_date())
        dirName = find_dir_with_closest_time(dirNameDict_firsttime, dirNameDict_lasttime, time)

        if dirName:
            move(model.filename, model.dir, os.path.join(os.getcwd(), dirName))


def _read_timetable(filename: str = None):
    if not filename:
        filename = get_info_dir("timetable.txt")

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


def better_gpx_via_timetable(gpxfilename: str):
    """
    crossmatch gpx file with timetable and take only entries for which photos exist
    :param gpxfilename: input gpx file
    output: _new1.gpx containing only usefull locations
            _new2.gpx containing only not usefull locations

    does not uses exif infos
    """

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
