import os
import re
from collections import OrderedDict

import numpy as np

from EXIFnaming.helpers.decode import read_exiftag
from EXIFnaming.helpers.settings import hdr_program, panorama_program, photographer
from EXIFnaming.helpers.tags import scene_to_tag, is_scene_abbreviation, is_process_tag, process_to_tag


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
                self.location[key] = data[key]

    def update_via_tag_array(self, data: dict, i: int):

        for key in Location.location_keys:
            if key in data and data[key][i]:
                self.location[key] = data[key][i]

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
    regex = re.compile(r"^([-\w]+)_([0-9]+)[A-Z0-9]*")
    restriction_keys = ['directory', 'name_main', 'first', 'last', 'name_part']
    tag_setting_keys = ['title', 'tags', 'rating', 'description', 'gps']

    def __init__(self, directory, filename):
        self.directory = directory
        self.filename = filename
        self.name = filename[:filename.rfind(".")]
        self.id = self.filename
        self.title = ""
        self.tags = []
        self.tags_p = []
        self.descriptions = []
        self.description_tree = OrderedDict()
        self.location = Location()
        self.rating = None
        self.gps = ()
        self.tagDict = None
        match = FileMetaData.regex.search(filename)
        if match:
            self.main_name = match.group(1)
            self.counter = int(match.group(2))
        else:
            print(filename, 'does not match regex')
        self.has_changed = False

    def import_filename(self):
        self.id, self.tags, self.tags_p = filename_to_tag(self.name)

    def import_fullname(self, startdir: str):
        self.id, self.tags = fullname_to_tag(self.directory, self.name, startdir)

    def update(self, data: dict):
        def good_key(key: str):
            return key in data and data[key]

        if not self._passes_restrictions(data):
            return

        if good_key('title'): self.title = data['title']
        if good_key('tags'): self.tags += [tag for tag in data['tags'].split(', ') if tag]
        if good_key('gps'): self.gps = data['gps'].split(', ')
        if good_key('rating'): self.rating = data['rating']
        if good_key('description'): self.descriptions.append(data['description'])
        self.location.update(data)
        set_path(self.description_tree, ["Location"], str(self.location))

    def update_processing(self, data: dict):
        def set_keys(path: [], keys: list):
            for key in keys:
                set_path(self.description_tree, path + [key], data[key])

        def good_key(key: str):
            return key in data and data[key]

        def filter_keys(key_part: str):
            return [key for key in data if key_part in key and data[key]]

        if not self._passes_restrictions(data):
            return

        if good_key('tags'): self.tags_p += [tag for tag in data['tags'].split(', ') if tag]
        if good_key('rating'): self.rating = data['rating']
        hdr_keys = filter_keys("HDR")
        tm_keys = filter_keys("TM")
        pano_keys = filter_keys("PANO")
        known_keys = FileMetaData.restriction_keys + FileMetaData.tag_setting_keys + hdr_keys + tm_keys + pano_keys
        other_keys = [key for key in data if not key in known_keys and data[key]]
        if hdr_keys:
            set_path(self.description_tree, ["Processing", "HDR", "program"], hdr_program)
            set_keys(["Processing", "HDR", "HDR-setting"], hdr_keys)
        if tm_keys:
            set_path(self.description_tree, ["Processing", "HDR", "program"], hdr_program)
            set_keys(["Processing", "HDR", "HDR-Tonemapping"], tm_keys)
        if pano_keys:
            set_path(self.description_tree, ["Processing", "Panorama", "program"], panorama_program)
            set_keys(["Processing", "Panorama"], pano_keys)
        if other_keys:
            set_keys(["Processing", "misc"], other_keys)

    def _passes_restrictions(self, data):
        def not_match_entry(key: str, func):
            return key in data and data[key] and not func(data[key])

        if not_match_entry('directory', lambda value: value in self.directory):
            return False
        if not_match_entry('name_main', lambda value: value == self.main_name):
            return False
        if not_match_entry('first', lambda value: int(value) <= self.counter):
            return False
        if not_match_entry('last', lambda value: self.counter <= int(value)):
            return False
        if not_match_entry('name_part', lambda value: value in self.filename):
            return False

        self.has_changed = True
        return True

    def to_tag_dict(self) -> dict:
        if not self.title:
            self.title = ", ".join(self.tags + self.tags_p)

        description_formated = format_as_tree(self.description_tree)
        if description_formated:
            self.descriptions.append(description_formated)
        full_description = "\n\n".join(self.descriptions)

        tagDict = {'Label': self.name, 'title': self.title,
                   'Keywords': self.tags, 'Subject': list(self.tags),
                   'ImageDescription': full_description, 'XPComment': full_description, 'Description': full_description,
                   'Identifier': self.id, 'Rating': self.rating, 'Artist': photographer}

        if len(self.gps) == 2:
            tagDict["GPSLatitudeRef"] = self.gps[0]
            tagDict["GPSLatitude"] = self.gps[0]
            tagDict["GPSLongitudeRef"] = self.gps[1]
            tagDict["GPSLongitude"] = self.gps[1]

        add_dict(tagDict, self.location.to_tag_dict())
        tagDict['Keywords'].extend(self.tags_p)
        tagDict['Subject'].extend(self.tags_p)
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
    indented_newline = "\n-" + " " * 3
    for key in data:
        if not data[key]:
            continue
        if type(data[key]) == str:
            value = data[key]
            if "\n" in value: value = indent(value)
        else:
            value = format_as_tree(data[key])
            value = indent(value)
        out += key + ": " + value + "\n"
    out = out.strip(indented_newline)
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


def filename_to_tag(filename: str):
    filename_dict = split_filename(filename)
    image_id = "_".join(filename_dict["main"] + filename_dict["p_tags"])
    image_tags = filename_dict["tags"]
    image_tags_p = [tag2 for tag in filename_dict["scene"] for tag2 in scene_to_tag(tag)]
    image_tags_p += [tag2 for tag in filename_dict["process"] for tag2 in process_to_tag(tag)]
    return image_id, image_tags, image_tags_p


def split_filename(filename: str):
    def starts_and_ends_with_digit(string) -> bool:
        return np.chararray.isdigit(string[0]) and np.chararray.isdigit(string[-1])

    filename_splited = filename.split('_')
    if len(filename_splited) == 0: return
    name = {"main": [], "tags": [], "scene": [], "process": [], "p_tags": []}
    counter_complete = False
    for subname in filename_splited:
        if counter_complete:
            if is_process_tag(subname):
                name["process"].append(subname)
                name["p_tags"].append(subname)
            elif is_scene_abbreviation(subname):
                name["scene"].append(subname)
                name["p_tags"].append(subname)
            else:
                name["tags"].append(subname)
        else:
            name["main"].append(subname)
            if starts_and_ends_with_digit(subname): counter_complete = True
    return name


def fullname_to_tag(dirpath: str, filename: str, startdir=""):
    relpath = os.path.relpath(dirpath, startdir)
    if relpath == ".": relpath = ""
    dirpath_split = relpath.split(os.sep)
    filename_prim = filename.split("_")[0]
    image_id = filename
    image_tags = dirpath_split + [filename_prim]
    return image_id, image_tags
