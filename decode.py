import sys
import subprocess
import os
from collections import OrderedDict
import datetime as dt
import operator
from constants import unknownTags
from fileop import concatPathToStandard


def readTags(inpath=os.getcwd(), subdir=False, Fileext=".JPG"):
    date_org_name = "Date/Time Original"
    inpath = concatPathToStandard(inpath)

    print("process", countFilesIn(inpath,subdir,Fileext), "Files in ", inpath, "subdir:", subdir)
    askToContinue()

    timebegin = dt.datetime.now()
    ListOfDicts = []
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not subdir and not inpath == dirpath: break
        if countFiles(filenames,Fileext) == 0:
            print("  No matching files in ", dirpath.replace(inpath + "\\", ""))
            continue
        out = callExiftool(dirpath + "\\*" + Fileext, [], False)
        out = out[out.find("ExifTool Version Number"):]
        out_split = out.split("========")
        print("%4d tags extracted in " % len(out_split), dirpath.replace(inpath + "\\", ""))
        for tags in out_split:
            ListOfDicts.append(decodeTags(tags))

    outdict = listsOfDictsToDictOfLists(ListOfDicts)
    outdict = sortDict(outdict, [date_org_name])
    for i in range(len(outdict["Directory"])):
        outdict["Directory"][i].replace("/", "\\")
    timedelta = dt.datetime.now() - timebegin
    print("elapsed time: %2d min, %2d sec" % (int(timedelta.seconds / 60), timedelta.seconds % 60))
    return outdict

def has_not_keys(indict, keys):
    if not keys: return True
    notContains=[]
    for key in keys:
        if not key in indict:
            notContains.append(key)
            print(key + " not in dict")
            return True
    if notContains:
        print("dictionary of tags doesn't contain ",notContains)
        return True
    return False

def callExiftool(name, options=[], override=True):
    args = ["exiftool", name] + options
    if override: args.append("-overwrite_original_in_place")
    proc = subprocess.Popen(args, stdout=subprocess.PIPE)  # , shell=True
    (out, err) = proc.communicate()
    return str(out)

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

def countFilesIn(inpath, subdir=False, Fileext=".JPG" ):
    NFiles = 0
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        for filename in filenames:
            if not Fileext.lower() == filename.lower()[filename.rfind("."):]: continue
            if not subdir and not inpath == dirpath: continue
            NFiles += 1
    return NFiles

def countFiles(filenames, Fileext=".JPG" ):
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
    if not date_org_name in tagDict:
        print("error:", date_org_name, "not in", tagDict)
    return tagDict


def listsOfDictsToDictOfLists(ListOfDicts):
    """

    :type ListOfDicts: list
    """
    essential= ["File Name","Directory","Date/Time Original"]
    if not ListOfDicts or not ListOfDicts[0] or not ListOfDicts[0].keys(): return {}
    if has_not_keys(ListOfDicts[0],essential): return {}

    DictOfLists=OrderedDict()
    for key in ListOfDicts[0]:
        val=ListOfDicts[0][key]
        DictOfLists[key] = [val]

    badkeys=OrderedDict()
    for i,subdict in enumerate(ListOfDicts[1:],start=1):
        for key in subdict:
            if not key in DictOfLists:
                badkeys[key] = i
                DictOfLists[key] = [""]*i
            DictOfLists[key].append(subdict[key])
        for key in DictOfLists:
            if not key in subdict:
                if not key in badkeys: badkeys[key]=0
                badkeys[key] += 1
                DictOfLists[key].append("")

    if badkeys:
        for key in essential:
            if key in badkeys:
                raise AssertionError(key + ' is essential but not in one of the files')
        print("Following keys did not occur in every file. Number of not occurrences is listed in following dictionary:", badkeys)
        askToContinue()

    return DictOfLists
