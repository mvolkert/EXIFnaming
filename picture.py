import datetime as dt
import itertools as it
import os
import numpy as np
from fileop import concatPathToSave,renameInPlace,renameTemp,moveToSubpath,moveBracketSeries,moveSeries,move,removeIfEmtpy
from decode import readTags, has_not_keys
from cv2op import is_blurry, are_similar

includeSubdirs = True


def setIncludeSubdirs(toInclude=True):
    global includeSubdirs
    includeSubdirs = toInclude
    print("modifySubdirs:", includeSubdirs)


def renameBack(Fileext=".JPG"):
    inpath = os.getcwd()
    dirname = concatPathToSave(inpath)
    Tagdict = np.load(dirname + "\\Tags" + Fileext + ".npz")["Tagdict"].item()
    temppostfix = renameTemp(Tagdict["Directory"], Tagdict["File Name"])
    for i in range(len(list(Tagdict.values())[0])):
        filename = Tagdict["File Name new"][i]
        if not os.path.isfile(Tagdict["Directory"][i] + "\\" + filename): continue
        filename_old = Tagdict["File Name"][i]
        renameInPlace(Tagdict["Directory"][i], filename + temppostfix, filename_old)
        Tagdict["File Name new"][i], Tagdict["File Name"][i] = Tagdict["File Name"][i], Tagdict["File Name new"][i]


def detectBlurry():
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: continue
        print(dirpath, len(dirnames), len(filenames))
        for filename in filenames:
            if not ".JPG" in filename: continue
            if not is_blurry(dirpath + "\\" + filename, 30): continue
            moveToSubpath(filename, dirpath, "blurry")


def detectSimilar():
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: continue
        print(dirpath, len(dirnames), len(filenames))
        dircounter = 0
        filenames = [filename for filename in filenames if ".JPG" in filename]
        for filenameA, filenameB in it.combinations(filenames, 2):
            print(filenameA, filenameB)
            if not are_similar(dirpath + "\\" + filenameA, dirpath + "\\" + filenameB, 0.9): continue
            dircounter += 1
            moveToSubpath(filenameA, dirpath, "%2d" % dircounter)
            moveToSubpath(filenameB, dirpath, "%2d" % dircounter)


def filterSeries():
    '''
    '''
    inpath = os.getcwd()
    skipdirs = ["B" + str(i) for i in range(1, 8)] + ["S", "single", "HDR", ".git", "tags"]

    print(inpath)
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: continue
        if os.path.basename(dirpath) in skipdirs: continue
        print(dirpath, len(dirnames), len(filenames))
        moveBracketSeries(dirpath, filenames)
        moveSeries(dirpath, filenames)
        for filename in filenames:
            if not ".JPG" in filename: continue
            moveToSubpath(filename, dirpath, "single")
    return


def filterSeries_back():
    inpath = os.getcwd()
    reverseDirs = ["B" + str(i) for i in range(1, 8)] + ["S", "single", "blurry"]

    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not os.path.basename(dirpath) in reverseDirs: continue
        print(dirpath, len(dirnames), len(filenames))
        for filename in filenames:
            if not ".JPG" in filename: continue
            move(filename, dirpath, os.path.dirname(dirpath))
        removeIfEmtpy(dirpath)


def renameHDR(mode="HDRT", ext=".jpg", folder="HDR"):
    import re

    matchreg = r"^([-\w]+)_([0-9]+)B1([-\w\s'&]*)_2\3"
    matchreg2 = r"^([-a-zA-Z0-9]+)[-a-zA-Z_]*_([0-9]+)([-\w\s'&]*)_([0-9]+)\3"
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        print("Folder: " + dirpath)
        if not includeSubdirs and not inpath == dirpath: continue
        if not folder == "" and not folder == dirpath.split("\\")[-1]: continue
        print("Folder: " + dirpath)
        for filename in filenames:
            if mode in filename: continue
            match = re.search(matchreg, filename)
            if not match:
                print("use reg2:", filename)
                match = re.search(matchreg2, filename)
            if match:
                filename_new = match.group(1) + "_" + match.group(2) + "_" + mode + match.group(3) + ext
                if os.path.isfile(dirpath + "\\" + filename_new):
                    i = 2
                    while os.path.isfile(dirpath + "\\" + filename_new):
                        filename_new = match.group(1) + "_" + match.group(2) + "_" + mode
                        filename_new += "%d" % i + match.group(3) + ext
                        i += 1
                        # print(filename_new)
                renameInPlace(dirpath, filename, filename_new)
            else:
                print("no match:", filename)


def rotate(mode="HDRT", sign=1, folder="HDR", override=True):
    """
    Rotation: Rotate 90 CW or Rotate 270 CW
    Rotate back
    """

    from PIL import Image

    NFiles = 0
    timebegin = dt.datetime.now()
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: continue
        if not folder == "" and not folder == dirpath.split("\\")[-1]: continue
        print(dirpath)
        Tagdict = readTags(dirpath, includeSubdirs)
        if has_not_keys(Tagdict, keys=["Directory", "File Name", "Rotation"]): return
        leng = len(list(Tagdict.values())[0])
        for i in range(leng):
            # Load the original image:
            if not mode in Tagdict["File Name"][i]: continue
            if Tagdict["Rotation"][i] == "Horizontal (normal)":
                continue
            else:
                name = Tagdict["Directory"][i] + "\\" + Tagdict["File Name"][i]
                print(Tagdict["File Name"][i])
                img = Image.open(name)
                if Tagdict["Rotation"][i] == "Rotate 90 CW":
                    img_rot = img.rotate(90 * sign, expand=True)
                elif Tagdict["Rotation"][i] == "Rotate 270 CW":
                    img_rot = img.rotate(-90 * sign, expand=True)
                else:
                    continue
                NFiles += 1
                if not override: name = name[:name.rfind(".")] + "_rot" + name[name.rfind("."):]
                img_rot.save(name, 'JPEG', quality=99, exif=img.info['exif'])

    timedelta = dt.datetime.now() - timebegin
    print("rotated %3d files in %2d min, %2d sec" % (NFiles, int(timedelta.seconds / 60), timedelta.seconds % 60))
