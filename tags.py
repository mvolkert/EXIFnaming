#!/usr/bin/env python3

'''
collection of Tag operations
works with: www.sno.phy.queensu.ca/~phil/exiftool/
exiftool.exe has to be in the same folder
'''

__author__ = "Marco Volkert"
__copyright__ = ("Copyright 2017, Marco Volkert")
__email__ = "marco.volkert24@gmx.de"       
__status__ = "Development"

import subprocess
import os
import shutil
from collections import OrderedDict
import datetime as dt
import operator
import numpy as np

#for reloading
from IPython import get_ipython
get_ipython().magic('reload_ext autoreload')
from tags_misc import * 

print('loaded collection of Tag operations')

inpath = standardDir
subdir = True

def setInpath(path=os.getcwd(),modifySubdirs=True):
    newpath=path
    if not ":\\" in path: newpath=standardDir+path
    if not os.path.isdir(newpath): 
        print(newpath,"is not a valid path")     
        return
    global inpath, subdir    
    inpath = newpath
    subdir = modifySubdirs
    print(inpath,"modifySubdirs:",subdir)


def printinfo(tagGroupNames=[],Fileext=".JPG"):  
    outdict=readTags(inpath,subdir,Fileext)
    for  tagGroupName in TagNames:
        if not tagGroupNames==[] and not tagGroupName in tagGroupNames: continue
        outstring=""            
        for entry in ["File Name"]+TagNames[tagGroupName]:
            if not entry in outdict: continue
            if len(outdict[entry])==len(outdict["File Name"]): outstring+="%-30s\t"%entry  
            else: del outdict[entry]
        outstring+="\n"    
        for i in range(len(outdict["File Name"])):    

            outstring+="%-40s\t"%outdict["File Name"][i]
            for entry in TagNames[tagGroupName]:
                if not entry in outdict: continue
                val=outdict[entry]
                outstring+="%-30s\t"%val[i]
            outstring+="\n"  
              
        dirname=scriptDir+inpath.replace(standardDir,'') 
        if not os.path.isdir(dirname):  os.makedirs(dirname)  
        ofile=open(dirname+"\\tags_"+tagGroupName+".txt",'a')            
        ofile.write(outstring)              
        ofile.close()  
        
