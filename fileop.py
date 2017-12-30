import os
import re
import shutil

from misc import askToContinue

def getSavesDir():
    path = os.path.realpath(__file__)
    for i in range(2):
        path=os.path.dirname(path)
    return path + "\\saves\\"

def moveFiles(filenames, path: str):
    if os.path.isdir(path):
        print("directory already exists: ", path)
        return
    if len(filenames) == 0: return
    os.makedirs(path)
    for filename in filenames:
        os.rename(filename[0] + "\\" + filename[1], path + "\\" + filename[1])


def moveFilesToSubpath(filenames, dirpath, subpath):
    if len(filenames) == 0: return
    os.makedirs(dirpath + "\\" + subpath, exist_ok=True)
    for filename in filenames:
        os.rename(dirpath + "\\" + filename, dirpath + "\\" + subpath + "\\" + filename)


def moveToSubpath(filename, dirpath, subpath):
    os.makedirs(dirpath + "\\" + subpath, exist_ok=True)
    if not os.path.isfile(dirpath + "\\" + filename): return
    os.rename(dirpath + "\\" + filename, dirpath + "\\" + subpath + "\\" + filename)


def move(filename, oldpath, newpath):
    os.makedirs(newpath, exist_ok=True)
    if not os.path.isfile(oldpath + "\\" + filename): return
    if os.path.isfile(newpath + "\\" + filename): return
    os.rename(oldpath + "\\" + filename, newpath + "\\" + filename)


def renameInPlace(dirpath, oldFilename, newFilename):
    os.rename(dirpath + "\\" + oldFilename, dirpath + "\\" + newFilename)


def concatPathToSave(path):
    path = getSavesDir() + os.path.basename(path)
    os.makedirs(path, exist_ok=True)
    return path

def writeToFile(path,content):
    ofile = open(path, 'a')
    ofile.write(content)
    ofile.close()

def removeIfEmtpy(dirpath):
    if len(os.listdir(dirpath))==1:
        if os.path.isfile(dirpath+"\\thumbs.db"): os.remove(dirpath+"\\thumbs.db")
    if not os.listdir(dirpath): os.rmdir(dirpath)

def renameTemp(DirectoryList, FileNameList):
    if not len(DirectoryList) == len(FileNameList):
        print("error in renameTemp: len(DirectoryList)!=len(FileNameList)")
        return ""
    temppostfix = "temp"
    for i in range(len(FileNameList)):
        os.rename(DirectoryList[i] + "\\" + FileNameList[i], DirectoryList[i] + "\\" + FileNameList[i] + temppostfix)
    return temppostfix


def renameEveryTemp(inpath):
    temppostfix = "temp"
    if not os.path.isdir(inpath):
        print('not found directory: ' + inpath)
        return
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        for filename in filenames:
            os.rename(dirpath + "\\" + filename, dirpath + "\\" + filename + temppostfix)
    return temppostfix


def moveBracketSeries(dirpath,filenames):
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

def moveSeries(dirpath,filenames,series_type="S"):
    for filename in filenames:
        match = re.search('_([0-9]+)'+series_type+'([0-9]+)', filename)
        if match:
            moveToSubpath(filename, dirpath, series_type)


def copyFilesTo(files, path):
    print(len(files), "matches are to be copied to", path)
    askToContinue()
    os.makedirs(path, exist_ok=True)
    for filename in files:
        shutil.copy2(filename, path)


def changeExtension(filename,ext):
    return filename[:filename.rfind(".")] + ext