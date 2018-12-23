#!/usr/bin/env python3

"""
collection of Tag tools
"""

import os
from collections import OrderedDict
from typing import Callable, Dict

from EXIFnaming.models import *

dateTimeKey = "Date/Time Original"
modelKey = "Camera Model Name"

def getPath(Tagdict, i: int):
    if not all([x in Tagdict for x in ["Directory", "File Name"]]):
        print("Directory or File Name is not in Tagdict")
        return ""
    return os.path.join(Tagdict["Directory"][i], Tagdict["File Name"][i])


ModelInit: Dict[str, Callable[[dict, int], ModelBase]] = OrderedDict()
ModelInit['DMC-TZ101'] = lambda Tagdict, i: DMC_TZ101(Tagdict, i)
ModelInit['DMC-TZ7'] = lambda Tagdict, i: DMC_TZ7(Tagdict, i)


def create_model(Tagdict, i: int) -> ModelBase:

    if modelKey in Tagdict:
        model = Tagdict[modelKey][i]
        if model in ModelInit:
            return ModelInit[model](Tagdict, i)
    if dateTimeKey in Tagdict and Tagdict[dateTimeKey][i]:
        return PhotoFile(Tagdict, i)
    return NormalFile(Tagdict, i)

def hasDateTime(Tagdict: dict) -> bool:
    return dateTimeKey in Tagdict and Tagdict[dateTimeKey]