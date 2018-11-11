import os
import re
from collections import OrderedDict

import numpy as np

from EXIFnaming.helpers import constants as c
from EXIFnaming.helpers.decode import read_exiftag
from EXIFnaming.helpers.settings import hdr_program, panorama_program, photographer


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
    restriction_keys = ['directory', 'name_main', 'first', 'last', 'name_part']
    tag_setting_keys = ['title', 'tags', 'rating', 'description', 'gps']
    linesep = " | "

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
        self.main_name, self.counter = get_main_and_counter(self.name)
        self.has_changed = False

    def import_filename(self):
        self.id, self.tags, self.tags_p = filename_to_tag(self.name)

    def import_fullname(self, startdir: str):
        self.id, self.tags = fullname_to_tag(self.directory, self.name, startdir)

    def import_exif(self):
        self.tagDict = read_exiftag(self.directory, self.filename)
        self.location.update(self.tagDict)

        if "User Comment" in self.tagDict:
            user_comment = self.tagDict["User Comment"]
            user_comment_split = user_comment.split("..")
            user_comment_split = [string for line in user_comment_split for string in
                                  line.split(FileMetaData.linesep + ".")]
            process_dict = {}
            pano_keys = ["Projection", "FOV", "Ev"]
            for entry in user_comment_split:
                if not ": " in entry: continue
                entry = entry.strip(FileMetaData.linesep)
                key, value = entry.split(": ", 1)
                if key in pano_keys:
                    key = "PANO-" + key
                process_dict[key] = value
            self.update_processing(process_dict)

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

    def update_processing(self, data: dict):
        def good_key(key: str):
            return key in data and data[key]

        if not self._passes_restrictions(data):
            return

        if good_key('tags'): self.tags_p += [tag for tag in data['tags'].split(', ') if tag]
        if good_key('rating'): self.rating = data['rating']

        known_keys = FileMetaData.restriction_keys + FileMetaData.tag_setting_keys
        other_keys = [key for key in data if not key in known_keys and data[key]]
        for key in other_keys:
            self.description_tree[key] = data[key]

    def _passes_restrictions(self, data):
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
            self.description_tree["HDR-program"] = hdr_program
        if any(["PANO" in key for key in self.description_tree]):
            self.description_tree["PANO-program"] = panorama_program
        description_tree = OrderedDict()
        process_order = ["HDR", "TM", "PANO"]
        for key_part in process_order:
            process_subkeys = [key for key in self.description_tree if key_part in key]
            for key in process_subkeys:
                description_tree[key] = self.description_tree[key]
        description_formated = format_plain(description_tree)
        self.descriptions.append(description_formated)

    def to_tag_dict(self) -> dict:
        if not self.title:
            self.title = ", ".join(self.tags + self.tags_p)

        tags = [", ".join(self.tags), str(self.location), ", ".join(self.tags_p)]
        self.descriptions.append((FileMetaData.linesep + "\n").join(tags))
        if len(self.description_tree.keys()) > 0:
            self._write_description_tree()
        full_description = (FileMetaData.linesep + "\n\n").join(self.descriptions)

        tagDict = {'Label': self.name, 'Title': self.title,
                   'Keywords': self.tags, 'Subject': list(self.tags),
                   'Description': full_description, 'UserComment': full_description,
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


def filename_to_tag(filename: str):
    filename_dict = split_filename(filename)
    image_id = "_".join(filename_dict["main"] + filename_dict["p_tags"])
    image_tags = filename_dict["tags"]
    image_tags_p = [tag2 for tag in filename_dict["scene"] for tag2 in scene_to_tag(tag)]
    image_tags_p += [tag2 for tag in filename_dict["process"] for tag2 in process_to_tag(tag)]
    return image_id, image_tags, image_tags_p


def split_filename(filename: str):
    filename_splited = filename.split('_')
    if len(filename_splited) == 0: return
    filename_dict = {"main": [], "tags": [], "scene": [], "process": [], "p_tags": []}
    counter_complete = False
    for subname in filename_splited:
        if counter_complete:
            if is_process_tag(subname):
                filename_dict["process"].append(subname)
                filename_dict["p_tags"].append(subname)
            elif is_scene_abbreviation(subname):
                filename_dict["scene"].append(subname)
                filename_dict["p_tags"].append(subname)
            else:
                filename_dict["tags"].append(subname)
        else:
            filename_dict["main"].append(subname)
            if is_counter(subname): counter_complete = True
    return filename_dict


def is_counter(name) -> bool:
    starts_and_ends_with_digit = (np.chararray.isdigit(name[0]) and np.chararray.isdigit(name[-1]))
    is_movie_counter = name[0] == "M" and np.chararray.isdigit(name[-1])
    return starts_and_ends_with_digit or is_movie_counter


def get_main_and_counter(filename: str):
    filename_splited = filename.split('_')
    counter = None
    for entry in filename_splited:
        if is_counter(entry):
            match = get_main_and_counter.regex.search(entry)
            counter = match.group(1)
    return filename_splited[0], counter


get_main_and_counter.regex = re.compile(r"(M?\d*)")


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


def process_to_tag(scene: str) -> list:
    scene_striped = scene.strip('123456789').split('$')[0]
    scene_main = scene_striped.split('-')[0]
    out = [scene_striped]
    if scene_main in process_to_tag.map:
        out.append(process_to_tag.map[scene_main])
    return out

process_to_tag.map = {"HDR": "HDR", "HDRT": "HDR", "PANO": "Panorama"}


def is_scene_abbreviation(name: str):
    return name in c.SceneShort.values() or name in c.KreativeShort.values() or name in c.RecModes


def is_process_tag(name: str):
    scene_striped = name.strip('123456789').split('$')[0]
    scene_main = scene_striped.split('-')[0]
    return scene_main in process_to_tag.map.keys()