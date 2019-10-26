#!/usr/bin/env python3
"""
Picture processing, no usage of exif infos

dependencies: scikit-image, opencv-python
"""
import os

from EXIFnaming.helpers.cv2op import is_blurry, are_similar
from EXIFnaming.helpers.fileop import moveToSubpath, isfile, is_invalid_path

__all__ = ["detectBlurry", "detectSimilar"]


def detectBlurry():
    """
    detects blurry images and put them in a sub directory named blurry
    """
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath): continue
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
        if is_invalid_path(dirpath): continue
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
