import datetime as dt
from collections import OrderedDict

__all__ = ["giveDatetime", "newdate", "dateformating", "find_dir_with_closest_time", "find_dir_with_closest_time_new", "print_firstlast_of_dirname"]


def giveDatetime(datestring="2000:01:01 00:00:00.000") -> dt.datetime:
    args = []
    for sub1 in datestring.split():
        for sub2 in sub1.split(":"):
            if "." in sub2:
                args.append(int(sub2.split(".")[0]))
                subsec = int(sub2.split(".")[1])
                if subsec < 999:
                    args.append(subsec * 1000)
                elif subsec < 999999:
                    args.append(subsec)
            else:
                args.append(int(sub2))
    time = dt.datetime(*args)
    return time


def newdate(time: dt.datetime, time_old: dt.datetime, use_day: bool = True) -> bool:
    # adjust datebreak at midnight
    timedelta = time - time_old
    timedelta_seconds = abs(timedelta.total_seconds())
    if not time_old.year == time.year or not time_old.month == time.month or (
            use_day and not time_old.day == time.day): newdate.dateswitch = True
    if timedelta_seconds > 3600. * 4 and newdate.dateswitch:
        newdate.dateswitch = False
        return True
    else:
        return False


newdate.dateswitch = False


def dateformating(time: dt.datetime, dateformat: str = "") -> str:
    if not time:
        time = dt.datetime.now()
    y = dateformat.count('Y')
    if y > 0: dateformat = dateformat.replace('Y' * y, str(time.year)[-y:])
    if dateformat.count('N') > 0:
        dateformating.numberofDates += 1
        dateformat = _replace_date_ID(dateformat, 'N', dateformating.numberofDates)
    dateformat = _replace_date_ID(dateformat, 'M', time.month)
    dateformat = _replace_date_ID(dateformat, 'D', time.day)
    dateformat = _replace_date_ID(dateformat, 'H', time.hour)
    dateformat = _replace_date_ID(dateformat, 'm', time.minute)
    dateformat = _replace_date_ID(dateformat, 's', time.second)
    dateformat = _replace_date_ID(dateformat, 'S', int(time.microsecond / 1000))
    return dateformat


dateformating.numberofDates = 0


def _replace_date_ID(dateformat: str, search_str: str, value: int) -> str:
    count = dateformat.count(search_str)
    if count == 0: return dateformat
    return dateformat.replace(search_str * count, ("%0" + str(count) + "d") % value)


def find_dir_with_closest_time(dirDict_firsttime: dict, dirDict_lasttime: dict, time: dt.datetime,
                               maxdelta=3600 * 24) -> str:
    deltaDict = OrderedDict()
    for firsttime, name in dirDict_firsttime.items():
        deltaseconds = abs((time - firsttime).total_seconds())
        deltaDict[deltaseconds] = name
    for lasttime, name in dirDict_lasttime.items():
        deltaseconds = abs((time - lasttime).total_seconds())
        deltaDict[deltaseconds] = name
    deltatime_min = min(deltaDict.keys())
    if deltatime_min < maxdelta:
        return deltaDict[deltatime_min]
    return time.strftime("%y%m%d_unrelated")


def find_dir_with_closest_time_new(dirDict: dict, time: dt.datetime,
                                   maxdelta=3600 * 24) -> str:
    deltaDict = OrderedDict()
    for name, time_tub in dirDict.items():
        deltafirst = (time - time_tub[0]).total_seconds()
        deltalast = (time - time_tub[1]).total_seconds()
        if 0 < deltafirst and deltalast < 0:
            return name
        deltaDict[abs(deltafirst)] = name
        deltaDict[abs(deltalast)] = name

    deltatime_min = min(deltaDict.keys())
    if deltatime_min < maxdelta:
        return deltaDict[deltatime_min]
    return time.strftime("%y%m%d_unrelated")


def print_firstlast_of_dirname(dirDict_firsttime: dict, dirDict_lasttime: dict):
    outDict = OrderedDict()
    for time, name in dirDict_firsttime.items():
        outDict[name] = time.strftime("%H:%M")
    for time, name in dirDict_lasttime.items():
        outDict.setdefault(name, "")
        outDict[name] += time.strftime(" - %H:%M \n")
    ofile = open("timetable.txt", 'a')
    for name, value in outDict.items():
        ofile.write(name + "\t" + value)
    ofile.close()
