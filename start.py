#!/usr/bin/env python3

# when using anaconda, copy this file to: C:\Users\[Name]\.ipython\profile_default\startup

# start ipython
exec(open("D:\ProgramData\Anaconda3\Scripts\ipython-script.py").read())

# imports for utilities often used in ipython
import time
import os
import sys
from collections import OrderedDict
from shutil import copyfile
from send2trash import send2trash

# for reloading of scripts
from IPython import get_ipython

ipython = get_ipython()
ipython.magic('load_ext autoreload')
ipython.magic('autoreload 2')
# for external reloading:
# %load_ext autoreload
# %autoreload 2

# change to working dir
os.chdir(r"F:\Bilder\bearbeitung\tags\EXIFnaming")

import EXIFnaming

os.chdir(r"F:\Bilder\bearbeitung\tags\EXIFnaming\EXIFnaming")
import getTags
import setTags
import picture

os.chdir(r"F:\Bilder\bearbeitung")
