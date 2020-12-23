from collections import OrderedDict

from EXIFnaming.helpers import settings

__all__ = ["CameraModelShort", "RecModes", "hdr_algorithm", "tm_preset"]

CameraModelShort = OrderedDict()
CameraModelShort['DMC-TZ7'] = 'TZ7'
# CameraModelShort['DMC-TZ101'] = 'TZ101'
CameraModelShort['E4800'] = 'N'
CameraModelShort['SM-G900F'] = 'S5'
CameraModelShort['DCR-TRV25E'] = 'VS'
CameraModelShort['HDC-SD300'] = 'V'
#CameraModelShort['Canon EOS 450D'] = 'F'
#CameraModelShort['Canon EOS 5D Mark II'] = 'F'
CameraModelShort[settings.standard_kamera] = ''

RecModes = ["4KB", "4K", "HS", "FHD"]

hdr_algorithm = OrderedDict()
hdr_algorithm["E"] = "Entropy"
hdr_algorithm["Ld"] = "Luminance distance"
hdr_algorithm["LRGB"] = "Luminance RGB"
hdr_algorithm["C"] = "Colourmix"
hdr_algorithm["Ls"] = "Luminance sharpness"

tm_preset = OrderedDict()
tm_preset["Nb"] = "Natural balanced"
tm_preset["Ns"] = "Natural sharp"
tm_preset["Nbl"] = "Natural back light"
tm_preset["NBbl"] = "Natural Bright back light"
tm_preset["NDbl"] = "Natural Dark back light"
tm_preset["Nhd"] = "Natural highlight details"
tm_preset["Ndb"] = "Natural details brightened"
tm_preset["Npc"] = "Natural powerful colours"
tm_preset["Nso"] = "Natural soft"
tm_preset["Lb"] = "Landscape backlit"
tm_preset["Ls"] = "Landscape sunset"
tm_preset["Lpc"] = "Landscape powerful colours"
tm_preset["Lcad"] = "Landscape colour and detail"
tm_preset["LB"] = "Landscape Brilliant"
tm_preset["Afd"] = "Architecture fine detail"
tm_preset["Abi"] = "Architecture brighten interior"
tm_preset["Ss"] = "Surreal standard"
tm_preset["Spc"] = "Surreal powerful colours"
tm_preset["SE"] = "Surreal Extreme"
