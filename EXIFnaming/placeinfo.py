import csv
from collections import OrderedDict

import googlemaps

from EXIFnaming.helpers.fileop import get_info_dir
from EXIFnaming.helpers.settings import googlemaps_api_key


def get_info(search: str):
    gmaps = googlemaps.Client(key=googlemaps_api_key)
    params = {"input": search, "inputtype": "textquery", "fields": "geometry/location,name"}
    result = gmaps._request("/maps/api/place/findplacefromtext/json", params)
    return result


def write_infos():
    csv.register_dialect('semicolon', delimiter=';', lineterminator='\n')
    filename = get_info_dir("tags_places.csv")

    outname = get_info_dir("tags_places_gmaps.csv")
    outfile = open(outname, "w")
    writer = csv.DictWriter(outfile, fieldnames=["dirname", "tag", "name", "gps"], dialect="semicolon")
    writer.writeheader()
    with open(filename, "r") as infile:
        reader = csv.DictReader(infile, dialect="semicolon")
        for row in reader:
            search = row["dirname"] + " " + row["tag"]
            result = get_info(search.strip(" "))
            for canidate in result["candidates"]:
                outdir = OrderedDict()
                outdir["dirname"] = row["dirname"]
                outdir["tag"] = row["tag"]
                loc = canidate["geometry"]["location"]
                outdir["gps"] = "%f, %f" % (loc["lat"], loc["lng"])
                outdir["name"] = canidate["name"]
                writer.writerow(outdir)
    outfile.close()
