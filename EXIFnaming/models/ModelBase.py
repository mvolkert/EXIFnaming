import os
from collections import OrderedDict

import numpy as np

import EXIFnaming.helpers.constants as c

__all__ = ["ModelBase"]

class ModelBase:
    TagNames = OrderedDict()

    TagNames['AF'] = ["AF Area Mode", "AF Assist Lamp", "Focus Mode", "Macro Mode", "Metering Mode"]
    TagNames['Mode'] = ["Advanced Scene Mode", "Advanced Scene Type", "Color Effect", "Contrast Mode", "HDR",
                        "Photo Style", "Scene Capture Type", "Scene Mode", "Scene Type", "Self Timer",
                        "Sensitivity Type", "Shooting Mode", "Shutter Type", "Sweep Panorama Direction",
                        "Sweep Panorama Field Of View", "Timer Recording"]
    TagNames['Series'] = ["Bracket Settings", "Burst Mode", "Burst Speed", "Sequence Number"]
    TagNames['Series'] += ["Dependent Image 1 Entry Number", "Dependent Image 2 Entry Number", "Number Of Images"]
    TagNames['Exposure'] = ["Exposure Compensation", "Exposure Mode", "Exposure Program", "Exposure Time"]
    TagNames['Flash'] = ["Flash", "Flash Bias", "Flash Curtain", "Flash Fired"]
    TagNames['Zoom'] = ["Field Of View", "Focal Length In 35mm Format", "F Number", "Hyperfocal Distance"]
    TagNames['Qual'] = ["ISO", "Light Source", "Light Value", "Long Exposure Noise Reduction", "Program ISO",
                        "Gain Control", "White Balance"]
    TagNames['Time'] = ["Date/Time Original", "Sub Sec Time Original"]
    TagNames['Rec'] = ["Audio", "Megapixels", "Video Frame Rate", "Image Quality"]
    TagNames['Rot'] = ["Orientation", "Rotation", "Camera Orientation", "Roll Angle", "Pitch Angle"]

    CreativeShort = OrderedDict()
    CreativeShort['Expressive'] = "EXPS"
    CreativeShort['Retro'] = "RETR"
    CreativeShort['Old Days'] = "OLD"
    CreativeShort['High Key'] = "HKEY"
    CreativeShort['Low Key'] = "LKEY"
    CreativeShort['Sepia'] = "SEPI"
    CreativeShort['Monochrome'] = "MONO"
    CreativeShort['Dynamic Monochrome'] = "D.MONO"
    CreativeShort['Rough Monochrome'] = "R.MONO"
    CreativeShort['Silky Monochrome'] = "S.MONO"
    CreativeShort['Impressive Art'] = "IART"
    CreativeShort['High Dynamic'] = "HDYN"
    CreativeShort['Cross Process'] = "XPRO"
    CreativeShort['Toy Effect'] = "TOY "
    CreativeShort['Toy Pop'] = "TOYP"
    CreativeShort['Bleach Bypass'] = "BLEA"
    CreativeShort['Miniature'] = "MINI"
    CreativeShort['Soft'] = "SOFT"
    CreativeShort['Fantasy'] = "FAN "
    CreativeShort['Star'] = "STAR"
    CreativeShort['Color Select'] = "CLR"
    CreativeShort['Sunshine'] = "SUN"

    SceneShort = OrderedDict()
    SceneShort['Clear Portrait'] = "POR1"
    SceneShort['Silky Skin'] = "POR2"
    SceneShort['Backlit Softness'] = "POR3"
    SceneShort['Clear in Backlight'] = "POR4"
    SceneShort['Relaxing Tone'] = "POR5"
    SceneShort['Sweet Child\'s Face'] = "POR6"
    SceneShort['Distinct Scenery'] = "LAN1"
    SceneShort['Bright Blue Sky'] = "LAN2"
    SceneShort['Romantic Sunset Glow'] = "SUN1"
    SceneShort['Vivid Sunset Glow'] = "SUN2"
    SceneShort['Glistening Water'] = "GLIT1"
    SceneShort['Clear Nightscape'] = "NIGHT1"
    SceneShort['Cool Night Sky'] = "NIGHT2"
    SceneShort['Warm Glowing Nightscape'] = "NIGHT3"
    SceneShort['Artistic Nightscape'] = "NIGHT4"
    SceneShort['Glittering Illuminations'] = "GLIT2"
    SceneShort['Handheld Night Shot'] = "NIGHT5"
    SceneShort['Clear Night Portrait'] = "NIGHT6"
    SceneShort['Soft Image of a Flower'] = "SOFT1"
    SceneShort['Appetizing Food'] = "SOFT2"
    SceneShort['Cute Desert'] = "SOFT3"
    SceneShort['Freeze Animal Motion'] = "FAST1"
    SceneShort['Clear Sports Shot'] = "FAST2"
    SceneShort['Monochrome'] = "SMONO"
    SceneShort['Panorama'] = "PANO"

    unknownTags = OrderedDict()
    unknownTags[("AF Area Mode", "Unknown (0 49)")] = "49-area"
    unknownTags[("AF Area Mode", "Unknown (240 0) ")] = "Tracking"
    unknownTags[("Contrast Mode", "Unknown (0x3)")] = "3"
    unknownTags[("Contrast Mode", "Unknown (0x5)")] = "5"
    unknownTags[("Contrast Mode", "Unknown (0x8)")] = "8"
    unknownTags[("Advanced Scene Mode", "Unknown (54 1)")] = "HS"
    unknownTags[("Advanced Scene Mode", "Unknown (60 7)")] = "4K"
    unknownTags[("Advanced Scene Mode", "Unknown (0 7)")] = "4K"
    unknownTags[("Scene Mode", "Unknown (60)")] = "4K"
    unknownTags[("Scene Mode", "Unknown (54)")] = "HS"

    def __init__(self, Tagdict: OrderedDict, i: int):
        self.Tagdict = Tagdict
        self.i = i
        self.filename = self.get_entry("File Name")
        self.dir = self.get_entry("Directory")

    def fix_unknownTags(self):
        for key in self.Tagdict:
            val = self.get_entry(key)
            if (key, val) in self.unknownTags:
                self.set_entry(key, self.unknownTags[(key, val)])

    def set_entry(self, key: str, val: str):
        self.Tagdict[key][self.i] = val

    def get_entry(self, entry: str):
        return self.Tagdict[entry][self.i]

    def check_entry(self, entry: str, value: str) -> bool:
        return self.get_entry(entry) == value

    def has(self, entry: str) -> bool:
        return entry in self.Tagdict and self.get_entry(entry)

    def is_4KBurst(self) -> bool:
        return self.check_entry("Image Quality", "4k Movie") and self.check_entry("Video Frame Rate", "29.97")

    def is_4KFilm(self) -> bool:
        return self.check_entry("Image Quality", "4k Movie")

    def is_HighSpeed(self) -> bool:
        return self.check_entry("Image Quality", "Full HD Movie") and self.check_entry("Advanced Scene Mode", "HS")

    def is_FullHD(self) -> bool:
        return self.check_entry("Image Quality", "Full HD Movie") and self.check_entry("Advanced Scene Mode", "Off")

    def is_series(self) -> bool:
        return self.check_entry("Burst Mode", "On")

    def is_Bracket(self) -> bool:
        return self.has("Bracket Settings") and not self.check_entry("Bracket Settings", "No Bracket")

    def is_stopmotion(self) -> bool:
        return self.check_entry("Timer Recording", "Stop-motion Animation")

    def is_timelapse(self) -> bool:
        return self.check_entry("Timer Recording", "Time Lapse")

    def is_4K(self) -> bool:
        return self.check_entry("Image Quality", '8.2')

    def is_creative(self) -> bool:
        return self.check_entry("Scene Mode", "Creative Control") or self.check_entry("Scene Mode", "Digital Filter")

    def is_scene(self) -> bool:
        return self.has("Scene Mode") and not self.check_entry("Scene Mode", "Off") and self.is_printable_scene()

    def is_HDR(self) -> bool:
        return self.has("HDR") and not self.check_entry("HDR", "Off")

    def is_sun(self) -> bool:
        return self.check_entry("Scene Mode", "Sun1") or self.check_entry("Scene Mode", "Sun2")

    def is_rotated_by(self, deg: int) -> bool:
        if deg == 0:
            return self.check_entry("Rotation", "Horizontal (normal)")
        elif deg == 90:
            return self.check_entry("Rotation", "Rotate 90 CW")
        elif deg == 270 or deg == -90:
            return self.check_entry("Rotation", "Rotate 270 CW")
        return False

    def is_upward(self) -> bool:
        width = self.get_entry("Image Width")
        height = self.get_entry("Image Height")
        return width < height

    def is_printable_scene(self) -> bool:
        return self.get_entry("Advanced Scene Mode") in self.get_scene_abbr_dict()

    def is_printable_creative(self) -> bool:
        return self.get_entry("Advanced Scene Mode") in self.get_creative_abbr_dict()

    def get_printable_scene(self) -> str:
        return self.get_scene_abbr_dict()[self.get_entry("Advanced Scene Mode")]

    def get_printable_creative(self) -> str:
        return self.get_creative_abbr_dict()[self.get_entry("Advanced Scene Mode")]

    def get_scene_abbr_dict(self) -> OrderedDict:
        return ModelBase.SceneShort

    def get_creative_abbr_dict(self) -> OrderedDict:
        return ModelBase.CreativeShort

    def get_recMode(self) -> str:
        if self.is_4KBurst():
            return "4KB"
        elif self.is_4KFilm():
            return "4K"
        elif self.is_HighSpeed():
            return "HS"
        elif self.is_FullHD():
            return "FHD"
        else:
            return ""

    def get_sequence_string(self) -> str:
        sequence_number = self.get_sequence_number()
        if self.is_Bracket(): return "B%d" % sequence_number
        if self.is_series():  return "S%02d" % sequence_number
        if self.is_stopmotion(): return "SM%03d" % sequence_number
        if self.is_timelapse(): return "TL%03d" % sequence_number
        if self.is_4K(): return "4KBSF"
        return ""

    def get_mode(self) -> str:
        if self.is_scene():
            return  self.get_printable_scene()
        elif self.is_creative():
            return self.get_printable_creative()
        elif self.is_HDR():
            return "HDR"
        return ""

    def get_date(self) -> str:
        dateTimeString = self.get_entry("Date/Time Original")
        if self.has("Sub Sec Time Original"):
            subsec = self.get_entry("Sub Sec Time Original")
            if subsec: dateTimeString += "." + subsec
        return dateTimeString

    def get_sequence_number(self) -> int:
        """
        sequence starts with 1; 0 means no sequence
        """
        if not self.has("Sequence Number"): return 0
        sequence_str = self.get_entry("Sequence Number")
        if np.chararray.isdigit(sequence_str): return int(sequence_str)
        return 0

    def get_path(self) -> str:
        return os.path.join(self.dir, self.filename)

    def get_model_abbr(self) -> str:
        if not self.has('Camera Model Name'): return ""
        model = self.get_entry('Camera Model Name')
        if model in c.CameraModelShort:
            return c.CameraModelShort[model]
        return model

    def ignore_same_date(self) -> bool:
        return False
