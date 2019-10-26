import operator
import os
import re
from collections import OrderedDict
from typing import List

import numpy as np
from sortedcollections import OrderedSet

from EXIFnaming.helpers import constants as c, settings
from EXIFnaming.helpers.decode import read_exiftag
from EXIFnaming.helpers.program_dir import log
from EXIFnaming.helpers.tags import SceneModeAbbreviations

__all__ = ["FileMetaData", "Location", "add_dict", "FilenameAccessor", "FilenameBuilder"]


class Location:
    location_keys = ['Country', 'State', 'City', 'Location']
    tag_names = {'Country': ['Country', 'LocationCreatedCountryName'],
                 'State': ['State', 'LocationCreatedProvinceState'],
                 'City': ['City', 'LocationCreatedCity'],
                 'Location': ['Location', 'LocationCreatedSublocation']}

    def __init__(self, data=None, i=-1):
        self.location = OrderedDict()
        if data:
            if i > -1:
                self.update_via_tag_array(data, i)
            else:
                self.update(data)

    def update(self, data: dict):

        for key in Location.location_keys:
            if key in data and data[key]:
                if data[key] == "none":
                    self.location.pop(key, None)
                else:
                    self.location[key] = data[key]

    def update_via_tag_array(self, data: dict, i: int):

        for key in Location.location_keys:
            if key in data and data[key][i]:
                self.location[key] = data[key][i]

    def get_minor(self) -> list:
        out = []
        minor_keys = ["City", "Location"]
        for key in minor_keys:
            if not key in self.location: continue
            out.append(self.location[key])
        return out

    def to_tag_dict(self) -> dict:
        tag_dict = {}
        if self.location.keys():
            loc_tags = []
            for key in self.location:
                loc_tags.append(self.location[key])
                for tag_name in Location.tag_names[key]:
                    tag_dict[tag_name] = self.location[key]
            tag_dict['Keywords'] = loc_tags
            tag_dict['Subject'] = list(loc_tags)
        return tag_dict

    def __str__(self):
        out = ""
        for key in self.location:
            out += self.location[key] + ", "
        return out.strip(", ")


