import sys

import numpy as np

from EXIFnaming.helpers.settings import video_types


def askToContinue():
    response = input("Do you want to continue ?")
    print(response)
    if 'n' in response:
        sys.exit('aborted')


def tofloat(string):
    import re

    if string.isdigit(): return float(string)

    matchreg = r"^([0-9]+)[.]([0-9]+)"
    match = re.match(matchreg, string)
    if match:
        return float(match.group(0))

    matchreg = r"^([0-9]+)[/]([0-9]+)"
    match = re.match(matchreg, string)
    if match:
        print(match)
        nominator = float(match.group(1))
        denominator = float(match.group(2))
        return nominator / denominator


def getPostfix(filename, postfix_stay=True):
    postfix = ''
    filename, ext = filename.rsplit('.', 1)
    filename_splited = filename.split('_')
    if postfix_stay and len(filename_splited) > 1:
        found = False
        for subname in filename_splited:
            if found:
                postfix += "_" + subname
            elif is_counter(subname, ext):
                found = True

    return postfix


def is_counter(name, ext=".JPG") -> bool:
    starts_and_ends_with_digit = (np.chararray.isdigit(name[0]) and np.chararray.isdigit(name[-1]))
    is_movie = ext in video_types
    is_movie_counter = is_movie and name[0] == "M" and np.chararray.isdigit(name[-1])
    return starts_and_ends_with_digit or is_movie_counter