def readTag(dirpath,filename):
    outdict=OrderedDict()
    proc = subprocess.Popen(["exiftool", dirpath+"\\"+filename], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    out=str(out) 
    already_date_org=False
    for tag in out.split("\\r\\n"):
        try:
            key=tag.split(": ")[0].strip()
            val=tag.split(": ")[1].strip()
        except: 
            continue   
        if "Date/Time Original" in tag: 
            if already_date_org: pass  
            else: 
                already_date_org=True
                continue
        if val in unknownTags: val=unknownTags[val]    
        outdict[key]=[val]        
    return outdict  


        
    

def rename_PM(Prefix="P",dateformat='YYMM-DD',name="",startindex=1,digits=3,easymode=False,onlyprint=False,postfix_stay=True,Fileext=".JPG",Fileext_video=".MP4",Fileext_Raw=".Raw"):     
    rename(inpath,Prefix,dateformat,name,startindex,digits,easymode,onlyprint,postfix_stay,Fileext,Fileext_Raw)
    rename(inpath,Prefix,dateformat,name,1,2,easymode,onlyprint,postfix_stay,Fileext_video,Fileext_Raw)
        
        
def rename(Prefix="P",dateformat='YYMM-DD',name="",startindex=1,digits=3,easymode=False,onlyprint=False,postfix_stay=True,Fileext=".JPG",Fileext_Raw=".Raw"): 
    Tagdict=readTags(inpath,subdir,Fileext)
    
    #check integrity
    if len(Tagdict)==0: return 
    keysPrim=["Directory","File Name","Date/Time Original"]
    keysJPG=["Image Quality","HDR","Advanced Scene Mode","Scene Mode","Bracket Settings","Burst Mode","Sequence Number","Sub Sec Time Original"]
    keysMP4=["Image Quality","HDR","Advanced Scene Mode","Scene Mode","Video Frame Rate"]
    if easymode:
        keysImportant=keysPrim
    elif any(Fileext==ext for ext in ['.jpg','.JPG']):
        keysImportant=keysPrim+keysJPG
    elif any(Fileext==ext for ext in ['.mp4','.MP4']):
        keysImportant=keysPrim+keysMP4
    else:
        print("unknown file extension")
        return
    if has_not_keys(Tagdict,keys=keysImportant): return       
    
    #rename temporary
    if not onlyprint: temppostfix=renameTemp(Tagdict["Directory"],Tagdict["File Name"])
    else: temppostfix=""

    #initialize
    leng=len(list(Tagdict.values())[0])
    counter=startindex-1
    mp4counter=0
    digits=str(digits)
    time_old=giveDatetime()
    outstring=""  
    lastnewname=""
    last_SequenceNumber=1e4
    Tagdict["File Name new"]=[]
    
    for i in range(leng):
    
        dateTimeString=Tagdict["Date/Time Original"][i]
        if "Sub Sec Time Original" in Tagdict: dateTimeString+="."+Tagdict["Sub Sec Time Original"][i]
        time=giveDatetime(dateTimeString)
        
        if newdate(time,time_old,'D' in dateformat or 'N' in dateformat):
            daystring=dateformating(time,dateformat)
            NamePrefix=Prefix+daystring
            if not name=='': NamePrefix+="_"+name
            if not i==0: counter=0
                
        filename=Tagdict["File Name"][i]
        postfix=getPostfix(filename,postfix_stay)        
        counterString=""        
        sequenceString=""      
        newpostfix=""        

        if any(Fileext==ext for ext in ['.jpg','.JPG']): 
            if easymode: counter+=1 
            else:
                #SequenceNumber
                SequenceNumber=int(Tagdict["Sequence Number"][i])
                if last_SequenceNumber>=SequenceNumber and not time==time_old: counter+=1 
                if SequenceNumber>0:  last_SequenceNumber=SequenceNumber      
                else: last_SequenceNumber=1e4 #SequenceNumber==0 -> no sequence -> high possible value such that even sequences with deleted first pictures can be registered
            
                #check Modes
                is_series=Tagdict["Burst Mode"][i]=="On"
                is_Bracket=not Tagdict["Bracket Settings"][i]=="No Bracket"
                is_stopmotion=Tagdict["Timer Recording"][i]=="Stop-motion Animation"
                is_timelapse=Tagdict["Timer Recording"][i]=="Time Lapse"
                is_4K=Tagdict["Image Quality"][i]=='8.2'
                
                #Name Sequence Modes
                if is_Bracket: sequenceString+="B%d"%SequenceNumber
                elif is_series: sequenceString+="S%02d"%SequenceNumber
                elif is_stopmotion: sequenceString+="SM%03d"%SequenceNumber
                elif is_timelapse: sequenceString+="TL%03d"%SequenceNumber
                elif is_4K: sequenceString+="4KBSF"
                
            counterString=("_%0"+digits+"d")%counter    
            
        elif any(Fileext==ext for ext in ['.mp4','.MP4']):
            counter+=1
            counterString="_M"+("%02d")%counter
            if not easymode:
                recmode=getRecMode(filename,Tagdict["Advanced Scene Mode"][i],Tagdict["Image Quality"][i],Tagdict["Video Frame Rate"][i]) #Video Frame Rate is deleted in mergeDicts, even interesting: search for standbilder aus 4K via Megapixels
                if not recmode=="": newpostfix+="_"+recmode
            
        if not easymode:    
            #Name Scene Modes
            is_creative=Tagdict["Scene Mode"][i]=="Creative Control" or Tagdict["Scene Mode"][i]=="Digital Filter"
            is_scene=not is_creative and not Tagdict["Scene Mode"][i]=="Off" and Tagdict["Advanced Scene Mode"][i] in SceneShort
            is_HDR=not Tagdict["HDR"][i]=="Off"
            if is_scene: newpostfix+="_"+SceneShort[Tagdict["Advanced Scene Mode"][i]]
            elif is_creative: newpostfix+="_"+KreativeShort[Tagdict["Advanced Scene Mode"][i]]
            elif is_HDR: newpostfix+="_HDR"
            if newpostfix in postfix: newpostfix=postfix
            else: newpostfix+=postfix
            
        newname=NamePrefix+counterString+sequenceString+newpostfix    
        if newname==lastnewname: newname=NamePrefix+counterString+sequenceString+"_K"+newpostfix

        if newname in Tagdict["File Name new"]: 
            print(Tagdict["Directory"][i]+"\\"+newname+postfix, "already exsists - counted further up - time:",time,"time_old: ",time_old )
            counter+=1 
            newname=NamePrefix+("_%0"+digits+"d")%counter+sequenceString+newpostfix

        time_old=time
        lastnewname=newname
        
        newname+=filename[filename.rfind("."):] 
        Tagdict["File Name new"].append(newname)
        outstring+="%-50s\t %-50s\n"%(filename,newname)    
        if not onlyprint: renameInPlace(Tagdict["Directory"][i],filename+temppostfix, newname) 
        filename_Raw=filename[:filename.rfind(".")]+Fileext_Raw
        if not Fileext_Raw=="" and os.path.isfile(Tagdict["Directory"][i]+"\\"+filename_Raw):
            newname_Raw=newname[:newname.rfind(".")]+Fileext_Raw
            outstring+="%-50s\t %-50s\n"%(filename,newname) 
            if not onlyprint: renameInPlace(Tagdict["Directory"][i],filename_Raw+temppostfix, newname_Raw) 
     

    dirname=savesDir+inpath.replace(standardDir,'')    
    if not os.path.isdir(dirname):  os.makedirs(dirname)    
    timestring=dateformating(dt.datetime.now(),"_MMDDHHmmss") 
    np.savez_compressed(dirname+"\\Tags"+Fileext+timestring, Tagdict=Tagdict)    
    ofile=open(dirname+"\\newnames"+Fileext+timestring+".txt",'a')            
    ofile.write(outstring)              
    ofile.close()    
    

def renameBack(Fileext=".JPG"):
    dirname=savesDir+inpath.replace(standardDir,'')    
    Tagdict=np.load(dirname+"\\Tags"+Fileext+".npz")["Tagdict"].item()
    temppostfix=renameTemp(Tagdict["Directory"],Tagdict["File Name"])
    for i in range(len(list(Tagdict.values())[0])):
        filename=Tagdict["File Name new"][i]
        if not os.path.isfile(Tagdict["Directory"][i]+"\\"+filename): continue
        filename_old=Tagdict["File Name"][i]
        os.rename(Tagdict["Directory"][i]+"\\"+filename+temppostfix, Tagdict["Directory"][i]+"\\"+filename_old) 
        Tagdict["File Name new"][i],Tagdict["File Name"][i]=Tagdict["File Name"][i],Tagdict["File Name new"][i]

    
def order(outpath=None):
    if outpath==None: outpath=inpath
    elif not ":\\" in outpath: outpath=standardDir+outpath
    if not os.path.isdir(outpath): return 

    Tagdict=readTags(inpath,subdir)
    if has_not_keys(Tagdict,keys=["Directory","File Name","Date/Time Original"]): return 
    lowJump=1200.
    bigJump=3600.
    time_old=giveDatetime()
    dircounter=1
    daystring=dateformating(giveDatetime(Tagdict["Date/Time Original"][0]),"YYMMDD_")
    filenames=[]
    filenames_S=[]
    leng=len(list(Tagdict.values())[0])   
    dirNameDict_firsttime=OrderedDict()
    dirNameDict_lasttime=OrderedDict()
    print('Number of JPG: %d'%leng)
    for i in range(leng):
        time=giveDatetime(Tagdict["Date/Time Original"][i])
        timedelta = time - time_old
        timedelta_seconds=timedelta.days*3600*24+timedelta.seconds
        
        if i>0 and (timedelta_seconds>bigJump or (timedelta_seconds>lowJump and len(filenames)+len(filenames_S)>100) or newdate(time,time_old)): 
            dirNameDict_lasttime[time_old]=daystring+"%02d"%dircounter
            moveFiles(filenames,outpath+"\\"+daystring+"%02d"%dircounter)
            moveFiles(filenames_S,outpath+"\\"+daystring+"%02d_S"%dircounter) 
                  
            filenames=[]  
            filenames_S=[]
            if newdate(time,time_old):
                daystring=dateformating(time,"YYMMDD_")
                dircounter=1
            else: dircounter+=1
            dirNameDict_firsttime[time]=daystring+"%02d"%dircounter
        if Tagdict["Burst Mode"][i]=="On":   
            filenames_S.append((Tagdict["Directory"][i],Tagdict["File Name"][i])) 
        else:    
            filenames.append((Tagdict["Directory"][i],Tagdict["File Name"][i]))   
        
        time_old=time 

    dirNameDict_lasttime[time_old]=daystring+"%02d"%dircounter
    moveFiles(filenames,outpath+"\\"+daystring+"%02d"%dircounter)
    moveFiles(filenames_S,outpath+"\\"+daystring+"%02d_S"%dircounter) 
    filenames=[]  
    filenames_S=[]   
    
    Tagdict_mp4=readTags(inpath,subdir,Fileext=".MP4")
    if has_not_keys(Tagdict_mp4,keys=["Directory","File Name","Date/Time Original"]): return 
    leng=len(list(Tagdict_mp4.values())[0])   
    print('Number of mp4: %d'%leng)
    for i in range(leng):
        time=giveDatetime(Tagdict_mp4["Date/Time Original"][i])
        dirName = searchDirByTime(dirNameDict_lasttime,time,bigJump)
        if not dirName:       
            dirName = searchDirByTime(dirNameDict_firsttime,time,bigJump)        
        
        if dirName:
            moveFile2(Tagdict_mp4["File Name"][i],Tagdict_mp4["Directory"][i],outpath+"\\"+dirName+"_mp4")

def detect3D():
    Tagdict=readTags(inpath,subdir)
    if has_not_keys(Tagdict,keys=["Directory","File Name","Date/Time Original","Burst Mode","Sequence Number"]): return 
    time_old=giveDatetime()
    filenames=[]
    dir="\\3D"
    for i in range(len(list(Tagdict.values())[0])):
        if not os.path.isdir(Tagdict["Directory"][i]+dir):
            os.makedirs(Tagdict["Directory"][i]+dir)
        is_series=Tagdict["Burst Mode"][i]=="On"
        SequenceNumber=int(Tagdict["Sequence Number"][i])
        if is_series or SequenceNumber>1: continue
        time=giveDatetime(Tagdict["Date/Time Original"][i])
        timedelta = time - time_old
        timedelta_sec=timedelta.days*3600*24+timedelta.seconds
        time_old=time 
        if timedelta_sec<10 or (SequenceNumber==1 and timedelta_sec<15) or filenames==[]: 
            filenames.append(Tagdict["Directory"][i]+"\\"+Tagdict["File Name"][i])
        elif len(filenames)>1:
            for filename in filenames:
                if os.path.isfile(filename.replace(Tagdict["Directory"][i],Tagdict["Directory"][i]+dir)): continue
                shutil.copy2(filename, Tagdict["Directory"][i]+dir) 
            filenames=[]    
    #shutil.copy2("filename","destdir")
    #exclude is_series and SequenceNumber>1 
    #more than one picture within 10s    
    
def detectSunsetLig():
    Tagdict=readTags(inpath,subdir)
    if has_not_keys(Tagdict,keys=["Directory","File Name","Scene Mode"]): return 
    dir="\\Sunset"
    time_old=giveDatetime()
    for i in range(len(list(Tagdict.values())[0])):
        if not os.path.isdir(Tagdict["Directory"][i]+dir):
            os.makedirs(Tagdict["Directory"][i]+dir)
        is_sun= Tagdict["Scene Mode"][i]=="Sun1" or Tagdict["Scene Mode"][i]=="Sun2"
        time=giveDatetime(Tagdict["Date/Time Original"][i])
        if 23<time.hour or time.hour<17: continue
        if not is_sun: continue
        filename=Tagdict["Directory"][i]+"\\"+Tagdict["File Name"][i]
        if os.path.isfile(filename.replace(Tagdict["Directory"][i],Tagdict["Directory"][i]+dir)): continue
        shutil.copy2(filename, Tagdict["Directory"][i]+dir)   
    #evening and Sun1 or Sun2 are used      
    
def filterSeries():
    import re
    '''
    r"^[-a-zA-Z0-9]+(_[-a-zA-Z0-9]*)?+_[0-9]+B[1-7](_[a-zA-Z0-9]*)?"
    
    [0-9]+B[1-7]
    [0-9]+S[0-9]+
    '''
    BList=[]
    skipdirs=["B"+str(i) for i in range(1,8)]+["S","single"]
    
    print(inpath)
    #print(skipdirs)
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        print(dirpath, len(dirnames), len(filenames))
        if not subdir and not inpath==dirpath: continue
        if any([skipdir==dirpath.split("\\")[-1] for skipdir in skipdirs]): continue
        #dir=dirpath.replace(inpath,"")+"\\"
        counter_old="000"
        counter2_old="0"
        BList=[]
        for filename in filenames:
            #example: filename="MS17-4_552B2.JPG"
            if not ".JPG" in filename: continue
            match = re.search("_([0-9]+)B([1-7])",filename)
            if match:
                counter,counter2=match.groups()
                if not counter==counter_old:
                    moveFiles2(BList,dirpath,"B"+counter2_old)  
                    BList=[]
                BList.append(filename)
            else:    
                moveFiles2(BList,dirpath,"B"+counter2_old)   
                BList=[]    
                match = re.search("_([0-9]+)S([0-9]+)",filename)
                if match:
                    counter,counter2=match.groups()
                    moveFile(filename,dirpath,"S")   
                    
                else:
                    counter="000"
                    counter2="0"
                    moveFile(filename,dirpath,"single")
            counter_old=counter
            counter2_old=counter2
        moveFiles2(BList,dirpath,"B"+counter2_old)     
        
    return    
        
def filterSeries_back():
    skipdirs=["B"+str(i) for i in range(1,8)]+["S","single"]
    
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        print(dirpath, len(dirnames), len(filenames))
        if not subdir and not inpath==dirpath: continue
        if not any([skipdir in dirpath for skipdir in skipdirs]): continue
        for filename in filenames:
            if not ".JPG" in filename: continue     
            os.rename(dirpath+"\\"+filename, os.path.dirname(dirpath)+"\\"+filename)    
        #os.path.delete(os.path.dirname(dirpath))    
            
def renameHDR(mode="HDRT",ext=".jpg",folder="HDR"):
    import re

    matchreg=r"^([-\w]+)_([0-9]+)B1([-\w\s'&]*)_2\3"  
    matchreg2=r"^([-a-zA-Z0-9]+)[-a-zA-Z_]*_([0-9]+)([-\w\s'&]*)_([0-9]+)\3"  
    for (dirpath, dirnames, filenames) in os.walk(inpath):  
        print("Folder: "+ dirpath)
        if not subdir and not inpath==dirpath: continue
        if not folder=="" and not folder==dirpath.split("\\")[-1]: continue
        print("Folder: "+ dirpath)
        for filename in filenames:
            if mode in filename: continue
            match = re.search(matchreg,filename)
            if not match: 
                print("use reg2:",filename)
                match = re.search(matchreg2,filename)
            if match:
                filename_new=match.group(1)+"_"+match.group(2)+"_"+mode+match.group(3)+ext
                #print(match.groups())
                if os.path.isfile(dirpath+"\\"+filename_new):
                    i=2
                    while os.path.isfile(dirpath+"\\"+filename_new):
                        filename_new=match.group(1)+"_"+match.group(2)+"_"+mode+"%d"%i+match.group(3)+ext
                        i+=1    
                #print(filename_new)     
                os.rename(dirpath+"\\"+filename, dirpath+"\\"+filename_new)    
            else:
                match = re.search(matchreg2,filename)
                print("no match:",filename)
    
    
def rotate(mode="HDRT",sign=1,folder="HDR",override=True):

    #Rotation: Rotate 90 CW or Rotate 270 CW
    #Rotate back 
    
    # Import Pillow:
    from PIL import Image

    if not ":\\" in inpath: inpath=standardDir+inpath
    if not os.path.isdir(inpath): return

    NFiles=0    
    timebegin=dt.datetime.now()
    
    for (dirpath, dirnames, filenames) in os.walk(inpath):  
        if not subdir and not inpath==dirpath: continue
        if not folder=="" and not folder==dirpath.split("\\")[-1]: continue
        print(dirpath)
        Tagdict=readTags(dirpath,subdir)
        if has_not_keys(Tagdict,keys=["Directory","File Name","Rotation"]): return 
        leng=len(list(Tagdict.values())[0])   
        for i in range(leng):
            # Load the original image:
            if not mode in Tagdict["File Name"][i]: continue
            if Tagdict["Rotation"][i]=="Horizontal (normal)": continue
            else:
                name=Tagdict["Directory"][i]+"\\"+Tagdict["File Name"][i]
                print(Tagdict["File Name"][i])
                img = Image.open(name)
                if Tagdict["Rotation"][i]=="Rotate 90 CW": img_rot = img.rotate(90*sign, expand=True)
                elif Tagdict["Rotation"][i]=="Rotate 270 CW": img_rot = img.rotate(-90*sign, expand=True)
                else: continue
                NFiles+=1
                if not override: name=name[:name.rfind(".")]+"_rot"+name[name.rfind("."):] 
                img_rot.save(name, 'JPEG', quality=99,exif=img.info['exif'])     

    timedelta=dt.datetime.now()-timebegin    
    print("rotated %3d files in %2d min, %2d sec"%(NFiles,int(timedelta.seconds/60),timedelta.seconds%60)) 

        
def adjustDate(timeshift=[-1,0,0]):
  
    delta_t=dt.timedelta(hours=timeshift[0],minutes=timeshift[1],seconds=timeshift[2])
    Tagdict=readTags(inpath,subdir)
    if has_not_keys(Tagdict,keys=["Directory","File Name","Date/Time Original"]): return 
    leng=len(list(Tagdict.values())[0])   
    for i in range(leng):
        name=Tagdict["Directory"][i]+"\\"+Tagdict["File Name"][i]
        time=giveDatetime(Tagdict["Date/Time Original"][i])
        newtime=time+delta_t
        timestring=dateformating(newtime,"YYYY:MM:DD HH:mm:ss")
        callExiftool(name, ["-DateTimeOriginal='"+timestring+"'"])
    
def addLocation(country="Germany",city="Nueremberg",location="Location"):

    Tagdict=readTags(inpath,subdir)
    if has_not_keys(Tagdict,keys=["Directory","File Name","Date/Time Original"]): return 
    leng=len(list(Tagdict.values())[0])   
    for i in range(leng):
        name=Tagdict["Directory"][i]+"\\"+Tagdict["File Name"][i]
        optionCountry = "-Country="+country+"\ testSpace"
        optionCity = "-City="+city
        optionLocation = "-Location="+location
        
        callExiftool(name, [optionCountry,optionCity,optionLocation])

def nameToExif():

    import re

    Tagdict=readTags(inpath,subdir)
    if has_not_keys(Tagdict,keys=["Directory","File Name","Date/Time Original"]): return 
    leng=len(list(Tagdict.values())[0])   
    
    for i in range(leng):
        
        id=''
        title=''
        state= ''
        filename=Tagdict["File Name"][i]
        filename=filename[:filename.rfind(".")]        
        filename_splited=filename.split('_')
        if len(filename_splited)>1:
            found=False
            for subname in filename_splited:
                if found: 
                    print(subname)
                    if subname in SceneToTag: state=SceneToTag[subname]
                    else: title+=subname+"_"
                else:
                    id+=subname+"_"
                    if np.chararray.isdigit(subname[0]) and np.chararray.isdigit(subname[-1]): found=True
        if(id != ''): id=id[:-1] 
        if(title != ''): title=title[:-1]    
        options=[]
        options.append("-ImageDescription="+id )
        options.append("-Title="+title)   
        options.append("-State="+state)   
        name=Tagdict["Directory"][i]+"\\"+Tagdict["File Name"][i]
        callExiftool(name, options)
        
def test():
    print(inpath,subdir)   
