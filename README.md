# EXIFnaming

Renaming/Ordering/Modifying Photos using EXIF tool https://sno.phy.queensu.ca/~phil/exiftool/.
"exiftool.exe" has to be in helpers sub folder of this module.

Developed for Panasonic Lumix TZ101 but other models may also work.
You are free to contact me for verifying the support of your kamera model.

##Functionalities:

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

##Usage:
It is designed to be used via ipython.
You do need at least basic knowlege about python.
The different functions can either be used via the toplevel module or via the subscriptes.


##Naming Conventions:
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
        mapping between Advaned Scene names and Abrivations
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

    
##EXIF Conventions
* Label:  
    Same as Filename used to retrive Filename if it was changed
* Title:  
    Main Tags, but can be chosen differently
* Description:  
    Contains main Description, Tags and Processing information.  
    Is Formated in a way that is nicely readable multiline and plain view  
    Following Programms can read it: Flickr, FStop (Android), Google Fotos, [maybe more]
* User Comment: Same as Description. Windows can display it.
* Keywords/Subject:      
    Both are used store Tags of the pictures.
    Following Programms can read it: Flickr, FStop (Android), Windows, [maybe more]
* Location: xpm LocationCreated is used

    