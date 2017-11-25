#!/usr/bin/env python3
#exec(open("./start.py").read())
exec(open("D:\ProgramData\Anaconda3\Scripts\ipython-script.py").read())
import time
import os
from os import listdir,rename,walk
from os.path import join,getmtime
import sys
from collections import OrderedDict
from shutil import copyfile
from send2trash import send2trash

#for reloading
from IPython import get_ipython
ipython = get_ipython()
ipython.magic('load_ext autoreload')
ipython.magic('autoreload 2')
#for external reloading:     
#%load_ext autoreload
#%autoreload 2