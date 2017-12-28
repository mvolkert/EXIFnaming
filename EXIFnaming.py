"""
collection of Tag operations
works with: www.sno.phy.queensu.ca/~phil/exiftool/
exiftool.exe has to be in the same folder
"""

__author__ = "Marco Volkert"
__copyright__ = "Copyright 2017, Marco Volkert"
__email__ = "marco.volkert24@gmx.de"
__status__ = "Development"

from setTags import *
from getTags import *
from picture import *

# for reloading
from IPython import get_ipython

get_ipython().magic('reload_ext autoreload')
print('loaded collection of Tag operations')
