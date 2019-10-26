import os
import re
import shutil
from collections import OrderedDict
from typing import Iterable

import numpy as np

import EXIFnaming.helpers.constants as c
from EXIFnaming.helpers.misc import askToContinue
from EXIFnaming.helpers.program_dir import get_saves_dir, log
from EXIFnaming.helpers import settings

__all__ = ["count_files", "count_files_in", "is_invalid_path", "writeToFile", "renameInPlace", "moveFiles",
           "renameTemp", "move", "copyFilesTo", "get_filename_sorted_dirfiletuples", "moveToSubpath", "isfile",
           "moveBracketSeries", "moveSeries", "removeIfEmtpy", "get_relpath_depth", "move_media", "get_plain_filenames",
           "filterFiles", "file_has_ext", "remove_ext"]


def moveFiles(filenames, path: str):
    if os.path.isdir(path):
        print("directory already exists: ", path)
        return
    if len(filenames) == 0: return
    os.makedirs(path)
    for filename in filenames:
        rename_join((filename[0], filename[1]), (path, filename[1]))


def moveFilesToSubpath(filenames, dirpath, subpath):
    if len(filenames) == 0: return
    os.makedirs(os.path.join(dirpath, subpath), exist_ok=True)
    for filename in filenames:
        rename_join((dirpath, filename), (dirpath, subpath, filename))


def moveToSubpath(filename, dirpath, subpath):
    os.makedirs(os.path.join(dirpath, subpath), exist_ok=True)
    if not isfile(dirpath, filename): return
    rename_join((dirpath, filename), (dirpath, subpath, filename))


def move(filename, oldpath, newpath):
    os.makedirs(newpath, exist_ok=True)
    if not isfile(oldpath, filename): return
    if isfile(newpath, filename): return
    rename_join((oldpath, filename), (newpath, filename))


def renameInPlace(dirpath: str, oldFilename: str, newFilename: str):
    if oldFilename == newFilename: return
    rename_join((dirpath, oldFilename), (dirpath, newFilename))


def rename_join(path1: tuple, path2: tuple):
    os.rename(os.path.join(*path1), os.path.join(*path2))


def isfile(*path):
    return os.path.isfile(os.path.join(*path))


def save_tagdict(fileext: str, timestring: str, Tagdict: OrderedDict):
    np.savez_compressed(get_saves_dir("Tags" + fileext + timestring), Tagdict=Tagdict)


def writeToFile(path: str, content: str):
    ofile = open(path, 'a')
    ofile.write(content)
    ofile.close()


def removeIfEmtpy(dirpath: str):
    if len(os.listdir(dirpath)) == 1:
        if isfile(dirpath, "thumbs.db"): os.remove(os.path.join(dirpath, "thumbs.db"))
    if not os.listdir(dirpath): os.rmdir(dirpath)


def renameTemp(DirectoryList: list, FileNameList: list):
    if not len(DirectoryList) == len(FileNameList):
        log().error("error in renameTemp: len(DirectoryList)!=len(FileNameList)")
        return ""
    temppostfix = "temp"
    for i in range(len(FileNameList)):
        rename_join((DirectoryList[i], FileNameList[i]), (DirectoryList[i], FileNameList[i] + temppostfix))
    return temppostfix


def renameEveryTemp(inpath: str):
    temppostfix = "temp"
    if not os.path.isdir(inpath):
        print('not found directory: ' + inpath)
        return
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        for filename in filenames:
            rename_join((dirpath, filename), (dirpath, filename + temppostfix))
    return temppostfix


def moveBracketSeries(dirpath: str, filenames: list) -> list:
    main_old = "000"
    counter2_old = "0"
    BList = []
    other_filenames = []
    for filename in filenames:
        # example: filename="MS17-4_552B2.JPG"
        if not file_has_ext(filename, settings.image_types):
            other_filenames.append(filename)
            continue
        match = re.search('(\w+_[0-9]+)B([1-7])', filename)
        if match:
            main, counter2 = match.groups()
            if not main == main_old:
                moveFilesToSubpath(BList, dirpath, "B" + counter2_old)
                BList = []
            BList.append(filename)
            main_old = main
            counter2_old = counter2
        else:
            moveFilesToSubpath(BList, dirpath, "B" + counter2_old)
            BList = []
            other_filenames.append(filename)
    moveFilesToSubpath(BList, dirpath, "B" + counter2_old)
    return other_filenames


