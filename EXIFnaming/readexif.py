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
from sortedcollections import OrderedSet

from EXIFnaming.helpers import settings, fileop
from EXIFnaming.helpers.date import giveDatetime, newdate, dateformating, print_firstlast_of_dirname, \
    find_dir_with_closest_time, find_dir_with_closest_time_new
from EXIFnaming.helpers.decode import read_exiftags, has_not_keys, read_exiftag
from EXIFnaming.helpers.fileop import writeToFile, renameInPlace, moveFiles, renameTemp, move, \
    copyFilesTo, get_filename_sorted_dirfiletuples, is_invalid_path
from EXIFnaming.helpers.measuring_tools import Clock, TimeJumpDetector
from EXIFnaming.helpers.misc import tofloat
from EXIFnaming.helpers.program_dir import get_saves_dir, get_gps_dir, get_info_dir, log, log_function_call
from EXIFnaming.helpers.tag_conversion import FilenameBuilder
from EXIFnaming.helpers.tags import create_model, getPath

__all__ = ["print_info", "rename", "order", "order_with_timetable", "searchby_exiftag_equality",
           "searchby_exiftag_interval", "rotate", "rename_from_exif", "print_timetable", "better_gpx_via_timetable",
           "find_bad_exif"]


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


def rename(Prefix="", dateformat='YYMM-DD', startindex=1, onlyprint=False, keeptags=False, is_video=False, name="", ignore_model=False):
    """
    Rename into Format: [Prefix][dateformat](_[name])_[Filenumber][SeriesType][SeriesSubNumber]_[PhotoMode]
    :param Prefix: prefix has to fulfil regex [-a-zA-Z]*
    :param dateformat: Y:Year,M:Month,D:Day,N:DayCounter; Number of occurrences determine number of digits
    :param startindex: minimal counter
    :param onlyprint: do not rename; only output file of proposed renaming into saves directory
    :param keeptags: any tags - name or postfixes will be preserved
    :param is_video: is video file extension
    :param name: optional name between date and filenumber, seldom used
    :param ignore_model: whether to sort by model
    """
    log_function_call(rename.__name__, Prefix, dateformat, startindex, onlyprint, keeptags, is_video, name, ignore_model)
    Tagdict = read_exiftags(file_types=settings.video_types if is_video else settings.image_types, ignore_model=ignore_model)
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
            if (sequence_number < 2 and not time == time_old) or model.ignore_same_date() or ignore_model:
                counter += 1
            counterString = ("%0" + digits + "d") % counter
            if not "HDR" in filename: counterString += model.get_sequence_string()

        filenameBuilder.add_main(counterString)
        filenameBuilder.add_post(model.get_mode())
        if keeptags: filenameBuilder.use_old_tags()

        newname = filenameBuilder.build()

        # handle already exiting filename - its ok when they are in different directories
        # its not ok to have to files with one uppercase and another lowercase -> equals with ignore case
        if len(Tagdict["File Name new"]) > 0:
            if newname.lower() == Tagdict["File Name new"][-1].lower() and \
                    Tagdict["Directory"][i].lower() == Tagdict["Directory"][i - 1].lower():
                log().warning("%s already exists - postfix it with V%d", os.path.join(model.dir, newname), 1)
                newname = filenameBuilder.set_version("V%d" % 1).build()

            for version in range(2, 100):
                indexes_samename = [i for i, name in enumerate(Tagdict["File Name new"])
                                    if name.lower() == newname.lower()]
                if indexes_samename:
                    if Tagdict["Directory"][i] == Tagdict["Directory"][indexes_samename[0]]:
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
    log().info("number of photos for each date:")
    for i in range(leng):
        model = create_model(Tagdict, i)
        time = giveDatetime(model.get_date())
        if not i == 0 and newdate(time, time_old, 'D' in dateformat or 'N' in dateformat):
            log().info("%s: %s", time_old.date(), counter)
            if maxCounter < counter: maxCounter = counter
            counter = startindex - 1
        if model.get_sequence_number() < 2: counter += 1
        time_old = time
    log().info("%s: %s", time_old.date(), counter)
    if maxCounter < counter: maxCounter = counter
    return str(len(str(maxCounter)))


def order():
    """
    order by date using exif info
    """
    log_function_call(order.__name__)
    inpath = os.getcwd()

    Tagdict = read_exiftags(file_types=settings.image_types, ignore_model=True)
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
    log().info('Number of JPG: %d', leng)
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
    if len(Tagdict_mp4) == 0:
        return
    leng = len(list(Tagdict_mp4.values())[0])
    log().info('Number of mp4: %d', leng)
    for i in range(leng):
        model = create_model(Tagdict_mp4, i)
        time = giveDatetime(model.get_date())
        dirName = find_dir_with_closest_time(dirNameDict_firsttime, dirNameDict_lasttime, time)

        if dirName:
            move(model.filename, model.dir, os.path.join(inpath, dirName, "mp4"))
        else:
            log().warning("Did not move %s to %s", model.filename, dirName)


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


