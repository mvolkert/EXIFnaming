import datetime as dt
import os
from logging import Logger


def get_saves_dir(*subpath):
    create_program_dir()
    return os.path.join(".EXIFnaming", "saves", *subpath)


def get_gps_dir(*subpath):
    return os.path.join(".EXIFnaming", "gps", *subpath)


def get_info_dir(*subpath):
    create_program_dir()
    return os.path.join(".EXIFnaming", "info", *subpath)


def get_setexif_dir(*subpath):
    create_program_dir()
    return os.path.join(".EXIFnaming", "setexif", *subpath)


def get_log_dir(*subpath):
    create_program_dir()
    return os.path.join(".EXIFnaming", "log", *subpath)


def create_program_dir():
    mainpath = ".EXIFnaming"
    subdirs = ["saves", "gps", "info", "setexif", "log"]
    for subdir in subdirs:
        path = os.path.join(mainpath, subdir)
        os.makedirs(path, exist_ok=True)


def get_logger() -> Logger:
    if not get_logger.logger:
        import logging
        logFormatter = logging.Formatter("%(asctime)s  %(message)s")
        rootLogger = logging.getLogger()

        timestring = dt.datetime.now().strftime("%y%m%d%H%M")
        fileHandler = logging.FileHandler(get_log_dir(timestring + ".log"))
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)

        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        rootLogger.addHandler(consoleHandler)
        rootLogger.setLevel(10)
        get_logger.logger = rootLogger
    return get_logger.logger


get_logger.logger = None
