import os
import re
import shutil

from EXIFnaming.helpers.misc import askToContinue


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


def renameInPlace(dirpath, oldFilename, newFilename):
    rename_join((dirpath, oldFilename), (dirpath, newFilename))


def rename_join(path1: tuple, path2: tuple):
    os.rename(os.path.join(*path1), os.path.join(*path2))


def isfile(*path):
    return os.path.isfile(os.path.join(*path))


def getSavesDir():
    path = ".EXIFnaming"
    os.makedirs(path, exist_ok=True)
    return path


def writeToFile(path, content):
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


def moveBracketSeries(dirpath: str, filenames: list):
    counter_old = "000"
    counter2_old = "0"
    BList = []
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
    moveFilesToSubpath(BList, dirpath, "B" + counter2_old)


def moveSeries(dirpath: str, filenames: list, series_type="S"):
    for filename in filenames:
        match = re.search('_([0-9]+)' + series_type + '([0-9]+)', filename)
        if match:
            moveToSubpath(filename, dirpath, series_type)

def move_media(dirpath: str, filenames: list, name_search=".MP4", dest="mp4"):
    for filename in filenames:
        if name_search in filename:
            moveToSubpath(filename, dirpath, dest)


def copyFilesTo(files: list, path: str, prompt = True):
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
