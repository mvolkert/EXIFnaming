#!/usr/bin/env python3

"""
collection of Tag tools
"""

import os
from EXIFnaming.models import *


def getPath(Tagdict, i: int):
    if not all([x in Tagdict for x in ["Directory", "File Name"]]):
        print("Directory or File Name is not in Tagdict")
        return ""
    return os.path.join(Tagdict["Directory"][i], Tagdict["File Name"][i])

def create_model(Tagdict, i: int) -> ModelBase:
    if not 'Camera Model Name' in Tagdict:
        return NormalFile(Tagdict, i)
    model = Tagdict['Camera Model Name'][i]
    if model == "DMC_TZ101":
        return DMC_TZ101(Tagdict, i)
    if model == "DMC_TZ7":
        return DMC_TZ7(Tagdict, i)
    dateTimeKey = "Date/Time Original"
    if dateTimeKey in Tagdict and Tagdict[dateTimeKey][i]:
        return PhotoFile(Tagdict, i)
    return NormalFile(Tagdict, i)
