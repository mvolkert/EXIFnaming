#!/usr/bin/env python3
"""
Does not uses Tags at all
"""
import datetime as dt
import os

import numpy as np

from EXIFnaming.helpers.cv2op import is_blurry, are_similar
from EXIFnaming.helpers.date import dateformating
from EXIFnaming.helpers.fileop import getSavesDir, renameInPlace, renameTemp, moveToSubpath, moveBracketSeries, \
    moveSeries, move, removeIfEmtpy, isfile, get_relpath_depth, move_media, copyFilesTo
from EXIFnaming.helpers.misc import askToContinue

includeSubdirs = True


def setIncludeSubdirs(toInclude=True):
    global includeSubdirs
    includeSubdirs = toInclude
    print("modifySubdirs:", includeSubdirs)


def renameBack(timestring="", Fileext=".JPG"):
    """
    rename back using backup in saves; change to directory you want o rename back
    :param timestring: time of backup
    :param Fileext: file extension
    :return:
    """
    dirname = getSavesDir()
    tagFile = os.path.join(dirname, "Tags" + Fileext + timestring + ".npz")
    if not timestring or os.path.isfile(tagFile):
        tagFiles = [x for x in os.listdir(dirname) if ".npz" in x]
        tagFile = os.path.join(dirname, tagFiles[-1])
    Tagdict = np.load(tagFile)["Tagdict"].item()
    temppostfix = renameTemp(Tagdict["Directory"], Tagdict["File Name new"])
    print(len(list(Tagdict.values())[0]))
    for i in range(len(list(Tagdict.values())[0])):
        filename = Tagdict["File Name new"][i] + temppostfix
        if not os.path.isfile(os.path.join(Tagdict["Directory"][i], filename)): continue
        filename_old = Tagdict["File Name"][i]
        renameInPlace(Tagdict["Directory"][i], filename, filename_old)
        Tagdict["File Name new"][i], Tagdict["File Name"][i] = Tagdict["File Name"][i], Tagdict["File Name new"][i]
    timestring = dateformating(dt.datetime.now(), "_MMDDHHmmss")
    np.savez_compressed(os.path.join(dirname, "Tags" + Fileext + timestring), Tagdict=Tagdict)


def detectBlurry():
    """
    detects blurry images and put them in a sub directory named blurry
    """
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: continue
        print(dirpath, len(dirnames), len(filenames))
        for filename in filenames:
            if not ".JPG" in filename: continue
            if not is_blurry(dirpath, filename, 30): continue
            moveToSubpath(filename, dirpath, "blurry")


def detectSimilar(similarity=0.9):
    """
    put similar pictures in same sub folder
    :param similarity: -1: completely different, 1: same
    """
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: continue
        print(dirpath, len(dirnames), len(filenames))
        dircounter = 0
        filenamesA = [filename for filename in filenames if ".JPG" in filename]
        for i, filenameA in enumerate(filenamesA):
            print(filenameA)
            notSimCounter = 0
            for filenameB in filenamesA[i + 1:]:
                if notSimCounter == 10: break
                if not isfile(dirpath, filenameA): continue
                if not isfile(dirpath, filenameB): continue
                if not are_similar(dirpath, filenameA, dirpath, filenameB, similarity):
                    notSimCounter += 1
                    continue
                notSimCounter = 0
                moveToSubpath(filenameB, dirpath, "%03d" % dircounter)
            if not os.path.isdir(os.path.join(dirpath, "%03d" % dircounter)): continue
            moveToSubpath(filenameA, dirpath, "%03d" % dircounter)
            dircounter += 1


def filterSeries():
    """
    put each kind of series in its own directory
    """
    inpath = os.getcwd()
    skipdirs = ["B" + str(i) for i in range(1, 8)] + ["S", "single", "HDR", "mp4", ".git", "tags"]

    print(inpath)
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: continue
        if os.path.basename(dirpath) in skipdirs: continue
        print(dirpath, len(dirnames), len(filenames))
        moveBracketSeries(dirpath, filenames)
        moveSeries(dirpath, filenames, "S")
        moveSeries(dirpath, filenames, "SM")
        moveSeries(dirpath, filenames, "TL")
        move_media(dirpath, filenames, ".MP4", "mp4")
        move_media(dirpath, filenames, "HDRT", "HDR")
        move_media(dirpath, filenames, ".JPG", "single")