def rotate(subname: str = "", folder: str = r"", sign=1, override=True, ask=True):
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
        if has_not_keys(Tagdict, keys=["Orientation"]): continue
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


def rename_from_exif():
    """
    use exif information written by :func:`write_exif_using_csv` to restore filename
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
            log().info("Folder: %s", dirname)
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
    :return:
    """
    if not timefile:
        timefile = get_info_dir("timetable.txt")

    log_function_call(order_with_timetable.__name__, timefile)

    dirNameDict_firsttime, dirNameDict_lasttime = _read_timetable(timefile)
    Tagdict = read_exiftags()
    leng = len(list(Tagdict.values())[0])
    log().info('Number of jpg: %d', leng)
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


def _read_timetable_new(filename: str = None):
    if not filename:
        filename = get_info_dir("timetable.txt")

    file = open(filename, 'r')
    dirNameDict = OrderedDict()
    for line in file:
        dir_name, start, end = [entry.strip(' ').strip('\r\n') for entry in line.split(';')]
        if not start or not end: continue
        start = dt.datetime.strptime(start, _read_timetable.timeformat)
        end = dt.datetime.strptime(end, _read_timetable.timeformat)
        dirNameDict[dir_name] = (start, end)
    file.close()
    return dirNameDict


def better_gpx_via_timetable(gpxfilename: str = "", gpxTimeRegex: str = "%Y-%m-%dT%H:%M:%S.%fZ", timedelta=3600, timezone=0):
    """
    crossmatch gpx file with timetable and take only entries for which photos exist
    :param gpxfilename: input gpx file, can be left empty to use all
    :param gpxTimeRegex: regex of time in gpx file
    :param timedelta: how near the gpx Data has to be to the timetable in secounds
    :param timezone: hours compaired to UTC
    output: _new1.gpx containing only usefull locations
            _new2.gpx containing only not usefull locations

    does not uses exif infos
    """

    def write(dirName_last, gpxfile_out):
        if dirName != dirName_last:
            if not dirName_last == "": gpxfile_out.write("</trkseg></trk>\r\n")
            gpxfile_out.write("<trk><name>" + dirName + "</name><trkseg>\r\n")
        gpxfile_out.write(line)

    def get_gpx_files():
        gpxDir = get_gps_dir()
        files = []
        for (dirpath, dirnames, filenames) in os.walk(gpxDir):
            if not gpxDir == dirpath: break
            for filename in filenames:
                if not filename.endswith(".gpx"): continue
                files.append(os.path.join(gpxDir, filename))
        return files

    timefile = get_info_dir("timetable.txt")
    gpxfilenames = [get_gps_dir(gpxfilename)] if gpxfilename else get_gpx_files()
    dirNameDict = _read_timetable_new(timefile)
    timeregex = re.compile("(.*<time>)([^<]*)(</time>.*)")
    gpxfilename_out, ext = gpxfilenames[0].rsplit('.', 1)
    dirName_last1 = ""
    dirName_last2 = ""
    gpxfile_out1 = open(gpxfilename_out + "_new1." + ext, "w")
    gpxfile_out2 = open(gpxfilename_out + "_new2." + ext, "w")
    for gpxfilename in gpxfilenames:
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
                time = dt.datetime.strptime(time, gpxTimeRegex)
                time = time + dt.timedelta(hours=timezone)
                dirName = find_dir_with_closest_time_new(dirNameDict, time, timedelta)
                if "unrelated" in dirName:
                    write(dirName_last2, gpxfile_out2)
                    dirName_last2 = dirName
                else:
                    write(dirName_last1, gpxfile_out1)
                    dirName_last1 = dirName
                    print(dirName_last1, dirName_last2)
    gpxfile_out1.close()
    gpxfile_out2.close()


def tidy_gpx(gpxfilename: str = ""):
    gpxfilename = get_gps_dir(gpxfilename)
    gpxfilename_out, ext = gpxfilename.rsplit('.', 1)
    gpxfile_out = open(gpxfilename_out + "_new1." + ext, "w")
    gpxfile_out.write(
        '<?xml version="1.0" encoding="UTF-8" ?><gpx version="1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.topografix.com/GPX/1/0" xsi:schemaLocation="http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd">\r\n')
    import xml.etree.ElementTree as ET
    tree = ET.parse(gpxfilename)
    root = tree.getroot()
    for child in root:
        if "trk" in child.tag:
            gpxfile_out.write("<trk>")
            for child2 in child:
                if "trkseg" in child2.tag:
                    gpxfile_out.write("<trkseg>\n")
                    for child3 in child2:
                        if "trkpt" in child3.tag:
                            gpxfile_out.write(f'<trkpt lat="{child3.attrib["lat"]}" lon="{child3.attrib["lon"]}">')
                            for child4 in child3:
                                if "ele" in child4.tag:
                                    gpxfile_out.write(f'<ele>{child4.text}</ele>')
                                if "time" in child4.tag:
                                    gpxfile_out.write(f'<time>{child4.text}</time>')
                                if "course" in child4.tag:
                                    gpxfile_out.write(f'<course>{child4.text}</course>')
                                if "speed" in child4.tag:
                                    gpxfile_out.write(f'<speed>{child4.text}</speed>')
                        gpxfile_out.write("</trkpt>\n")
                    gpxfile_out.write("</trkseg>\n")
            gpxfile_out.write("</trk>")

    gpxfile_out.write('</gpx>')
    gpxfile_out.close()