class FileMetaData:
    restriction_keys = ['directory', 'name_main', 'first', 'last', 'name_part']
    tag_setting_keys = ['title', 'tags', 'tags2', 'tags3', 'rating', 'description', 'gps']
    kown_keys = restriction_keys + tag_setting_keys + Location.location_keys
    linesep = " | "
    secondary_regex = re.compile(r"_[0-9]+[A-Z]+\d*[2-9]")

    def __init__(self, directory, filename):
        self.directory = directory
        self.filename = filename
        self.id = self.filename
        self.title = ""
        self.tags = []
        self.tags2 = []
        self.tags3 = []
        self.descriptions = []
        self.description_tree = OrderedDict()
        self.location = Location()
        self.rating = None
        self.gps = ()
        self.gps_exif = False
        self.tagDict = None
        self.filenameAccessor = FilenameAccessor(filename)
        self.main_name = self.filenameAccessor.pre
        self.counter = self.filenameAccessor.counter_main()
        self.has_changed = False

    def import_filename(self):
        self.id = self.filenameAccessor.identifier()
        self.tags = self.filenameAccessor.tags()
        self.tags2 = self.filenameAccessor.mapped_modes()
        match = FileMetaData.secondary_regex.search(self.id)
        if match:
            self.rating = 2
        else:
            self.rating = 3
        for process in self.filenameAccessor.processes:
            des = process_to_description(process)
            add_dict(self.description_tree, des)

    def import_fullname(self, startdir: str):
        self.id, self.tags = fullname_to_tag(self.directory, self.filenameAccessor.name, startdir)

    def import_exif(self, overwrite_gps=False):
        self.tagDict = read_exiftag(self.directory, self.filename)
        self.location.update(self.tagDict)
        if "Rating" in self.tagDict and int(self.tagDict["Rating"]) > 0:
            self.rating = self.tagDict["Rating"]

        if not overwrite_gps and "GPS Latitude" in self.tagDict and self.tagDict["GPS Latitude"]:
            self.gps_exif = True

        if "User Comment" in self.tagDict:
            user_comment = self.tagDict["User Comment"]
            user_comment_split = user_comment.split("..")
            user_comment_split = [string for line in user_comment_split for string in
                                  line.split(FileMetaData.linesep + ".")]
            pano_keys = ["Projection", "FOV", "Ev"]
            for entry in user_comment_split:
                if not ": " in entry: continue
                entry = entry.strip(FileMetaData.linesep)
                key, value = entry.split(": ", 1)
                if not key or not value: continue
                if key in FileMetaData.kown_keys: continue
                if key in pano_keys:
                    key = "PANO-" + key
                self.description_tree[key] = value

    def update(self, data: dict):
        def good_key(key: str):
            return key in data and data[key]

        if not self.passes_restrictions(data):
            return

        if good_key('title'): self.title = data['title']
        if good_key('tags'): self.tags += [tag for tag in data['tags'].split(', ') if tag]
        if good_key('tags2'): self.tags2 += [tag for tag in data['tags2'].split(', ') if tag]
        if good_key('tags3'): self.tags3 += [tag for tag in data['tags3'].split(', ') if tag]
        if good_key('gps') and not self.gps_exif: self.gps = data['gps'].split(', ')
        if good_key('rating'): self.rating = data['rating']
        if good_key('description'): self.descriptions.append(data['description'])
        self.location.update(data)

        for key in data:
            if not data[key] or key in FileMetaData.kown_keys: continue
            self.description_tree[key] = data[key]

    def passes_restrictions(self, data):
        def not_match_entry(key: str, func):
            return key in data and data[key] and not func(data[key])

        if not_match_entry('directory', lambda value: value in self.directory):
            return False
        if not_match_entry('name_main', lambda value: value == self.main_name):
            return False
        if not_match_entry('first', lambda value: value <= self.counter):
            return False
        if not_match_entry('last', lambda value: self.counter <= value):
            return False
        if not_match_entry('name_part', lambda value: value in self.filename):
            return False

        self.has_changed = True
        return True

    def _write_description_tree(self):
        if any(["HDR" in key or "TM" in key for key in self.description_tree]):
            self.description_tree["HDR-program"] = settings.hdr_program
        if any(["PANO" in key for key in self.description_tree]):
            self.description_tree["PANO-program"] = settings.panorama_program
        description_tree = OrderedDict()
        process_order = ["HDR", "TM", "PANO", ""]
        for key_part in process_order:
            process_subkeys = [key for key in self.description_tree if key_part in key]
            for key in process_subkeys:
                description_tree[key] = self.description_tree[key]
        description_formated = format_plain(description_tree)
        self.descriptions.append(description_formated)

    def _write_description_tags(self):
        tags = []
        if self.tags:
            tags.append(", ".join(self.tags))
        if str(self.location):
            tags.append(str(self.location))
        if self.tags2:
            tags.append(", ".join(self.tags2))
        if tags:
            self.descriptions.append((FileMetaData.linesep + "\n").join(tags))

    def to_tag_dict(self) -> dict:
        if not self.title:
            self.title = ", ".join(OrderedSet(self.location.get_minor() + self.tags))

        self._write_description_tags()
        if len(self.description_tree.keys()) > 0:
            self._write_description_tree()
        full_description = (FileMetaData.linesep + "\n\n").join(self.descriptions)

        tagDict = {'Label': self.filenameAccessor.name, 'Title': self.title,
                   'Keywords': self.tags, 'Subject': list(self.tags),
                   'Description': full_description, 'UserComment': full_description,
                   'Identifier': self.id, 'Rating': self.rating, 'Artist': settings.photographer}

        if len(self.gps) == 2:
            tagDict["GPSLatitudeRef"] = self.gps[0]
            tagDict["GPSLatitude"] = self.gps[0]
            tagDict["GPSLongitudeRef"] = self.gps[1]
            tagDict["GPSLongitude"] = self.gps[1]

        add_dict(tagDict, self.location.to_tag_dict())
        tagDict['Keywords'].extend(self.tags2 + self.tags3)
        tagDict['Subject'].extend(self.tags2 + self.tags3)
        return tagDict

    def __str__(self):
        return "FileMetaData(" + self.title + " " + str(self.tags) + " " + str(self.descriptions) + " " + str(
            self.location) + ")"


