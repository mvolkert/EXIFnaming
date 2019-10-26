import operator
import os
import subprocess
import sys
from collections import OrderedDict
from typing import List, Dict, Set

from sortedcollections import OrderedSet

from EXIFnaming.helpers.fileop import count_files, count_files_in, is_invalid_path, isfile
from EXIFnaming.helpers.measuring_tools import Clock
from EXIFnaming.helpers.program_dir import log
from EXIFnaming.helpers import settings
from EXIFnaming.models import ModelBase

__all__ = ["read_exiftags", "call_exiftool", "askToContinue", "write_exiftags", "count_files_in", "write_exiftag",
           "has_not_keys", "call_exiftool_direct", "read_exiftag"]


def read_exiftags(inpath="", file_types=settings.image_types, skipdirs=(), ask=True):
    if not inpath:
        inpath = os.getcwd()
    file_types = _get_distinct_filestypes(file_types)
    log().info("process %d %s Files in %s, settings.includeSubdirs: %r",
               count_files_in(inpath, file_types, skipdirs), file_types, inpath, settings.includeSubdirs)
    if ask: askToContinue()

    clock = Clock()
    ListOfDicts = []
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, skipdirs): continue
        if count_files(filenames, file_types) == 0:
            log().info("  No matching files in %s", os.path.relpath(dirpath, inpath))
            continue
        for filetype in file_types:
            if count_files(filenames, [filetype]) == 0:
                continue
            out, err = call_exiftool(dirpath, "*" + filetype, [], False)
            out = out[out.find("ExifTool Version Number"):]
            out_split = out.split("========")
            log().info("%4d tags of %s files extracted in %s", len(out_split), filetype,
                       os.path.relpath(dirpath, inpath))
            for tags in out_split:
                ListOfDicts.append(decode_exiftags(tags))

    outdict = listsOfDicts_to_dictOfLists(ListOfDicts)
    if not outdict: return {}
    outdict = sort_dict_by_date_and_model(outdict)
    clock.finish()
    return outdict


def _get_distinct_filestypes(types: List[str]) -> Set[str]:
    return set([filetype.lower() for filetype in types])


def write_exiftags(tagDict: dict, inpath="", options=()):
    if not inpath:
        inpath = os.getcwd()
    clock = Clock()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not settings.includeSubdirs and not inpath == dirpath: break
        n = count_files(filenames, settings.image_types + settings.video_types)
        if n == 0:
            log().info("  No matching files in %s", os.path.relpath(dirpath, inpath))
            continue
        all_options = list(options) + tag_dict_to_options(tagDict)
        call_exiftool(dirpath, "*", all_options, True)
        log().info("%4d tags written in   %s", n, os.path.relpath(dirpath, inpath))
    clock.finish()


def write_exiftag(tagDict: dict, inpath="", filename="", options=("-ImageDescription=", "-XPComment=")):
    if not inpath:
        inpath = os.getcwd()
    all_options = list(options) + tag_dict_to_options(tagDict)
    call_exiftool(inpath, filename, all_options, True)


def tag_dict_to_options(data: dict) -> list:
    options = []
    for key in data:
        if not data[key]: continue
        if type(data[key]) == list:
            data_set = OrderedSet(data[key])
            for value in data_set:
                if value:
                    options.append("-%s=%s" % (key, value))
        else:
            options.append("-%s=%s" % (key, data[key]))
    return options


def has_not_keys(indict: dict, keys: list) -> bool:
    if not keys: return True
    notContains = []
    for key in keys:
        if not key in indict:
            notContains.append(key)
            log().info("%s not in dict", key)
            return True
    if notContains:
        log().info("dictionary of tags doesn't contain: %s", notContains)
        return True
    return False


def call_exiftool(dirpath: str, name: str, options: List = (), override=True) -> (str, str):
    fullname = os.path.join(dirpath, name)
    return call_exiftool_direct(options + [fullname], override)


def call_exiftool_direct(options: List = (), override=True) -> (str, str):
    path = getExiftoolPath()
    encoding_args = ["-charset", settings.encoding_format, "-charset", "FileName=" + settings.encoding_format]
    args = [path + "exiftool"] + encoding_args + options
    if override and options: args.append("-overwrite_original_in_place")
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = proc.communicate()
    out = out.decode(settings.encoding_format)
    err = err.decode("UTF-8")
    for line in err.split("\r\n"):
        if not line: continue
        log().warning(line)
    return out, err


