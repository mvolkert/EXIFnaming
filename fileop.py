import os

def getStandardDir():
    path = os.path.realpath(__file__)
    for i in range(3):
        path=os.path.dirname(path)
    return path + "\\"

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
    os.rename(dirpath + "\\" + filename, dirpath + "\\" + subpath + "\\" + filename)


def move(filename, oldpath, newpath):
    os.makedirs(newpath, exist_ok=True)
    os.rename(oldpath + "\\" + filename, newpath + "\\" + filename)


def renameInPlace(dirpath, oldFilename, newFilename):
    os.rename(dirpath + "\\" + oldFilename, dirpath + "\\" + newFilename)


def concatPathToStandard(path):
    if ":\\" not in path: path = getStandardDir() + path
    if not os.path.isdir(path):
        print(path, "is not a valid path")
        return None
    print(path)
    return path


def concatPathToSave(path):
    path = getSavesDir() + os.path.basename(path)
    os.makedirs(path, exist_ok=True)
    return path

def writeToFile(path,content):
    ofile = open(path, 'a')
    ofile.write(content)
    ofile.close()

def removeIfEmtpy(dirpath):
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