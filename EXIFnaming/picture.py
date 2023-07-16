#!/usr/bin/env python3
"""
Picture processing, no usage of exif infos

dependencies: scikit-image, opencv-python, PIL
"""
import os
import re

from PIL import Image

from EXIFnaming.helpers.cv2op import is_blurry, are_similar
from EXIFnaming.helpers.fileop import moveToSubpath, isfile, is_invalid_path, file_has_ext

__all__ = ["detect_blurry", "detect_similar", "resize"]

from EXIFnaming.helpers.program_dir import log_function_call
from EXIFnaming.helpers.tag_conversion import FilenameAccessor


def detect_blurry():
    """
    detects blurry images and put them in a sub directory named blurry
    """
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath): continue
        print(dirpath, len(dirnames), len(filenames))
        for filename in filenames:
            if not file_has_ext(filename, ('.JPG', ".jpg")): continue
            if not is_blurry(dirpath, filename, 30): continue
            moveToSubpath(filename, dirpath, "blurry")


def detect_similar(similarity=0.9):
    """
    put similar pictures in same sub folder
    :param similarity: -1: completely different, 1: same
    """
    inpath = os.getcwd()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath): continue
        print(dirpath, len(dirnames), len(filenames))
        dircounter = 0
        filenamesA = [filename for filename in filenames if file_has_ext(filename, ('.JPG', ".jpg"))]
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


def resize(size=(128, 128)):
    """
    resize to icon like image
    :param size: size of resulting image
    """
    log_function_call(resize.__name__, size)

    inpath = os.getcwd()
    dest = os.path.join(inpath, "SMALL")
    os.mkdir(dest)
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, blacklist=["SMALL"]): continue
        for filename in filenames:
            if not file_has_ext(filename, ('.JPG', ".jpg")): continue
            # Load the original image:
            accessor = FilenameAccessor(filename)
            img = Image.open(os.path.join(dirpath, filename))
            img.thumbnail(size, Image.ANTIALIAS)
            accessor.processes.append("SMALL")
            outfile = os.path.join(dest, accessor.sorted_filename())
            img.save(outfile, 'JPEG', quality=90)


def make_gif(duration: int = 100):
    inpath = os.getcwd()
    os.makedirs("gif", exist_ok=True)
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, whitelist=["S"]): continue
        pictures = []
        last_main = ""
        last_end = ""
        for filename in filenames:
            if not file_has_ext(filename, ('.JPG', ".jpg")): continue
            match = re.search(r'(.+[0-9]+)S([0-9]+)_(.+)\.(JPG|jpg)', filename)
            if match:
                main = match.group(1)
                if last_main == main:
                    pictures.append(filename)
                else:
                    if len(pictures) > 2:
                        frames = [Image.open(dirpath + os.sep + image) for image in pictures]
                        frame_one = frames[0]
                        frames_resized = []
                        for frame in frames:
                            frame = frame.resize((int(frame_one.width / 2), int(frame_one.height / 2)))
                            frames_resized.append(frame)
                        frames_resized[0].save(f"{last_main}_{last_end}.gif", format="GIF", append_images=frames_resized[1:],
                                               save_all=True, duration=duration, loop=0)
                    last_main = main
                    last_end = match.group(3)
                    pictures = [filename]


def make_gif_per_dir(duration: int = 100):
    inpath = os.getcwd()
    os.makedirs("gif_dir", exist_ok=True)
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if is_invalid_path(dirpath, whitelist=["S"]): continue
        baseDir = dirpath.replace(inpath, '').split(os.sep)[1]
        if len(filenames) < 2: continue
        frames = [Image.open(dirpath + os.sep + image) for image in filenames]
        frame_one = frames[0]
        frames_resized = []
        for frame in frames:
            frame = frame.resize((int(frame_one.width / 2), int(frame_one.height / 2)))
            frames_resized.append(frame)
        frames_resized[0].save(f"gif_dir/{baseDir}.gif", format="GIF", append_images=frames_resized[1:],
                               save_all=True, duration=duration, loop=0)
