# EXIFnaming

[![Build Status](https://travis-ci.com/mvolkert/EXIFnaming.svg?branch=master)](https://travis-ci.com/mvolkert/EXIFnaming)
[![PyPI version](https://badge.fury.io/py/EXIFnaming.svg)](https://badge.fury.io/py/EXIFnaming)
![PyPI - Downloads](https://img.shields.io/pypi/dm/EXIFnaming)
<!---[![codecov](https://codecov.io/gh/mvolkert/EXIFnaming/branch/master/graph/badge.svg)](https://codecov.io/gh/mvolkert/EXIFnaming)--->
<!---![GitHub contributors](https://img.shields.io/github/contributors/mvolkert/EXIFnaming)--->

Renaming/Ordering/Modifying Photos using exiftool (https://exiftool.org/).

Developed for Panasonic Lumix TZ101 but other models may also work.
You are free to contact me for verifying the support of your Camera model.

## Functionalities:
* Ordering:   
    in folders by date

* Renaming:  
    to pattern:  
    [AbrivationforPlace][YearMonthDay]\_[Filenumber][SeriesType][SeriesSubNumber]\_[PhotoMode]

* Filtering:  
    move pictures acording to renaming pattern to subfolders.  
    for expample: all Braket series with 5 pictures to one folder

* Tag writing:  
    write a single csv with minimal information and  
    let write all tags, title, description and so on into the exif information.
        
* Geotagging        

And many more...

## Usage:
It is designed to be used via ipython.
You do need at least basic knowlege about python.
The different functions can either be used via the toplevel module or via the submodules.


## Naming Conventions:
* AbrivationforPlace
    can be choosen freely
* YearMonthDay
    format can be choosen
* Filenumber
    handled by rename method
    shows the number of the picture or the series
* SeriesType
    handled by rename method
* SeriesSubNumber
    handled by rename method
    shows the number of the picture within this series.
* PhotoMode  
    * Scene:
        mapping between Advaned Scene names and Abbreviations
    * Postprocessing:
        * HDR:  
            * HDR-[HDR-Algorithm-Abr.]  
            * HDR-[HDR-Algorithm-Abr.]-[Tone Mapping-Preset-Abr.]  
            * HDR-[HDR-Algorithm-Abr.]-[Tone Mapping-Preset-Abr.]$[counter]  
            * HDR-[HDR-Algorithm-Abr.]$[[start]-[end]]  
            
            examples:  
            * "Colormix" Alorithm: HDR-C  
            * "Natural balanced" Tone Mapping: HDR-C-Nb  
            * secound version of HDR picture: HDR-C$2
            * HDR picture consists only of the second to fifth picture of bracket series: HDR-C$[2-5]
            * HDR picture consists of picture with counter 12,14 and 15: HDR-C$[12,14,15]
        * Panorma:  
            * PANO  
            * PANO-[submode]$[counter]    
* Tags  
    can be added to filename
    have to be seperated by "_"

    
## EXIF Conventions
* Label:  
    Same as Filename used to retrive Filename if it was changed
* Title:  
    Main Tags, but can be chosen differently
* Description:  
    Contains main Description, Tags and Processing information.  
    Is Formated in a way that is nicely readable multiline and in plain view  
    Following Programms can read it: Flickr, FStop (Android), Google Fotos and maybe more
* User Comment: Same as Description. Windows can display it.
* Keywords/Subject:
    Both are used store Tags of the pictures.
    Following Programms can read it: Flickr, FStop (Android), Windows and maybe more
* Location: xpm LocationCreated is used

## EXIFnaming folder structure
The program creates a folder ".EXIFnaming" in your photodirectory:  
* gps: put here your gpx files for geotagging  
* infos: information files writen by multilple functions  
* log: logfiles  
* saves: renaming writes saves to restore old names  
* setexif: put here your csv files for tag writing  

## Camera Models
* Can be used basically with all camera models which are supported by https://exiftool.org/  
* To use specialties of renaming like Series type or Scene mode, there has to be an implemention of ModelBase for your Camera Model  
* Contact me to improve the support of your Camera Model  

## Setup

Download https://exiftool.org/.
Then set EXIFnaming.settings.exiftool_directory to the location of the exiftool.exe.
You can do this for example by using `.ipython\profile_default\startup\start.py`.
Take also a look to other settings.