def add_dict(dict1: dict, dict2: dict):
    for key in dict2:
        if key in dict1:
            dict1[key] += dict2[key]
        else:
            dict1[key] = dict2[key]


def format_as_tree(data: dict) -> str:
    def indent(string: str) -> str:
        return indented_newline + string.replace("\n", indented_newline)

    out = ""
    indented_newline = "\n- "
    for key in data:
        if not data[key]:
            continue
        if type(data[key]) == str:
            value = data[key]
            if "\n" in value: value = indent(value)
        else:
            value = format_as_tree(data[key])
            value = indent(value)
        out += key + ": " + value + " \n"
    out = out.strip(indented_newline)
    return out


def sort_by_list(data: dict, order: list) -> OrderedDict:
    index_map = {v: i for i, v in enumerate(order)}
    return OrderedDict(sorted(data.items(), key=lambda pair: index_map[pair[0]]))


def format_plain(data: dict) -> str:
    out = ""
    for key in data:
        out += key + ": " + data[key] + FileMetaData.linesep + "\n"
    out = out[:-2]
    return out


def format_tree_plain(data: dict) -> str:
    out = ""
    for key in data:
        if not data[key]:
            continue
        if type(data[key]) == str:
            value = data[key]
        else:
            value = format_plain(data[key])
        out += key + ": " + value + " - "
    out = out[:-2]
    return out


def set_path(data: dict, path, value=None):
    sub_data = data
    for key in path[:-1]:
        if not key in sub_data:
            sub_data[key] = OrderedDict()
        sub_data = sub_data[key]
    if value:
        sub_data[path[-1]] = value
    elif not path[-1] in sub_data:
        sub_data[path[-1]] = OrderedDict()


def fullname_to_tag(dirpath: str, filename: str, startdir=""):
    relpath = os.path.relpath(dirpath, startdir)
    if relpath == ".": relpath = ""
    dirpath_split = relpath.split(os.sep)
    filename_prim = filename.split("_")[0]
    image_id = filename
    image_tags = dirpath_split + [filename_prim]
    return image_id, image_tags


def scene_to_tag(scene: str) -> list:
    out = [scene]
    scene_striped = scene.strip('123456789').split('$')[0]
    if not scene in c.RecModes:
        out.append(scene_striped.lower())
    return out


def process_to_tag(process: str) -> list:
    process_striped = process.strip('123456789').split('$')[0]
    process_main = process_striped
    process_sub = ""
    if '-' in process_main:
        process_main, process_sub = process_striped.split('-', 1)
    out = [process_striped]
    if process_main in process_to_tag.map:
        out.extend(process_to_tag.map[process_main])
        if process_main == "HDR" and "-" in process_sub:
            out.append("Tone Mapping")
    return out


process_to_tag.map = {"HDR": ["HDR"], "HDRT": ["HDR", "Tone Mapping"], "PANO": ["Panorama"]}


def is_scene_abbreviation(name: str):
    return name in SceneModeAbbreviations or name in c.RecModes


def is_process_tag(name: str):
    scene_striped = name.strip('123456789').split('$')[0]
    scene_main = scene_striped.split('-')[0]
    return scene_main in process_to_tag.map.keys()


def process_to_description(process: str) -> dict:
    description = {}
    if not "HDR" in process: return description
    process_striped = process.strip('123456789').split('$')[0]
    process_split = process_striped.split('-')
    if len(process_split) > 1:
        if process_split[1] in c.hdr_algorithm:
            description["HDR-Algorithm"] = c.hdr_algorithm[process_split[1]]
        else:
            log().info("%s not in hdr_algorithm", process_split[1])
    if len(process_split) > 2:
        if process_split[2] in c.tm_preset:
            description["TM-Preset"] = c.tm_preset[process_split[2]]
        else:
            log().info("%s not in tm_preset", process_split[1])
    return description


