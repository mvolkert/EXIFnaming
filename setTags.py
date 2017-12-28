import datetime as dt
from tags import *
from constants import SceneToTag
from decode import readTags, has_not_keys, callExiftool, askToContinue, writeTags, countFilesIn
from date import giveDatetime, dateformating

includeSubdirs = True


def setIncludeSubdirs(toInclude=True):
    global includeSubdirs
    includeSubdirs = toInclude
    print("modifySubdirs:", includeSubdirs)


def adjustDate(hours=-1, minutes=0, seconds=0, Fileext=".JPG"):
    inpath = os.getcwd()
    delta_t = dt.timedelta(hours=hours, minutes=minutes, seconds=seconds)
    Tagdict = readTags(inpath, includeSubdirs, Fileext)
    if has_not_keys(Tagdict, keys=["Directory", "File Name", "Date/Time Original"]): return
    leng = len(list(Tagdict.values())[0])
    for i in range(leng):
        time = giveDatetime(Tagdict["Date/Time Original"][i])
        newtime = time + delta_t
        timestring = dateformating(newtime, "YYYY:MM:DD HH:mm:ss")
        callExiftool(getPath(Tagdict, i), ["-DateTimeOriginal=" + timestring], True)


def addLocation(country="", city="", location=""):
    """
    country="Germany", city="Nueremberg", location="Location"
    """
    inpath = os.getcwd()
    options = []
    if country: options.append("-Country=" + country)
    if city: options.append("-City=" + city)
    if location: options.append("-Location=" + location)
    if not options: return
    writeTags(inpath, options, includeSubdirs, ".JPG")


def nameToExif():
    inpath = os.getcwd()
    timebegin = dt.datetime.now()
    print("process", countFilesIn(inpath, includeSubdirs, ""), "Files in ", inpath, "subdir:", includeSubdirs)
    askToContinue()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not includeSubdirs and not inpath == dirpath: break
        print(dirpath)
        for filename in filenames:
            filename, ext = filename.rsplit(".", 1)
            ext = "." + ext
            if ext not in [".JPG", ".jpg", ".MP4", ".mp4"]: continue
            filename_splited = filename.split('_')
            if len(filename_splited) == 0: continue
            id = ''
            title = ''
            state = ''
            found = False
            for subname in filename_splited:
                if found:
                    if subname in SceneToTag:
                        if SceneToTag[subname]: state += SceneToTag[subname] + "_"
                    else:
                        title += subname + "_"
                else:
                    id += subname + "_"
                    if (np.chararray.isdigit(subname[0]) and np.chararray.isdigit(subname[-1])) or \
                            subname[0] == "M" or "HDR" in subname: found = True
            options = []
            if id: options.append("-ImageDescription=" + id[:-1])
            if title: options.append("-Title=" + title[:-1])
            if state: options.append("-State=" + state[:-1])
            if not options: continue
            callExiftool(dirpath + "\\" + filename + ext, options, True)
    timedelta = dt.datetime.now() - timebegin
    print("elapsed time: %2d min, %2d sec" % (int(timedelta.seconds / 60), timedelta.seconds % 60))
