from __future__ import print_function

from time import sleep
from typing import List

from gphotospy import authorize
from gphotospy.album import *
from gphotospy.media import *

"""
https://dev.to/davidedelpapa/manage-your-google-photo-account-with-python-p-1-9m2
"""


def main():
    service = authorize.init('credentials.json')

    create_albums_for_each_name(service)


def get_media(service: dict[str, str]):
    try:
        media_manager = Media(service)

        # Retrieve the documents contents from the Docs service.
        iterator = media_manager.list()
        first = next(iterator)
        print(first)
    except Exception as err:
        print(err)


def mainname_to_id(service: dict[str, str]) -> dict[str, List[str]]:
    mainname_to_id_dict: dict[str, List[str]] = {}
    try:
        media_manager = Media(service)

        # Retrieve the documents contents from the Docs service.
        iterator = media_manager.list()
        for i in range(10):
            item = next(iterator)
            print(item)
            mainname = item['filename'].split('_')[0]
            if not mainname in mainname_to_id_dict:
                mainname_to_id_dict[mainname] = []
            mainname_to_id_dict[mainname].append(item['id'])
        print(mainname_to_id_dict)
        return mainname_to_id_dict
    except Exception as err:
        print(err)


def create_albums(service: dict[str, str], album_contents: dict[str, List[str]]):
    album_manager = Album(service)
    existing_albums = {album['title']: album['id'] for album in get_albums(service)}
    print(existing_albums)
    for key in album_contents:
        if not key in existing_albums:
            album_id = album_manager.create(key)['id']
        else:
            album_id = existing_albums[key]
        print(album_id)
        chunks = [album_contents[key][x:x + 50] for x in range(0, len(album_contents[key]), 50)]
        for chunk in chunks:
            print(chunk)
            album_manager.batchAddMediaItems(album_id, chunk)

def create_albums_for_each_name(service: dict[str, str]):
    media_manager = Media(service)
    album_manager = Album(service)
    last_name = ""
    iterator = media_manager.list()
    while True:
        if not iterator:
            return
        item = next(iterator)
        print(item)
        mainname = item['filename'].split('_')[0]
        if not mainname == last_name:
            last_name = mainname
            try:
                album_manager.create(mainname)
            except Exception as err:
                print(err)
                sleep(60)
                album_manager.create(mainname)

def delete_albums(service: dict[str, str]):
    media_manager = Media(service)
    album_manager = Album(service)
    albums = get_albums(service)


def get_albums(service: dict[str, str])->List[dict]:
    album_manager = Album(service)
    album_iterator = album_manager.list()
    albums = []
    while True:
        try:
            album= next(album_iterator)
            if not album:
                break
            albums.append(album)
        except Exception as err:
            print(err)
            break
    return albums


if __name__ == '__main__':
    main()
