from collections import OrderedDict
from EXIFnaming.models.ModelBase import ModelBase


class PhotoFile(ModelBase):
    TagNames = OrderedDict()

    CreativeShort = OrderedDict()

    SceneShort = OrderedDict()

    unknownTags = OrderedDict()


    def __init__(self, Tagdict: OrderedDict, i: int):
        super().__init__(Tagdict, i)

    def is_4KBurst(self):
        return False

    def is_4KFilm(self):
        return False

    def is_HighSpeed(self):
        return False

    def is_FullHD(self):
        return False

    def is_series(self):
        return False

    def is_Bracket(self):
        return False

    def is_stopmotion(self):
        return False

    def is_timelapse(self):
        return False

    def is_4K(self):
        return False

    def is_creative(self):
        return False

    def is_scene(self):
        return False

    def is_HDR(self):
        return False

    def is_sun(self):
        return False

    def get_scene_abbr_dict(self) -> OrderedDict:
        return PhotoFile.SceneShort

    def get_creative_abbr_dict(self) -> OrderedDict:
        return PhotoFile.CreativeShort


    def get_recMode(self):
        return ""

    def get_sequence_string(self, SequenceNumber: int) -> str:
        return ""

    def get_mode(self):
        return ""

    def get_SequenceNumber(self):
        return 0