def find_bad_exif(do_move=True, check_date_additional=False, folder: str = r""):
    """
    find files with missing exif data
    """
    log_function_call(find_bad_exif.__name__, do_move)

    clock = Clock()
    inpath = os.getcwd()
    lines_no_tags = OrderedSet()
    lines_bad_date_additional = OrderedSet()
    lines_date_missing = OrderedSet()
    out_filename_no_tags = get_info_dir("no_tags.csv")
    file_no_tags, writer_no_tags = fileop.create_csv_writer(out_filename_no_tags,
                                                            ["directory", "name_part"])
    out_filename_bad_date_additional = get_info_dir("bad_date_additional.csv")
    file_bad_date_additional, writer_bad_date_additional = fileop.create_csv_writer(out_filename_bad_date_additional,
                                                                                    ["directory", "name_part"])
    out_filename_date_missing = get_info_dir("date_missing.csv")
    file_date_missing, writer_date_missing = fileop.create_csv_writer(out_filename_date_missing,
                                                                      ["directory", "name_part"])
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, regex=folder): continue
        if fileop.count_files(filenames, settings.image_types) == 0: continue
        Tagdict = read_exiftags(dirpath, settings.image_types, ask=False)
        if len(list(Tagdict.values())) == 0: continue
        leng = len(list(Tagdict.values())[0])
        for i in range(leng):
            if (not "Keywords" in Tagdict or not Tagdict["Keywords"][i]) or \
                    (not "Subject" in Tagdict or not Tagdict["Subject"][i]) or \
                    (not "Description" in Tagdict or not Tagdict["Description"][i]) or \
                    (not "User Comment" in Tagdict or not Tagdict["User Comment"][i]):
                lines_no_tags.add(
                    (os.path.basename(dirpath), _remove_counter(Tagdict["File Name"][i])))
                if do_move and not "bad_exif" in dirpath:
                    move(Tagdict["File Name"][i], dirpath,
                         dirpath.replace(inpath, os.path.join(inpath, "bad_exif_keywords")))
            if not "Date/Time Original" in Tagdict or not Tagdict["Date/Time Original"][i]:
                lines_date_missing.add(
                    (os.path.basename(dirpath), _remove_counter(Tagdict["File Name"][i])))
                if do_move and not "bad_exif" in dirpath:
                    move(Tagdict["File Name"][i], dirpath,
                         dirpath.replace(inpath, os.path.join(inpath, "bad_exif_date_missing")))
            if check_date_additional and \
                    (("Date Created" in Tagdict and Tagdict["Date Created"][i]) or
                     ("Time Created" in Tagdict and Tagdict["Time Created"][i]) or
                     ("Create Date" in Tagdict and Tagdict["Create Date"][i]) or
                     ("Modify Date" in Tagdict and Tagdict["Modify Date"][i]) or
                     ("Digital Creation Date" in Tagdict and Tagdict["Digital Creation Date"][i])):
                lines_bad_date_additional.add(
                    (os.path.basename(dirpath), _remove_counter(Tagdict["File Name"][i])))
                if do_move and not "bad_exif" in dirpath:
                    move(Tagdict["File Name"][i], dirpath,
                         dirpath.replace(inpath, os.path.join(inpath, "bad_exif_date_additional")))
    writer_no_tags.writerows(lines_no_tags)
    writer_bad_date_additional.writerows(lines_bad_date_additional)
    writer_date_missing.writerows(lines_date_missing)
    file_no_tags.close()
    file_bad_date_additional.close()
    file_date_missing.close()
    clock.finish()


def first_date_per_folder() -> OrderedDict:
    """
    find files with missing exif data
    """
    log_function_call(first_date_per_folder.__name__)

    clock = Clock()
    inpath = os.getcwd()
    folder_dict = OrderedDict()

    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath): continue
        if fileop.count_files(filenames, settings.image_types) == 0: continue
        Tagdict = read_exiftags(dirpath, settings.image_types, ask=False)
        if len(list(Tagdict.values())) == 0: continue
        folder_dict[os.path.relpath(dirpath, inpath)] = [date for date in Tagdict["Date/Time Original"] if date][0]

    clock.finish()
    return folder_dict


def _remove_counter(filename: str):
    filename = fileop.remove_ext(filename)
    return filename[:filename.rfind("_")]
