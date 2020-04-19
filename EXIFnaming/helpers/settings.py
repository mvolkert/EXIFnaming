#!/usr/bin/env python3
"""
Settings - modfy as you like

encoding_format: the encoding_format may change on different os - tested on windows
exiftool_directory: put here path/to/exiftool.exe (download: https://sno.phy.queensu.ca/~phil/exiftool/) if unset is same directory as settings
googlemaps_api_key: if you want to use placeinfo.py - you need a api key of google
loglevel: preset is DEBUG(10) if you want printed less - set it to INFO(20)
photographer: Here comes your name
"""
includeSubdirs = True
encoding_format = "latin"
image_types = (".JPG", ".jpg", ".tif", ".tiff", ".hdr", ".exr", ".ufo", ".fpx", ".RW2", ".Raw", ".gif")
video_types = (".MP4", ".mp4")
project_types = (".data", ".hdrProject", ".pto")
hdr_program = "franzis HDR projects"
panorama_program = "Hugin"
photographer = None
standard_kamera = ""
googlemaps_api_key = ""
exiftool_directory = r""
loglevel = 20
