import os
import re
import shutil
import numpy as np
from collections import OrderedDict

from EXIFnaming.helpers.misc import askToContinue
from EXIFnaming.helpers.settings import includeSubdirs


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
    if not os.path.isfile(os.path.join(oldpath, filename)): return
    if isfile(newpath, filename): return
    rename_join((oldpath, filename), (newpath, filename))


def renameInPlace(dirpath: str, oldFilename: str, newFilename: str):
    if oldFilename == newFilename: return
    rename_join((dirpath, oldFilename), (dirpath, newFilename))


def rename_join(path1: tuple, path2: tuple):
    os.rename(os.path.join(*path1), os.path.join(*path2))


def isfile(*path):
    return os.path.isfile(os.path.join(*path))


def getSavesDir(*subpath):
    create_program_dir()
    return os.path.join(".EXIFnaming", "saves", *subpath)


def get_gps_dir(*subpath):
    return os.path.join(".EXIFnaming", "gps", *subpath)


def get_info_dir(*subpath):
    return os.path.join(".EXIFnaming", "info", *subpath)


def create_program_dir():
    mainpath = ".EXIFnaming"
    subdirs = ["saves", "gps", "info"]
    for subdir in subdirs:
        path = os.path.join(mainpath, subdir)
        os.makedirs(path, exist_ok=True)


def save_tagdict(fileext: str, timestring: str, Tagdict: OrderedDict):
    np.savez_compressed(getSavesDir("Tags" + fileext + timestring), Tagdict=Tagdict)


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
        print("error in renameTemp: len(DirectoryList)!=len(FileNameList)")
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
    counter_old = "000"
    counter2_old = "0"
    BList = []
    other_filenames = []
    for filename in filenames:
        # example: filename="MS17-4_552B2.JPG"
        if not ".JPG" in filename: continue
        match = re.search('_([0-9]+)B([1-7])', filename)
        if match:
            counter, counter2 = match.groups()
            if not counter == counter_old:
                moveFilesToSubpath(BList, dirpath, "B" + counter2_old)
                BList = []
            BList.append(filename)
            counter_old = counter
            counter2_old = counter2
        else:
            moveFilesToSubpath(BList, dirpath, "B" + counter2_old)
            BList = []
            other_filenames.append(filename)
    moveFilesToSubpath(BList, dirpath, "B" + counter2_old)
    return other_filenames


def moveSeries(dirpath: str, filenames: list, series_type="S") -> list:
    other_filenames = []
    for filename in filenames:
        match = re.search('_([0-9]+)' + series_type + '([0-9]+)', filename)
        if match:
            moveToSubpath(filename, dirpath, series_type)
        else:
            other_filenames.append(filename)
    return other_filenames


def move_media(dirpath: str, filenames: list, name_search=".MP4", dest="mp4") -> list:
    other_filenames = []
    for filename in filenames:
        if name_search in filename:
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


def count_files_in(inpath: str, file_extensions: tuple, skipdirs=()):
    NFiles = 0
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: break
        if os.path.basename(dirpath) in skipdirs: continue
        NFiles += count_files(filenames, file_extensions)
    return NFiles


def count_files(filenames: [], file_extensions: tuple):
    return len(filterFiles(filenames, file_extensions))


def filterFiles(filenames: [], file_extensions: tuple):
    return [filename for filename in filenames if not file_extensions or file_has_ext(filename, file_extensions)]


def file_has_ext(filename: str, file_extensions: tuple, ignore_case=True) -> bool:
    for fileext in file_extensions:
        if ignore_case:
            fileext = fileext.lower()
            filename = filename.lower()
        if fileext == filename[filename.rfind("."):]:
            return True
    return False

def is_invalid_path(dirpath, balcklist=None, whitelist=None, regex=r""):
    inpath = os.getcwd()
    basename = os.path.basename(dirpath)
    if not includeSubdirs and not inpath == dirpath: return True
    if basename.startswith('.'):  return True
    if '.EXIFnaming' in dirpath:  return True
    if balcklist and basename in balcklist: return True
    if whitelist and not basename in whitelist: return True
    if regex and not re.search(regex, basename): return True
    return False