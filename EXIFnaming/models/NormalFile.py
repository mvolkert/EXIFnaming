from collections import OrderedDict

from EXIFnaming.models.ModelBase import ModelBase

__all__ = ["NormalFile"]


class NormalFile(ModelBase):
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

    def is_upward(self) -> bool:
        return False

    def get_scene_abbr_dict(self) -> OrderedDict:
        return NormalFile.SceneShort

    def get_creative_abbr_dict(self) -> OrderedDict:
        return NormalFile.CreativeShort

    def get_recMode(self) -> str:
        return ""

    def get_sequence_string(self) -> str:
        return ""

    def get_mode(self) -> str:
        return ""

    def get_date(self) -> str:
        dateTimeString = self.get_entry("File Modification Date/Time")
        dateTimeString = dateTimeString.rsplit("+")[0]
        return dateTimeString

    def get_sequence_number(self) -> int:
        return 0

    def get_model_abbr(self) -> str:
        return "F"

    def ignore_same_date(self) -> bool:
        return True
