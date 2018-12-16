from collections import OrderedDict

from EXIFnaming.helpers.settings import standard_kamera

CameraModelShort = OrderedDict()
CameraModelShort['DMC-TZ7'] = 'TZ7'
CameraModelShort['SM-G900F'] = 'S5'
CameraModelShort[standard_kamera] = ''

RecModes = ["4KB", "4K", "HS", "FHD"]

hdr_algorithm = OrderedDict()
hdr_algorithm["E"] = "Entropy"
hdr_algorithm["Ld"] = "Luminance distance"
hdr_algorithm["C"] = "Colourmix"
hdr_algorithm["Ls"] = "Luminance sharpness"

tm_preset = OrderedDict()
tm_preset["Nb"] = "Natural balanced"
tm_preset["Npc"] = "Natural powerful colours"
tm_preset["Lpc"] = "Landscape powerful colours"
tm_preset["Ls"] = "Landscape sunset"
tm_preset["Spc"] = "Surreal powerful colours"
tm_preset["SE"] = "Surreal Extreme"
