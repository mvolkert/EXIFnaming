from collections import OrderedDict

from EXIFnaming.models.ModelBase import ModelBase

__all__ = ["ILCE_6300"]

class ILCE_6300(ModelBase):
    TagNames = OrderedDict()



    # Rotation: Horizontal (normal), Rotate 270 CW
    # Camera Orientation: Normal, Rotate CCW

    CreativeShort = OrderedDict()

    SceneShort = OrderedDict()

    unknownTags = OrderedDict()

    def __init__(self, Tagdict: OrderedDict, i: int):
        super().__init__(Tagdict, i)

    def is_series(self) -> bool:
        return self.check_entry("Release Mode", "Continuous")

    def get_scene_abbr_dict(self) -> OrderedDict:
        return ILCE_6300.SceneShort

    def get_creative_abbr_dict(self) -> OrderedDict:
        return ILCE_6300.CreativeShort

    def ignore_same_date(self) -> bool:
        return True

    def is_4KBurst(self) -> bool:
        return False

    def is_4KFilm(self) -> bool:
        return False

    def is_HighSpeed(self) -> bool:
        return False

    def is_FullHD(self) -> bool:
        return False

    def is_Bracket(self) -> bool:
        return False

    def is_stopmotion(self) -> bool:
        return False

    def is_timelapse(self) -> bool:
        return False
    def is_4K(self) -> bool:
        return False

    def is_creative(self) -> bool:
        return False

    def is_scene(self) -> bool:
        return False

    def is_HDR(self) -> bool:
        return False

    def is_sun(self) -> bool:
        return False