import datetime as dt
import os
from logging import Logger
from typing import Tuple

from EXIFnaming.helpers.settings import loglevel

__all__ = ["log", "get_saves_dir", "get_gps_dir", "get_info_dir", "get_setexif_dir", "get_log_dir", "log_function_call",
           "log_function_call_debug"]



def get_saves_dir(*subpath):
    program_dir = create_program_dir()
    return os.path.join(program_dir, "saves", *subpath)


def get_gps_dir(*subpath):
    program_dir = create_program_dir()
    return os.path.join(program_dir, "gps", *subpath)


def get_info_dir(*subpath):
    program_dir = create_program_dir()
    return os.path.join(program_dir, "info", *subpath)


def get_setexif_dir(*subpath):
    program_dir = create_program_dir()
    return os.path.join(program_dir, "setexif", *subpath)


def get_log_dir(*subpath):
    program_dir = create_program_dir()
    return os.path.join(program_dir, "log", *subpath)


def create_program_dir():
    if not create_program_dir.dir:
        mainpath = ".EXIFnaming"
        program_path = os.path.join(os.getcwd(), mainpath)

        subdirs = ["saves", "gps", "info", "setexif", "log"]
        for subdir in subdirs:
            path = os.path.join(mainpath, subdir)
            os.makedirs(path, exist_ok=True)
        create_program_dir.dir = program_path
    return create_program_dir.dir


create_program_dir.dir = None


def log() -> Logger:
    directory = os.getcwd()
    if not log.logger or not log.dir == directory:
        log.dir = directory

        import logging
        logFormatter = logging.Formatter("%(asctime)s  %(message)s")
        rootLogger = logging.getLogger()

        if log.logger:
            log.logger.handlers.pop()
        else:
            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(logFormatter)
            rootLogger.addHandler(consoleHandler)

        timestring = dt.datetime.now().strftime("%y%m%d%H%M")
        fileHandler = logging.FileHandler(get_log_dir(timestring + ".log"))
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)

        rootLogger.setLevel(loglevel)
        log.logger = rootLogger
    return log.logger


log.logger = None
log.dir = None


def log_function_call(function_name: str, *parameters):
    parameter_str = _join_params(parameters)
    log().info("call %s(%s)", function_name, parameter_str)


def log_function_call_debug(function_name: str, *parameters):
    parameter_str = _join_params(parameters)
    log().debug("call %s(%s)", function_name, parameter_str)


def _join_params(parameters: Tuple) -> str:
    parameters = [str(parameter) for parameter in parameters]
    return ", ".join(parameters)
