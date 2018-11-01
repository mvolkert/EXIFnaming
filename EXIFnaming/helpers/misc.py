import sys
import numpy as np

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
    filename = filename[:filename.rfind(".")]
    filename_splited = filename.split('_')
    if postfix_stay and len(filename_splited) > 1:
        found = False
        for subname in filename_splited:
            if found:
                postfix += "_" + subname
            elif np.chararray.isdigit(subname[0]) and np.chararray.isdigit(subname[-1]):
                found = True

    return postfix
