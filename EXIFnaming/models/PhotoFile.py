from collections import OrderedDict

from EXIFnaming.models.ModelBase import ModelBase

__all__ = ["PhotoFile"]


class PhotoFile(ModelBase):
    TagNames = OrderedDict()

    CreativeShort = OrderedDict()

    SceneShort = OrderedDict()

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

    def get_scene_abbr_dict(self) -> OrderedDict:
        return PhotoFile.SceneShort

    def get_creative_abbr_dict(self) -> OrderedDict:
        return PhotoFile.CreativeShort

    def get_recMode(self) -> str:
        return ""

    def get_sequence_string(self) -> str:
        return ""

    def get_mode(self) -> str:
        return ""

    def get_sequence_number(self) -> int:
        return 0
