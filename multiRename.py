#!/usr/bin/env python3

'''
collection of rename operations
'''

__author__ = "Marco Volkert"
__copyright__ = "Copyright 2017, Marco Volkert"
__email__ = "marco.volkert24@gmx.de"
__status__ = "Development"

# for reloading
from IPython import get_ipython

get_ipython().magic('reload_ext autoreload')
from tags_misc import *

print('loaded collection of rename operations')


def renameFolderCount(name="Name", start=1):
    inpath = renameFolderCount.path + name
    dirCounter = start
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if inpath == dirpath: continue
        fileCounter = 1
        for filename in filenames:
            newFilename = name + "_%02d_%02d" % (dirCounter, fileCounter) + ".jpg"
            os.rename(dirpath + "\\" + filename, inpath + "\\" + newFilename)
            fileCounter += 1
        dirCounter += 1


renameFolderCount.path = "F:\\Video\\z_Bearbeitung\\Neue Bilder und Videos\\Fotoserien\\"


def renameFolderCountMulti():
    inpath = renameFolderCount.path
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not inpath == dirpath: continue
        for dirname in dirnames:
            renameFolderCount(dirname, 1)


def renameIndexNorm(subpath=""):
    import re
    if not subpath == "": subpath = "\\" + subpath
    inpath = renameIndexNorm.path + subpath
    dirCounter = 1
    fileCounter = 1
    lastNameMain = ""
    lastNameMid = ""
    matchreg = r"^([-\w]+)_([0-9]+)_([0-9]+)"
    temppostfix = renameTemp2(inpath)
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        for filename in filenames:
            match = re.search(matchreg, filename)
            if not match: continue
            nameMain = match.group(1)
            nameMid = match.group(2)
            nameEnd = match.group(3)
            if not nameMain == lastNameMain:
                dirCounter = 1
                fileCounter = 1
            elif not nameMid == lastNameMid:
                dirCounter += 1
                fileCounter = 1
            else:
                fileCounter += 1
            newFilename = nameMain + "_%02d_%02d" % (dirCounter, fileCounter) + ".jpg"
            renameInPlace(dirpath, filename, newFilename)
            lastNameMain = nameMain
            lastNameMid = nameMid


renameIndexNorm.path = "F:\\Video\\z_Bearbeitung\\Bilder\\websites"


def renameIndexNorm2(subpath="", name="", start=1, write=False):
    import re
    if not subpath == "": subpath = "\\" + subpath
    inpath = renameIndexNorm2.path + subpath
    if not name == "":  name += "_"
    dirCounter = start - 1
    fileCounter = 1
    lastNameMid = ""
    matchreg = r"([0-9]+)_([0-9]+)."
    if write: temppostfix = renameTemp2(inpath)
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        print("renameIndexNorm2:", dirpath)
        for filename in filenames:
            match = re.search(matchreg, filename)
            if not match:
                print("no match", dirpath, filename)
                newFilename = filename[:filename.rfind(".")] + ".jpg"
                if write: renameInPlace(dirpath, filename, newFilename)
                continue
            nameMid = match.group(1)
            nameEnd = match.group(2)
            if not nameMid == lastNameMid:
                dirCounter += 1
                fileCounter = 1
            else:
                fileCounter += 1
            newFilename = name + "%02d_%02d" % (dirCounter, fileCounter) + ".jpg"
            print(dirpath, newFilename)
            if write: renameInPlace(dirpath, filename, newFilename)
            lastNameMid = nameMid
    # for (dirpath, dirnames, filenames) in os.walk(inpath):
    # for filename in filenames:
    # if "jpg"+temppostfix in filename[filename.rfind("."):]:
    #    newFilename=filename[:filename.rfind(".")]+".jpg"
    # renameInPlace(dirpath,filename,newFilename)

    return dirCounter


renameIndexNorm2.path = "F:\\Video\\z_Bearbeitung\\Bilder\\websites"


def renameIndexNorm2Multi(subpath=""):
    if not subpath == "": subpath = "\\" + subpath
    inpath = renameIndexNorm2.path + subpath
    dirCounter = 1
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not inpath == dirpath: continue
        for dirname in dirnames:
            print("renameIndexNorm2Multi:", dirname)
            renameIndexNorm2(dirname, dirname, dirCounter)


def renameIndexNorm2Multi2(subpath="", name=""):
    if not subpath == "": subpath = "\\" + subpath
    inpath = renameIndexNorm2.path + subpath
    dirCounter = 0
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not inpath == dirpath: continue
        for dirname in dirnames:
            dirCounter = renameIndexNorm2(subpath + "\\" + dirname, name, dirCounter + 1)