def getExiftoolPath() -> str:
    if settings.exiftool_directory:
        path =  os.path.join(settings.exiftool_directory, '')
    else:
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '')
    if not isfile(path + "exiftool.exe"):
        raise FileNotFoundError(path + "exiftool.exe can not be found, please correct the directory of exiftool.exe")
    return path


def sort_dict_by_date_and_model(indict: Dict[str, list]) -> Dict[str, list]:
    date_mod_name = "File Modification Date/Time"
    date_org_name = "Date/Time Original"
    date_sub_name = "Sub Sec Time Original"
    model_name = "Camera Model Name"
    sortkeys = []
    if model_name in indict:
        sortkeys.append(model_name)
    if date_org_name in indict:
        sortkeys.append(date_org_name)
        if date_sub_name in indict:
            sortkeys.append(date_sub_name)
    if date_mod_name in indict:
        sortkeys.append(date_mod_name)
    return sort_dict(indict, sortkeys)


def sort_dict(indict: Dict[str, list], keys: list) -> Dict[str, list]:
    """example:
    sort indict by keys
    indict={"foo": [1, 3, 2], "bar": [8, 7, 6]}
    keys=["foo"]
    """

    indictkeys = list(indict.keys())
    cols = [indictkeys.index(key) for key in keys]
    lists = []
    for i in range(len(list(indict.values())[0])):
        vals = []
        for key in indictkeys:
            if key in indict:
                vals.append(indict[key][i])
            else:
                log().warning("sortDict_badkey %s" % key)
        lists.append(vals)

    for col in reversed(cols):
        lists = sorted(lists, key=operator.itemgetter(col))
    outdict = dict()
    for key in indict:
        outdict[key] = []
    for vals in lists:
        for i, val in enumerate(vals):
            outdict[indictkeys[i]].append(val)
    return outdict


def askToContinue():
    response = input("Do you want to continue ?")
    print(response)
    if 'n' in response:
        sys.exit('aborted')


def read_exiftag(dirpath: str, filename: str) -> Dict[str, str]:
    out, err = call_exiftool(dirpath, filename, [], False)
    return decode_exiftags(out)


def decode_exiftags(tags: str) -> Dict[str, str]:
    tagDict = OrderedDict()
    for tag in tags.split("\r\n"):
        keyval = tag.split(": ", 1)
        if not len(keyval) == 2: continue
        key = keyval[0].strip()
        val = keyval[1].strip()
        if key in tagDict: continue
        if (key, val) in ModelBase.unknownTags: val = ModelBase.unknownTags[(key, val)]
        if key == "Directory": val = val.replace("/", os.sep)
        tagDict[key] = val
    if not tagDict:
        log().error("no tags extracted from: %r", tags)
    return tagDict


def listsOfDicts_to_dictOfLists(listOfDicts: List[dict], ask=False) -> Dict[str, list]:
    """
    :type listOfDicts: list
    :param ask: whether to ask for continue when keys not occur
    """
    essential = ["File Name", "Directory", "File Modification Date/Time"]
    if not listOfDicts or not listOfDicts[0] or not listOfDicts[0].keys(): return OrderedDict()
    if has_not_keys(listOfDicts[0], essential): return OrderedDict()

    DictOfLists = OrderedDict()
    for key in listOfDicts[0]:
        val = listOfDicts[0][key]
        DictOfLists[key] = [val]

    badkeys = OrderedDict()
    for i, subdict in enumerate(listOfDicts[1:], start=1):
        for key in subdict:
            if not key in DictOfLists:
                badkeys[key] = i
                DictOfLists[key] = [""] * i
            DictOfLists[key].append(subdict[key])
        for key in DictOfLists:
            if not key in subdict:
                if not key in badkeys: badkeys[key] = 0
                badkeys[key] += 1
                DictOfLists[key].append("")

    if badkeys:
        for key in essential:
            if key in badkeys:
                raise AssertionError(key + ' is essential but not in one of the files')
        if ask:
            log().warning(
                "Following keys did not occur in every file. Number of not occurrences is listed in following dictionary: %r",
                badkeys)
            askToContinue()

    return DictOfLists
