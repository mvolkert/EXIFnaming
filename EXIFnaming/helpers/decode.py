import sys
import subprocess
import os
from collections import OrderedDict
import datetime as dt
import operator

from EXIFnaming.helpers.constants import unknownTags

umlauts_dict = {
    '\\xc3\\xa4': 'ä',  # U+00E4	   \xc3\xa4
    '\\xc3\\xb6': 'ö',  # U+00F6	   \xc3\xb6
    '\\xc3\\xbc': 'ü',  # U+00FC	   \xc3\xbc
    '\\xc3\\x84': 'Ä',  # U+00C4	   \xc3\x84
    '\\xc3\\x96': 'Ö',  # U+00D6	   \xc3\x96
    '\\xc3\\x9c': 'Ü',  # U+00DC	   \xc3\x9c
    '\\xc3\\x9f': 'ß',  # U+00DF	   \xc3\x9f
}


def replace_umlauts(string):
    for x in umlauts_dict:
        if x in string:
            string=string.replace(x, umlauts_dict[x])
    return string

def readTags(inpath=os.getcwd(), includeSubdirs=False, Fileext=".JPG", skipdirs=[]):
    date_org_name = "Date/Time Original"

    print("process", countFilesIn(inpath, includeSubdirs, Fileext, skipdirs), "Files in ", inpath, "includeSubdirs:",
          includeSubdirs)
    askToContinue()

    timebegin = dt.datetime.now()
    ListOfDicts = []
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: break
        if os.path.basename(dirpath) in skipdirs: continue
        if countFiles(filenames, Fileext) == 0:
            print("  No matching files in ", dirpath.replace(inpath + "\\", ""))
            continue
        out = callExiftool(dirpath + "\\*" + Fileext, [], False)
        out = out[out.find("ExifTool Version Number"):]
        out_split = out.split("========")
        print("%4d tags extracted in " % len(out_split), dirpath.replace(inpath + "\\", ""))
        for tags in out_split:
            ListOfDicts.append(decodeTags(tags))

    outdict = listsOfDictsToDictOfLists(ListOfDicts)
    if not outdict: return {}
    outdict = sortDict(outdict, [date_org_name])
    for i in range(len(outdict["Directory"])):
        outdict["Directory"][i].replace("/", "\\")
    timedelta = dt.datetime.now() - timebegin
    print("elapsed time: %2d min, %2d sec" % (int(timedelta.seconds / 60), timedelta.seconds % 60))
    return outdict


def writeTags(inpath, options, includeSubdirs=False, Fileext=".JPG"):
    timebegin = dt.datetime.now()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: break
        n = countFiles(filenames, Fileext)
        if n == 0:
            print("  No matching files in ", dirpath.replace(inpath + "\\", ""))
            continue
        callExiftool(dirpath + "\\*" + Fileext, options, True)
        print("%4d tags written in   " % n, dirpath.replace(inpath + "\\", ""))
    timedelta = dt.datetime.now() - timebegin
    print("elapsed time: %2d min, %2d sec" % (int(timedelta.seconds / 60), timedelta.seconds % 60))


def has_not_keys(indict, keys):
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


def callExiftool(name, options=[], override=True):
    path = os.path.dirname(os.path.realpath(__file__)) + "\\"
    args = [path + "exiftool", name] + ["-charset","FileName=Latin2"]+ options
    if override and options: args.append("-overwrite_original_in_place")
    proc = subprocess.Popen(args, stdout=subprocess.PIPE)  # , shell=True
    (out, err) = proc.communicate()
    out = replace_umlauts(str(out))
    return out


def sortDict(indict: OrderedDict, keys: list):
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
            try:
                vals.append(indict[key][i])
            except:
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


def countFilesIn(inpath, includeSubdirs=False, Fileext="", skipdirs=[]):
    NFiles = 0
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: break
        if os.path.basename(dirpath) in skipdirs: continue
        for filename in filenames:
            if Fileext and not Fileext.lower() == filename.lower()[filename.rfind("."):]: continue

            NFiles += 1
    return NFiles


def countFiles(filenames, Fileext=".JPG"):
    return len([filename for filename in filenames if Fileext.lower() in filename.lower()])


def askToContinue():
    response = input("Do you want to continue ?")
    print(response)
    if 'n' in response:
        sys.exit('aborted')


def readTag(dirpath, filename):
    out = callExiftool(dirpath + "\\" + filename, [], False)
    return decodeTags(out)


def decodeTags(tags):
    date_org_name = "Date/Time Original"
    tagDict = OrderedDict()
    for tag in tags.split("\\r\\n"):
        keyval = tag.split(": ")
        if not len(keyval) == 2: continue
        key = keyval[0].strip()
        val = keyval[1].strip()
        if key in tagDict: continue
        if (key, val) in unknownTags: val = unknownTags[(key, val)]
        tagDict[key] = val
    if not tagDict:
        print("error: no tags extracted from:",tags)
    elif not date_org_name in tagDict:
        print("error:", date_org_name, "not in", tagDict)
    return tagDict


def listsOfDictsToDictOfLists(ListOfDicts):
    """

    :type ListOfDicts: list
    """
    essential = ["File Name", "Directory", "Date/Time Original"]
    if not ListOfDicts or not ListOfDicts[0] or not ListOfDicts[0].keys(): return {}
    if has_not_keys(ListOfDicts[0], essential): return {}

    DictOfLists = OrderedDict()
    for key in ListOfDicts[0]:
        val = ListOfDicts[0][key]
        DictOfLists[key] = [val]

    badkeys = OrderedDict()
    for i, subdict in enumerate(ListOfDicts[1:], start=1):
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
        askToContinue()

    return DictOfLists
