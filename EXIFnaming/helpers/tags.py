#!/usr/bin/env python3

"""
collection of Tag tools
"""

import os
from collections import OrderedDict
from typing import Callable

from EXIFnaming.models import *


def getPath(Tagdict, i: int):
    if not all([x in Tagdict for x in ["Directory", "File Name"]]):
        print("Directory or File Name is not in Tagdict")
        return ""
    return os.path.join(Tagdict["Directory"][i], Tagdict["File Name"][i])


ModelInit: OrderedDict[str, Callable[[dict, int], ModelBase]] = OrderedDict()
ModelInit['DMC_TZ101'] = lambda Tagdict, i: DMC_TZ101(Tagdict, i)
ModelInit['DMC_TZ7'] = lambda Tagdict, i: DMC_TZ7(Tagdict, i)


def create_model(Tagdict, i: int) -> ModelBase:
    dateTimeKey = "Date/Time Original"
    modelKey = "Camera Model Name"
    if modelKey in Tagdict:
        model = Tagdict[modelKey][i]
        if model in ModelInit:
            return ModelInit[model]()
    if dateTimeKey in Tagdict and Tagdict[dateTimeKey][i]:
        return PhotoFile(Tagdict, i)
    return NormalFile(Tagdict, i)