class FilenameAccessor:
    counter_main_regex = re.compile(r'(M?\d+)')

    def __init__(self, filename):
        self.filename = filename
        self.name, self.ext = filename.rsplit('.', 1)
        self.ext = "." + self.ext
        self.main = []
        self.pre = ""
        self.primmodes = []
        self.primtags = []
        self.counter = ""
        self.scenes = []
        self.processes = []
        self.posttags = []
        self._split_filename()

    def _split_filename(self):
        filename_splited = self.name.split('_')
        if len(filename_splited) == 0: return
        counter_index = self._counter_index()
        if counter_index < 0: return
        for i, subname in enumerate(filename_splited):
            if not subname: continue
            if i > counter_index:
                if is_process_tag(subname):
                    self.processes.append(subname)
                elif is_scene_abbreviation(subname):
                    self.scenes.append(subname)
                else:
                    self.posttags.append(subname)
            else:
                self.main.append(subname)
                if i == 0:
                    self.pre = subname
                elif i == counter_index:
                    self.counter = subname
                elif subname.isupper() or subname.isnumeric():
                    self.primmodes.append(subname)
                else:
                    self.primtags.append(subname)

    def tags(self) -> List[str]:
        return self.primtags + self.posttags

    def modes(self) -> List[str]:
        return self.scenes + self.processes

    def mapped_modes(self) -> List[str]:
        modes = [tag2 for tag in self.scenes for tag2 in scene_to_tag(tag)]
        modes += [tag2 for tag in self.processes for tag2 in process_to_tag(tag)]
        return modes

    def identifier(self) -> str:
        return "_".join(self.main + self.modes())

    def has_tag(self, tag) -> bool:
        return tag in self.primtags or tag in self.posttags

    def sorted_filename(self):
        arr = self.main + self.scenes + self.processes + self.posttags
        return "_".join(arr) + self.ext

    def counter_main(self) -> str:
        match = FilenameAccessor.counter_main_regex.search(self.counter)
        if match:
            return match.group(1)
        return self.counter

    def mainname(self) -> str:
        arr = self.main[:-1] + [self.counter_main()]
        return "_".join(arr)

    def _counter_index_longest(self) -> int:
        filename_splited = self.name.split('_')
        if len(filename_splited) == 0: return -1
        # get index of counter via longest item that looks like a counter
        indeces = [(i, len(e)) for i, e in enumerate(filename_splited) if self._is_counter(e)]
        if len(indeces) == 0:
            return -1
        if len(indeces) == 1:
            return indeces[0][0]
        indeces.sort(key=operator.itemgetter(1))
        return indeces[-1][0]

    def _counter_index(self) -> int:
        filename_splited = self.name.split('_')
        if len(filename_splited) == 0: return -1
        indeces = [i for i, e in enumerate(filename_splited) if self._is_counter(e)]
        if len(indeces) == 0:
            return -1
        return indeces[-1]

    def _is_counter(self, subname) -> bool:
        if not subname:
            return False
        if self.ext in settings.video_types:
            return subname[0] == "M" and np.chararray.isdigit(subname[-1])
        starts_and_ends_with_digit = (np.chararray.isdigit(subname[0]) and np.chararray.isdigit(subname[-1]))
        return starts_and_ends_with_digit


class FilenameBuilder:

    def __init__(self, old_filename: str):
        self.main = []
        self.post = []
        self.version = ""
        self.accessor = FilenameAccessor(old_filename)

    def add_main(self, part):
        if part:
            self.main.append(part)
        return self

    def add_post(self, part):
        if part:
            self.post.append(part)
        return self

    def set_version(self, version):
        self.version = version
        return self

    def use_old_tags(self):
        self.post += [tag for tag in self.accessor.processes if not tag in self.post]
        self.post += [tag for tag in self.accessor.primtags if not tag in self.main]
        self.post += [tag for tag in self.accessor.posttags if not tag in self.post]

    def build(self) -> str:
        if self.version:
            arr = self.main + [self.version] + self.post
        else:
            arr = self.main + self.post
        return "_".join(arr) + self.accessor.ext