def filterPrimary():
    """
    put single and B1 in same directory
    """
    import re
    inpath = os.getcwd()
    skipdirs = ["S", "single", "HDR", ".git", "tags"]

    print(inpath)
    foldersToMain(False, False, False, False, ["B" + str(i) for i in range(1, 8)])
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: continue
        if os.path.basename(dirpath) in skipdirs: continue
        print(dirpath, len(dirnames), len(filenames))
        moveSeries(dirpath, filenames, "S")
        moveSeries(dirpath, filenames, "SM")
        moveSeries(dirpath, filenames, "TL")
        for filename in filenames:
            match = re.search('_([0-9]+)B1', filename)
            if match: moveToSubpath(filename, dirpath, "primary")
        moveSeries(dirpath, filenames, "B")
        for filename in filenames:
            if not ".JPG" in filename: continue
            moveToSubpath(filename, dirpath, "primary")


def foldersToMain(all_folders=False, series=False, primary=False, blurry=False, dirs=None, one_level=True,
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
        print("A folder structure with a depth of %2d will be flattened" % deepest)
        askToContinue()
    elif deepest > 3:
        print("The folder structure has a depth of %2d" % deepest)
        print("chosen directory names:")
        print(reverseDirs)
        askToContinue()

    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not all_folders and not os.path.basename(dirpath) in reverseDirs: continue
        if dirpath == inpath: continue
        print(dirpath, len(dirnames), len(filenames))
        for filename in filenames:
            if not filename[-4:] in (".JPG", ".jpg", ".MP4", ".mp4"): continue
            if not_inpath and os.path.dirname(dirpath) == inpath: continue
            if one_level:
                destination = os.path.dirname(dirpath)
            else:
                destination = inpath
            move(filename, dirpath, destination)
        removeIfEmtpy(dirpath)


def renameHDR(mode="HDRT", ext=".jpg", folder="HDR"):
    """
    rename HDR pictures generated by FRANZIS HDR projects to a nicer form
    :param mode: name for HDR-Mode written to file
    :param ext: file extension
    :param folder: only files in folders of this name are renamed
    """
    import re

    matchreg = r"^([-\w]+)_([0-9]+)B1([-\w\s'&.]*)_2\3"
    matchreg2 = r"^([-a-zA-Z0-9]+)[-a-zA-Z_]*_([0-9]+)([-\w\s'&]*)_([0-9]+)\3"
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        print("Folder: " + dirpath)
        if not includeSubdirs and not inpath == dirpath: continue
        if not folder == "" and not folder == os.path.basename(dirpath): continue
        print("Folder: " + dirpath)
        for filename in filenames:
            if mode in filename: continue
            match = re.search(matchreg, filename)
            if not match:
                print("use reg2:", filename)
                match = re.search(matchreg2, filename)
            if match:
                filename_new = match.group(1) + "_" + match.group(2) + "_" + mode + match.group(3) + ext
                if os.path.isfile(os.path.join(dirpath, filename_new)):
                    i = 2
                    while os.path.isfile(os.path.join(dirpath, filename_new)):
                        filename_new = match.group(1) + "_" + match.group(2) + "_" + mode
                        filename_new += "%d" % i + match.group(3) + ext
                        i += 1
                        # print(filename_new)
                renameInPlace(dirpath, filename, filename_new)
            else:
                print("no match:", filename)


def renameTempBackAll():
    """
    rename temporary renamed files back
    """
    import re
    inpath = os.getcwd()
    matchreg = 'temp$'
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        for filename in filenames:
            match = re.search(matchreg, filename)
            if not match: continue
            newFilename = re.sub(matchreg, '', filename)
            renameInPlace(dirpath, filename, newFilename)
