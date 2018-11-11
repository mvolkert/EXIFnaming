import operator
import os
import subprocess
import sys
from collections import OrderedDict

from sortedcollections import OrderedSet

from EXIFnaming.helpers.constants import unknownTags
from EXIFnaming.helpers.fileop import count_files, count_files_in
from EXIFnaming.helpers.measuring_tools import Clock
from EXIFnaming.helpers.settings import includeSubdirs, encoding_format, file_types


def read_exiftags(inpath=os.getcwd(), fileext=".JPG", skipdirs=(), ask=True):
    if fileext:
        selected_file_types = (fileext,)
    else:
        selected_file_types = file_types
    print("process", count_files_in(inpath, selected_file_types, skipdirs), fileext, "Files in ", inpath,
          "includeSubdirs:", includeSubdirs)
    if ask: askToContinue()

    clock = Clock()
    ListOfDicts = []
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: break
        if os.path.basename(dirpath).startswith('.'): continue
        if os.path.basename(dirpath) in skipdirs: continue
        if count_files(filenames, selected_file_types) == 0:
            print("  No matching files in ", os.path.relpath(dirpath, inpath))
            continue
        out = call_exiftool(dirpath, "*" + fileext, [], False)
        out = out[out.find("ExifTool Version Number"):]
        out_split = out.split("========")
        print("%4d tags extracted in " % len(out_split), os.path.relpath(dirpath, inpath))
        for tags in out_split:
            ListOfDicts.append(decode_exiftags(tags))

    outdict = listsOfDicts_to_dictOfLists(ListOfDicts, ask)
    if not outdict: return {}
    outdict = sort_dict_by_date(outdict)
    clock.finish()
    return outdict


def write_exiftags(tagDict: dict, inpath=os.getcwd(), options=()):
    clock = Clock()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: break
        n = count_files(filenames, file_types)
        if n == 0:
            print("  No matching files in ", os.path.relpath(dirpath, inpath))
            continue
        all_options = list(options) + tag_dict_to_options(tagDict)
        call_exiftool(dirpath, "*", all_options, True)
        print("%4d tags written in   " % n, os.path.relpath(dirpath, inpath))
    clock.finish()


def write_exiftag(tagDict: dict, inpath=os.getcwd(), filename="", options=("-ImageDescription=", "-XPComment=")):
    all_options = list(options) + tag_dict_to_options(tagDict)
    call_exiftool(inpath, filename, all_options, True)


def tag_dict_to_options(data: dict):
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


def has_not_keys(indict: dict, keys: list):
    if not keys: return True
    notContains = []
    for key in keys:
        if not key in indict:
            notContains.append(key)
            print(key + " not in dict")
            return True
    if notContains:
        print("dictionary of tags doesn't contain ", notContains)
        return True
    return False


def call_exiftool(dirpath: str, name: str, options=(), override=True) -> str:
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "")
    fullname = os.path.join(dirpath, name)
    encoding_args = ["-charset", encoding_format, "-charset", "FileName=" + encoding_format]
    args = [path + "exiftool", fullname] + encoding_args + options
    if override and options: args.append("-overwrite_original_in_place")
    proc = subprocess.Popen(args, stdout=subprocess.PIPE)  # , shell=True
    (out, err) = proc.communicate()
    out = out.decode(encoding_format)
    return out


def sort_dict_by_date(indict: OrderedDict):
    sortkeys = ["Date/Time Original"]
    if "Sub Sec Time Original" in indict: sortkeys.append("Sub Sec Time Original")
    return sort_dict(indict, sortkeys)


def sort_dict(indict: OrderedDict, keys: list):
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
                print("sortDict_badkey", key)
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


def read_exiftag(dirpath: str, filename: str):
    out = call_exiftool(dirpath, filename, [], False)
    return decode_exiftags(out)


def decode_exiftags(tags: str):
    date_org_name = "Date/Time Original"
    tagDict = OrderedDict()
    for tag in tags.split("\r\n"):
        keyval = tag.split(": ", 1)
        if not len(keyval) == 2: continue
        key = keyval[0].strip()
        val = keyval[1].strip()
        if key in tagDict: continue
        if (key, val) in unknownTags: val = unknownTags[(key, val)]
        if key == "Directory": val = val.replace("/", os.sep)
        tagDict[key] = val
    if not tagDict:
        print("error: no tags extracted from:", tags)
    elif not date_org_name in tagDict:
        print("error:", date_org_name, "not in", tagDict)
    return tagDict


def listsOfDicts_to_dictOfLists(listOfDicts: list, ask=True) -> OrderedDict:
    """

    :type listOfDicts: list
    :parm ask whether to ask for continue when keys not occur
    """
    essential = ["File Name", "Directory", "Date/Time Original"]
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
        print(
            "Following keys did not occur in every file. Number of not occurrences is listed in following dictionary:",
            badkeys)
        if ask: askToContinue()

    return DictOfLists
