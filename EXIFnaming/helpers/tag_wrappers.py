import functools
import re

from EXIFnaming.helpers.settings import hdr_program, panorama_program


class Location:
    def __init__(self, country="", region="", city="", location=""):
        self.country = country
        self.region = region
        self.city = city
        self.location = location

    def update(self, data: {}):
        if data['country']: self.country = data['country']
        if data['region']: self.region = data['region']
        if data['city']: self.city = data['city']
        if data['location']: self.location = data['location']

    def toTagDict(self) -> dict:
        loc_tags = [self.country, self.city, self.location]
        return {'Country': self.country, 'State': self.country, 'City': self.city, 'Location': self.location,
                'Keywords': loc_tags, 'Subject': loc_tags,
                'LocationCreatedCountryName': self.country, 'LocationCreatedProvinceState': self.region,
                'LocationCreatedCity': self.city, 'LocationCreatedSublocation': self.location}

    def __str__(self):
        return "Location(" + self.country + " " + self.region + " " + self.city + " " + self.location + ")"


class FileMetaData:

    def __init__(self, directory, filename):
        self.directory = directory
        self.filename = filename
        self.title = filename
        self.tags = []
        self.descriptions = []
        self.location = Location()
        regex = r"^([-\w]+)_([0-9]+)[A-Z0-9]*"
        match = re.search(regex, filename)
        if match:
            self.main_name = match.group(1)
            self.counter = int(match.group(2))
        else:
            print(filename, 'does not match ', regex)

    def update(self, data: dict):
        def not_match_entry(key: str, func):
            return key in data and data[key] and not func(data[key])

        if not_match_entry('directory', lambda value: value in self.directory):
            return
        if not_match_entry('main_name', lambda value: value == self.main_name):
            return
        if not_match_entry('first', lambda value: int(value) <= self.counter):
            return
        if not_match_entry('last', lambda value: self.counter <= int(value)):
            return

        self.title = data['title']
        self.tags += data['tags'].split(', ')
        self.descriptions.append(data['description'])
        self.location.update(data)

    def update_processing(self, data: dict):
        def not_match_entry(key: str, func):
            return key in data and data[key] and not func(data[key])

        if not_match_entry('directory', lambda value: value in self.directory):
            return
        if not_match_entry('filename_part', lambda value: value in self.filename):
            return

        description = {"Processing": {}}
        processing_hdr = {}
        processing_pano = {}
        if 'HDR' in data and data['HDR']:
            processing_hdr["HDR-program"] = hdr_program
            processing_hdr["HDR-setting"] = data['HDR']
            if 'Tonemapping' in data and data['Tonemapping']:
                processing_hdr["HDR-Tonemapping"] = data['Tonemapping']
            description["Processing"]["HDR"] = processing_hdr
        if 'Panorama' in data and data['Panorama']:
            processing_pano["Panorama-program"] = panorama_program
            processing_pano["Panorama-infos"] = data['Panorama']
            description["Processing"]["Panorama"] = processing_pano
        formated = format_as_tree(description)
        if formated:
             self.descriptions.append(formated)


    def toTagDict(self) -> dict:
        tagDict = {'Label': self.filename, 'title': self.title, 'Keywords': self.tags, 'Subject': self.tags,
                   'ImageDescription': functools.reduce(lambda description, entry: description + "\n\n" + entry,
                                                        self.descriptions, ""),
                   'Identifier': self.filename}
        loc_Dict = self.location.toTagDict()
        for key in loc_Dict:
            if key in tagDict:
                tagDict[key] += loc_Dict[key]
            else:
                tagDict[key] = loc_Dict[key]
        return tagDict

    def __str__(self):
        return "FileMetaData(" + self.title + " " + str(self.tags) + " " + str(self.descriptions) + " " + str(
            self.location) + ")"


def format_as_tree(data):
    out = ""
    indented_newline = '\n' + '-' + ' ' * 3
    if type(data) == str:
        return data
    for key in data:
        print(data, key)
        if not data[key]:
            continue
        value = format_as_tree(data[key])
        if "\n" in value: value = indented_newline + value.replace('\n', indented_newline)
        out += key + ": " + value + "\n"
    out = out.strip(indented_newline)
    return out