def moveSeries(dirpath: str, filenames: list, series_type="S", counter_match=r'([0-9]+)') -> list:
    other_filenames = []
    for filename in filenames:
        match = re.search('_([0-9]+)' + series_type + counter_match, filename)
        if match:
            moveToSubpath(filename, dirpath, series_type)
        else:
            other_filenames.append(filename)
    return other_filenames


def move_media(dirpath: str, filenames: list, name_searches: list, dest: str) -> list:
    other_filenames = []
    for filename in filenames:
        if any(name_search in filename for name_search in name_searches):
            moveToSubpath(filename, dirpath, dest)
        else:
            other_filenames.append(filename)
    return other_filenames


def copyFilesTo(files: list, path: str, prompt=True):
    print(len(files), "matches are to be copied to", path)
    if prompt: askToContinue()
    os.makedirs(path, exist_ok=True)
    for filename in files:
        shutil.copy2(filename, path)


def changeExtension(filename: str, ext: str):
    return filename[:filename.rfind(".")] + ext


def get_relpath_depth(inpath, dirpath):
    relpath = os.path.relpath(dirpath, inpath)
    if relpath == ".": return 0
    return len(relpath.split(os.sep))


def count_files_in(inpath: str, file_extensions: Iterable, skipdirs=()):
    NFiles = 0
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not settings.includeSubdirs and not inpath == dirpath: break
        if os.path.basename(dirpath) in skipdirs: continue
        NFiles += count_files(filenames, file_extensions)
    return NFiles


def count_files(filenames: [], file_extensions: Iterable):
    return len(filterFiles(filenames, file_extensions))


def filterFiles(filenames: [], file_extensions: Iterable):
    return [filename for filename in filenames if not file_extensions or file_has_ext(filename, file_extensions)]


def file_has_ext(filename: str, file_extensions: Iterable, ignore_case=True) -> bool:
    for fileext in file_extensions:
        if ignore_case:
            fileext = fileext.lower()
            filename = filename.lower()
        if fileext == filename[filename.rfind("."):]:
            return True
    return False


def remove_ext(filename: str):
    if filename is None:
        return ""
    return filename[:filename.rfind(".")]


def is_invalid_path(dirpath, blacklist=None, whitelist=None, regex=r"", start="") -> bool:
    inpath = os.getcwd()
    basename = os.path.basename(dirpath)
    relpath = str(os.path.relpath(dirpath, inpath))
    dirnames = relpath.split(os.sep)
    if not settings.includeSubdirs and not inpath == dirpath: return True
    if any(len(dirname) > 1 and dirname.startswith('.') for dirname in dirnames):  return True
    if '.EXIFnaming' in dirpath:  return True
    if blacklist and any(basename.startswith(blacklistEntry) for blacklistEntry in blacklist): return True
    if whitelist and not basename in whitelist: return True
    if regex and not re.search(regex, basename): return True
    if start and relpath.lower() < start.lower(): return True
    log().info(dirpath)
    return False


def get_plain_filenames(*path) -> list:
    plain_filenames = []
    for (dirpath, dirnames, filenames) in os.walk(os.path.join(*path)):
        plain_filenames += filenames
    return sorted(plain_filenames)


def get_filename_sorted_dirfiletuples(file_extensions, *path) -> list:
    out = []
    for (dirpath, dirnames, filenames) in os.walk(os.path.join(*path)):
        for filename in filenames:
            if not file_has_ext(filename, file_extensions): continue
            if is_not_standard_camera(filename): continue
            out.append((dirpath, filename))
    return sorted(out, key=lambda x: x[1])


def is_not_standard_camera(filename: str) -> bool:
    models = [model for model in c.CameraModelShort.values() if not model == ""]
    return any(model in filename for model in models)
