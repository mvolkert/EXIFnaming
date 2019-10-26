#!/usr/bin/env python3
"""
get information about places from googlemaps

dependencies: googlemaps
"""
import csv
from collections import OrderedDict

import googlemaps

from EXIFnaming.helpers.program_dir import get_info_dir
from EXIFnaming.helpers import settings

__all__ = ["get_info", "write_infos"]


def get_info(search: str):
    """
    get infos for place
    :param search: place search string
    :return: result dict representing json
    """
    gmaps = googlemaps.Client(key=settings.googlemaps_api_key)
    params = {"input": search, "inputtype": "textquery", "fields": "geometry/location,name"}
    result = gmaps._request("/maps/api/place/findplacefromtext/json", params)
    return result


def write_infos():
    """
    use google maps to get gps infos of places
    uses tags_places.csv as input and fills it with gps and location name
    output: tags_places_gmaps.csv
    """
    csv.register_dialect('semicolon', delimiter=';', lineterminator='\n')
    filename = get_info_dir("tags_places.csv")

    outname = get_info_dir("tags_places_gmaps.csv")
    outfile = open(outname, "w")
    writer = csv.DictWriter(outfile, fieldnames=["directory", "name_part", "Location", "gps"], dialect="semicolon")
    writer.writeheader()
    with open(filename, "r") as infile:
        reader = csv.DictReader(infile, dialect="semicolon")
        for row in reader:
            search = row["directory"] + " " + row["name_part"]
            result = get_info(search.strip(" "))
            for canidate in result["candidates"]:
                outdir = OrderedDict()
                outdir["directory"] = row["directory"]
                outdir["name_part"] = row["name_part"]
                loc = canidate["geometry"]["location"]
                outdir["gps"] = "%f, %f" % (loc["lat"], loc["lng"])
                outdir["Location"] = canidate["name"]
                writer.writerow(outdir)
    outfile.close()
