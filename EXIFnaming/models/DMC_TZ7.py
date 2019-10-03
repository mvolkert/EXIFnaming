from collections import OrderedDict

from EXIFnaming.models.ModelBase import ModelBase

__all__ = ["DMC_TZ7"]


class DMC_TZ7(ModelBase):
    TagNames = OrderedDict()

    TagNames['AF'] = ["AF Area Mode", "AF Assist Lamp", "Focus Mode", "Macro Mode", "Metering Mode"]
    TagNames['Mode'] = ["Advanced Scene Mode", "Advanced Scene Type", "Color Effect", "Contrast Mode"
                                                                                      "Scene Capture Type",
                        "Scene Mode", "Scene Type", "Self Timer", "Shooting Mode"]
    TagNames['Series'] = ["Bracket Settings", "Burst Mode", "Sequence Number"]
    TagNames['Series'] += ["Dependent Image 1 Entry Number", "Dependent Image 2 Entry Number", "Number Of Images"]
    TagNames['Exposure'] = ["Exposure Compensation", "Exposure Mode", "Exposure Program", "Exposure Time"]
    TagNames['Flash'] = ["Flash", "Flash Bias", "Flash Warning"]
    TagNames['Zoom'] = ["Field Of View", "Focal Length", "Focal Length In 35mm Format", "F Number",
                        "Hyperfocal Distance"]
    TagNames['Qual'] = ["ISO", "Light Source", "Light Value", "Program ISO",
                        "Gain Control", "White Balance"]
    TagNames['Time'] = ["Date/Time Original"]
    TagNames['Rec'] = ["Audio", "Megapixels", "Video Frame Rate", "Image Quality"]
    TagNames['Rot'] = ["Orientation", "Rotation"]

    CreativeShort = OrderedDict()

    SceneShort = OrderedDict()

    SceneShort['Scenery'] = "LAND"
    SceneShort['Sunset'] = "SUN"
    SceneShort['Fireworks'] = "FIRE1"
    SceneShort['Candlelight'] = "FIRE2"
    SceneShort['Night Scenery'] = "NIGHT"
    SceneShort['Panorama Assist'] = "PANO.A"

    unknownTags = OrderedDict()

    def __init__(self, Tagdict: OrderedDict, i: int):
        super().__init__(Tagdict, i)

    def is_4KBurst(self) -> bool:
        return False

    def is_4KFilm(self) -> bool:
        return False

    def is_HighSpeed(self) -> bool:
        return False

    def is_FullHD(self) -> bool:
        return False

    def is_series(self) -> bool:
        return self.check_entry("Burst Mode", "On")

    def is_Bracket(self) -> bool:
        return self.has("Burst Mode") and self.check_entry("Burst Mode", "Auto Exposure Bracketing (AEB)")

    def is_stopmotion(self) -> bool:
        return False

    def is_timelapse(self) -> bool:
        return False

    def is_4K(self) -> bool:
        return False

    def is_creative(self) -> bool:
        return False

    def is_scene(self) -> bool:
        return self.has("Scene Mode") and not self.check_entry("Scene Mode", "Off") and self.is_printable_scene()

    def is_HDR(self) -> bool:
        return False

    def is_sun(self) -> bool:
        return self.check_entry("Scene Mode", "Sunset")

    def get_scene_abbr_dict(self) -> OrderedDict:
        return DMC_TZ7.SceneShort

    def get_creative_abbr_dict(self) -> OrderedDict:
        return DMC_TZ7.CreativeShort
