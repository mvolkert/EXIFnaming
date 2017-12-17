#!/usr/bin/env python3

'''
collection of Tag tools
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

from constants import unknownTags



def getRecMode(filename="",Advanced_Scene_Mode="",Image_Quality="",Video_Frame_Rate=""):
    if any(ext in filename for ext in ['.mp4','.MP4']):
        #print(Advanced_Scene_Mode,Image_Quality)
        if Image_Quality=="4k Movie" and Video_Frame_Rate=="29.97":
            return "4KB"
        elif Image_Quality=="4k Movie":
            return "4K"
        elif Image_Quality=="Full HD Movie" and Advanced_Scene_Mode=="HS":
            return "HS"
        elif Image_Quality=="Full HD Movie" and Advanced_Scene_Mode=="Off":
            return "FHD" 
        else: return "" 
    else:
        return "" 

def giveDatetime(datestring="2000:01:01 00:00:00.000"):
    args=[]
    for sub1 in datestring.split():
        for sub2 in sub1.split(":"):
            if "." in sub2:
                args.append(int(sub2.split(".")[0]))
                args.append(int(sub2.split(".")[1])*1000)
            else: args.append(int(sub2))    
    time=dt.datetime(*args)
    return time
    
    
def newdate(time,time_old,use_day=True):
    #adjust datebreak at midnight
    timedelta = time - time_old
    timedelta_seconds=timedelta.days*3600*24+timedelta.seconds
    if not time_old.year==time.year or not time_old.month==time.month or (use_day and not time_old.day==time.day): newdate.dateswitch=True
    if timedelta_seconds>3600.*4 and newdate.dateswitch:
        newdate.dateswitch=False 
        return True
    else: return False
newdate.dateswitch=False    
    
def dateformating(time,dateformat):
    if dateformat.count('Y')>4: yfirst=0
    else: yfirst=4-dateformat.count('Y')
    #m="%02d"%time.month
    #d="%02d"%time.day
    y=dateformat.count('Y')
    m=dateformat.count('M')
    d=dateformat.count('D')
    n=dateformat.count('N')
    h=dateformat.count('H')
    min=dateformat.count('m')
    sec=dateformat.count('s')
    daystring=dateformat
    if y>0: daystring=daystring.replace('Y'*y,str(time.year)[yfirst:])
    if m>0: daystring=daystring.replace('M'*m,("%0"+str(m)+"d")%time.month)
    if d>0: daystring=daystring.replace('D'*d,("%0"+str(d)+"d")%time.day)    
    if n>0: 
        #print("1",dateformating.numberofDates)
        dateformating.numberofDates+=1
        #print("2",dateformating.numberofDates)
        daystring=daystring.replace('N'*n,("%0"+str(n)+"d")%dateformating.numberofDates)
    #print("3",daystring)
    if h>0: daystring=daystring.replace('H'*h,("%0"+str(h)+"d")%time.hour)   
    if min>0: daystring=daystring.replace('m'*min,("%0"+str(min)+"d")%time.minute)   
    if sec>0: daystring=daystring.replace('s'*sec,("%0"+str(sec)+"d")%time.second)   
    return daystring
dateformating.numberofDates=0  

def renameTemp(DirectoryList,FileNameList):
    if not len(DirectoryList)==len(FileNameList): 
        print("error in renameTemp: len(DirectoryList)!=len(FileNameList)")
        return ""
    temppostfix="temp"
    for i in range(len(FileNameList)):
        os.rename(DirectoryList[i]+"\\"+FileNameList[i], DirectoryList[i]+"\\"+FileNameList[i]+temppostfix)
    return temppostfix 

def renameTemp2(inpath):
    temppostfix="temp"
    if not os.path.isdir(inpath): 
        print('not found directory: '+inpath)
        return 
    for (dirpath, dirnames, filenames) in os.walk(inpath): 
        for filename in filenames:
            os.rename(dirpath+"\\"+filename, dirpath+"\\"+filename+temppostfix)
    return temppostfix       

    
def sortDict(indict={"foo":[1,3,2],"bar":[8,7,6]},keys=["foo"]):
    indictkeys=list(indict.keys())
    cols=[indictkeys.index(key) for key in keys] 
    lists=[]
    for i in range(len(list(indict.values())[0])):
        vals=[]
        for key in indictkeys: 
            try: vals.append(indict[key][i])
            except: print("sortDict_badkey",key)
        lists.append(vals)  
        #lists.append([indict[key][i] for key in indict])   
        
    for col in reversed(cols):
        lists=sorted(lists, key=operator.itemgetter(col))
    outdict=dict()
    for key in indict:
        outdict[key]=[]
    for vals in lists:
        for i,val in enumerate(vals):
            outdict[indictkeys[i]].append(val)
    return outdict   

def has_not_keys(indict,keys=[]):
    if keys==[]: return True
    for key in keys:
        if not key in indict: 
            print(key+" not in dict")
            return True
    return False    
        
def readTags(inpath=os.getcwd(),subdir=False,Fileext=".JPG"):
    outdict=OrderedDict()
    NFiles=0
    date_org_name="Date/Time Original"
    
    if not ":\\" in inpath: inpath=standardDir+inpath
    
    if not os.path.isdir(inpath): 
        print('not found directory: '+inpath)
        return outdict

    for (dirpath, dirnames, filenames) in os.walk(inpath):
        for filename in filenames: 
            if not Fileext.lower()==filename.lower()[filename.rfind("."):]: continue
            if not subdir and not inpath==dirpath:continue
            NFiles+=1
    print("prozess",NFiles,"Files in ",inpath,"subdir:",subdir) 
    response = input("Do you want to continue ?")

    timebegin=dt.datetime.now()
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        if not subdir and not inpath==dirpath:break
        #todo: bug: case insensitive
        if len([filename for filename in filenames if Fileext.lower() in filename.lower()])==0: 
            print("  No matching files in ",dirpath.replace(inpath+"\\",""))
            continue
        out= callExiftool(dirpath+"\\*"+Fileext,[],False)    
        out=out[out.find("ExifTool Version Number"):]
        out_split=out.split("========")
        #if len(out_split)<2: return {}
        if len(out_split)>1: print("%4d tags extracted in "%len(out_split),dirpath.replace(inpath+"\\",""))
        else: print("%4d tags extracted in "%1,dirpath.replace(inpath+"\\",""))
        for tags in out_split:
            tagNamesDetected=[] #to check for multiple occurrences within one tag information
            for tag in tags.split("\\r\\n"):
                try:
                    key=tag.split(": ")[0].strip()
                    val=tag.split(": ")[1].strip()
                except: 
                    continue  
                if key in tagNamesDetected: continue        
                else: tagNamesDetected.append(key)
                if (key,val) in unknownTags: val=unknownTags[(key,val)]    
                outdict.setdefault(key,[]).append(val) 

    if len(outdict)==0: return outdict           
    keys=list(outdict.keys()) 
    #print(outdict)
    badkeys=[]    
    for key in keys:
        #print(key,len(outdict[key]))
        if not len(outdict[key])==len(outdict["File Name"]): 
            badkeys.append(key)
            del outdict[key]   
    print("badkeys:",badkeys)
    if date_org_name in badkeys: 
        print("error: "+date_org_name+" in badkeys")
        return {}    
    outdict=sortDict(outdict,[date_org_name])#"Directory",
    dirs=outdict["Directory"].copy()
    outdict["Directory"]=[]
    for dir in dirs:
        outdict["Directory"].append(dir.replace("/","\\"))   
    timedelta=dt.datetime.now()-timebegin    
    print("elapsed time: %2d min, %2d sec"%(int(timedelta.seconds/60),timedelta.seconds%60))        
    return outdict                 

def readTag_fromFile(inpath=os.getcwd(),subdir=False,Fileext=".JPG"):
    '''not tested'''
    dirname=scriptDir+inpath.replace(standardDir,'')    
    if not os.path.isdir(dirname):  os.makedirs(dirname)    
    Tagdict=np.load(dirname+"\\Tags"+Fileext)["Tagdict"].item()
    if isfile(Tagdict["Directory"][0]+"\\"+Tagdict["File Name"][0]):
        print("load")
    elif isfile(Tagdict["Directory"][0]+"\\"+Tagdict["File Name new"][0]):
        Tagdict["File Name"]=list(Tagdict["File Name new"])
        Tagdict["File Name new"]=[]
        print("switch")
    else:
        print("load again")
    return Tagdict
    
def getPostfix_old(filename):
    postfix=''
    filename_splited=filename.split('_')
    if postfix_stay and len(filename_splited)>1:
        post=filename_splited[-1]
        post2=post[post.rfind(".")-1]
        if not np.chararray.isdigit(post2): postfix="_"+post[:post.rfind(".")]
    return  postfix       
        
def getPostfix(filename,postfix_stay=True):
    postfix=''
    filename=filename[:filename.rfind(".")]        
    filename_splited=filename.split('_')
    if postfix_stay and len(filename_splited)>1:
        found=False
        for subname in filename_splited:
            if found: postfix+="_"+subname
            elif np.chararray.isdigit(subname[0]) and np.chararray.isdigit(subname[-1]): found=True

    return  postfix   
    
def moveFiles(filenames,path):
    if os.path.isdir(path): 
        print("directory already exists: ",path)
        return 
    if len(filenames) == 0: return
    os.makedirs(path)
    for filename in filenames:
        os.rename(filename[0]+"\\"+filename[1], path+"\\"+filename[1]) 

def moveFiles2(filenames,dirpath,subpath):
    if len(filenames) == 0: return
    os.makedirs(dirpath+"\\"+subpath, exist_ok=True)
    for filename in filenames:                    
        os.rename(dirpath+"\\"+filename, dirpath+"\\"+subpath+"\\"+filename)

def moveFile(filename,dirpath,subpath):
    os.makedirs(dirpath+"\\"+subpath, exist_ok=True)             
    os.rename(dirpath+"\\"+filename, dirpath+"\\"+subpath+"\\"+filename)
    
def moveFile2(filename,oldpath,newpath):
    os.makedirs(newpath, exist_ok=True)             
    os.rename(oldpath+"\\"+filename, newpath+"\\"+filename)    
 
def renameInPlace(dirpath,oldFilename,newFilename):            
    os.rename(dirpath+"\\"+oldFilename, dirpath+"\\"+newFilename)
  
def searchDirByTime(dirDict,time,jump):
    timedelta=dt.timedelta(seconds=jump)
    for lasttime in list(dirDict.keys()):
        timedelta_new=time-lasttime
        timedelta_new_sec=timedelta_new.days*3600*24+timedelta_new.seconds
        if timedelta_new_sec<timedelta.seconds: 
            timedelta=timedelta_new
            return dirDict[lasttime] 
    return None   

def callExiftool(name, options=[],override=True):

    list=["exiftool", name] + options
    if override: list.append("-overwrite_original_in_place")
    proc = subprocess.Popen(list, stdout=subprocess.PIPE)#, shell=True 
    (out, err) = proc.communicate()
    return str(out)
    