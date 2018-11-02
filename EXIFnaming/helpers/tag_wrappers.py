import functools
import os
import re
from collections import OrderedDict

import numpy as np

from EXIFnaming.helpers.settings import hdr_program, panorama_program, photographer
from EXIFnaming.helpers.tags import scene_to_tag


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

    def __init__(self, directory, filename):
        self.directory = directory
        self.filename = filename[:filename.rfind(".")]
        self.id = self.filename
        self.title = ""
        self.tags = []
        self.descriptions = []
        self.description_tree = OrderedDict()
        self.location = Location()
        self.rating = None
        match = FileMetaData.regex.search(filename)
        if match:
            self.main_name = match.group(1)
            self.counter = int(match.group(2))
        else:
            print(filename, 'does not match regex')

    def import_filename(self):
        self.id, self.tags = filename_to_tag(self.filename)

    def import_fullname(self, startdir: str):
        self.id, self.tags = fullname_to_tag(self.directory, self.filename, startdir)

    def update(self, data: dict):
        def good_key(key: str):
            return key in data and data[key]

        if not self._passes_restrictions(data):
            return

        if good_key('title'): self.title = data['title']
        if good_key('tags'): self.tags += [tag for tag in data['tags'].split(', ') if tag]
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

        if good_key('tags'): self.tags += [tag for tag in data['tags'].split(', ') if tag]
        if good_key('rating'): self.rating = data['rating']
        hdr_keys = filter_keys("HDR")
        tm_keys = filter_keys("TM")
        pano_keys = filter_keys("PANO")
        known_keys = ['directory', 'filename_part', 'tags', 'rating'] + hdr_keys + tm_keys + pano_keys
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
        return True

    def to_tag_dict(self) -> dict:
        if not self.title:
            self.title = functools.reduce(lambda title, tag: title + ", " + tag, self.tags, "").strip(", ")

        description_formated = format_as_tree(self.description_tree)
        if description_formated:
            self.descriptions.append(description_formated)
        full_description = functools.reduce(lambda description, entry: description + "\n\n" + entry, self.descriptions,
                                            "").strip("\n\n")

        tagDict = {'Label': self.filename, 'title': self.title, 'Keywords': self.tags, 'Subject': list(self.tags),
                   'ImageDescription': full_description, 'XPComment': full_description,
                   'Identifier': self.id, 'Rating': self.rating, 'Artist': photographer}

        add_dict(tagDict, self.location.to_tag_dict())
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
    def starts_and_ends_with_digit(string) -> bool:
        return np.chararray.isdigit(string[0]) and np.chararray.isdigit(string[-1])

    filename_splited = filename.split('_')
    if len(filename_splited) == 0: return
    image_id = ""
    image_tags = []
    counter_complete = False
    for subname in filename_splited:
        if counter_complete:
            if subname.isupper():
                image_id += subname + "_"
                image_tags.extend(scene_to_tag(subname))
            else:
                image_tags.append(subname)
        else:
            image_id += subname + "_"
            if starts_and_ends_with_digit(subname): counter_complete = True
    image_id = image_id[:-1]
    return image_id, image_tags


def fullname_to_tag(dirpath: str, filename: str, startdir=""):
    relpath = os.path.relpath(dirpath, startdir)
    if relpath == ".": relpath = ""
    dirpath_split = relpath.split(os.sep)
    filename_prim = filename.split("_")[0]
    image_id = filename
    image_tags = dirpath_split + [filename_prim]
    return image_id, image_tags
