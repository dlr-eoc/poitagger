import os
import tifffile as tf
import utm
#if os.name == 'nt':
#    import win32api
import traceback
import re
import shutil
import struct 
from itertools import tee, islice, chain
from PyQt5 import QtGui
import numpy as np
from bs4 import BeautifulSoup
import dateutil.parser
import datetime
import pytz 
import math

SUPPORTED_EXTENSIONS = [".ara",".ar2",".raw",".jpeg",".jpg",".tif",".tiff"]


gray_color_table = [QtGui.qRgb(i, i, i) for i in range(256)]
def toQImage(im, copy=False):
    if im is None:
        return QtGui.QImage()
    if im.dtype == np.float64:
        im=np.uint8(im)
    if im.dtype == np.uint8:
        if len(im.shape) == 2:
            qim = QtGui.QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QtGui.QImage.Format_Indexed8).rgbSwapped()
            qim.setColorTable(gray_color_table)
            return qim.copy() if copy else qim
        elif len(im.shape) == 3:
            if im.shape[2] == 3:
                qim = QtGui.QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QtGui.QImage.Format_RGB888).rgbSwapped() 
                return qim.copy() if copy else qim
            elif im.shape[2] == 4:
                qim = QtGui.QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QtGui.QImage.Format_ARGB32).rgbSwapped()
                return qim.copy() if copy else qim

# def normalize(img,fliphor=False):
    # normalized = img - img.min()
    # normalized *= 255.0/normalized.max() 
    # flipped = np.fliplr(normalized) if fliphor else normalized
    # gray = np.array(flipped, dtype=np.uint8)         
    # return gray

def toBool(mystr):
    if str(mystr).lower() == "true":
        return True
    else: 
        return False
        
def normalize(img,fliphor=False,inverse=False):
    normalized = img - img.min()
    normalized = np.multiply(normalized, 255.0/normalized.max() )
    flipped = np.fliplr(normalized) if fliphor else normalized
    if inverse==True:
        flipped = 255 - flipped
    gray = np.array(flipped, dtype=np.uint8)         
    return gray
    
  
def mse(imageA, imageB):
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])
    return err

def shift(image,base=0,typ=np.uint16):
    mi = image.min()
    imageout = image + base - mi
    return imageout.astype(typ)


    
def round_up_to_even(f):
    return int(math.ceil(f / 2.)*2 )

def round_up_to_odd(f):
    return int(np.ceil(f) // 2 * 2 + 1)
    
def prev_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)   

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def differs_more(a,b,diff):
    if abs(b-a) > diff:
        return True
    else:
        return False
    

def get_if_exists(conf,section,option,type="str", default=None, trim=None):
    if conf.has_option(section,option):
        if type=="int":
            return int(conf.get(section,option)[:trim])
        if type=="float":
            return float(conf.get(section,option)[:trim])
        if type=="str":
            return conf.get(section,option)[:trim]
    else:
        return default

def find_in_list_of_dict(list_of_dictionaries,key,value):
    for listitem in list_of_dictionaries:
        if listitem[key] == value: 
            yield listitem 
    
def imgfiles(dirpath):
    for root, dirs, files in os.walk(dirpath):
        ImageFiles = []
        for i in sorted(files):
            if os.path.splitext(i.lower())[1] in SUPPORTED_EXTENSIONS:
                #print(i)
                ImageFiles.append(i)
        return root, ImageFiles
    return dirpath, []            

        

def to_timestamp(datestr):
    dt = dateutil.parser.parse(datestr)
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=pytz.utc)
    return int((dt - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())

    
# checks if the copter is flying or not.
# in the Header of the RAW-File of the Thermal images there is a 
# Start-Lat/Lon Value that will be set, when the rotors are started.
# That means, if the Value switches from latlon = (0,0) to a different value 
# the copter is flying
# This works only from Version 9 of the raw-Format (from March 2014 on)

def is_flying(path):
    try:
        with open(path,  "rb") as f:
            f.seek(224)  #muesste 220 sein , so wird nicht (lon,lat) sondern (lat,height) abgefragt  
            raw_s_ll = f.read(8)
        f.close()
        start_latlon = struct.Struct("<II").unpack_from(raw_s_ll)    
    except:
        print("Can't read Header of File", path)
        #traceback.print_exc()
        return False
    if not start_latlon == (0,0):
        return True
    return False    

def get_latlon(path):
    try:
        with open(path, "rb") as f:
            f.seek(142)    
            raw_ll = f.read(8)
        f.close()
        latlon = struct.Struct("<II").unpack_from(raw_ll)    
    except:
        print("get_ll: Can't read Header of File", path)
        #print traceback.print_exc()
        return None
    return latlon

def valid_gps(lat,lon):
    lat_ok = True if 1<=abs(lat)<90 else False
    lon_ok = True if 1<=abs(lon)<180 else False
    return True if lat_ok and lon_ok else False

def magnitudeorder(value,start=100):
    value= abs(value)
    order = start
    if value > math.pow(10,start):
        raise Exception("value bigger than magnitude (start)")
    if value>1.0:
        while value>1.0:
            order=order-1
            value=value/10
        return start-order
    else:
        if value < math.pow(10,-start):
            raise Exception("value smaler than magnitude (-start)")
        while value<1.0:
            order=order-1
            value=value*10
        return order-start
    
def adapt_magnitude(wrong,reference):
    digits = len(str(int(reference)))
    out = wrong*math.pow(10,magnitudeorder(reference/wrong))
    digout = len(str(int(out)))
    if digout == digits:
        return out
    else:
        return wrong*math.pow(10,magnitudeorder(reference/wrong)-digout+digits)

        
        
def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60);
    if direction == 'W' or direction == 'S':
        dd *= -1
    return dd;
    

def evaldiv(string):
    splitted = string.split("/")
    if len(splitted)>2: 
        raise Exception("too many '/' in string")
    elif len(splitted)== 2:
        zaehler, nenner = splitted 
    else:
        zaehler, nenner = splitted[0], 1
    return float(zaehler) / float(nenner)

def check_folder(files):
    for name in sorted(files,reverse=True):
        (base,ext) = os.path.splitext(name) 
        if (ext.lower() == ".raw") or (ext.lower()== ".ara"):
            try:
                infile = os.path.join(root,name)
                if not is_flying(infile):
                    os.remove(infile)
                    break    
            except:
                pass

                
def join_folders(indir,outdir):
    """
    this moves the files of the SD-Card (indir) to the outdir and 
    merges them to the folders "FlugXXX/FlirSD" where XXX are ascending integers.   
    """
    flugnr = 0
    dirs = os.listdir(outdir)
    outdirlist = []
    error = False
    for i in dirs :
        if i[:4]=="Flug":
            if int(i[4:7])>flugnr:
                flugnr = int(i[4:7])
    lastfile = 0
    flugnr += 1
    if not indir:
        return ([],True)
    for root, dirs, files in sorted(os.walk(indir)):
        (updir,dirbase) =os.path.split(root)
        if not (dirbase[:4]=="FLIR"): continue
        
        for name in sorted(files):
            (base,ext) = os.path.splitext(name) 
            if (ext.lower() == ".raw") or (ext.lower()== ".ara"):
                try:
                    infile = os.path.join(root,name)
                    if not is_flying(infile):
                        os.remove(infile)
                        continue
                    if (int(base)<lastfile):
                        flugnr += 1
                    odf = os.path.join(outdir,"Flug%03d"%flugnr)
                    if not os.path.exists(odf):
                        os.makedirs(odf)
                    od = os.path.join(odf,"FlirSD")
                    if not os.path.exists(od):
                        print("Outdir:", od) 
                        os.makedirs(od)
                        outdirlist.append(od)
                    lastfile = int(base)
                    outfileraw = os.path.join(od, base + ".ARA")
                    print(infile)
                    os.rename(infile,outfileraw) #shutil.copy
                except:
                    error = True
                    print(traceback.print_exc())
            else:
                print(base, ext)
                raise Exception("There is an unexpected filetype in the folder")
        try:
            os.rmdir(root)
        except:
            print("%s is not empty" % root)
            error = True
    return (outdirlist,error)


def join_folders2(flugnr,indir,outdir,remove_noneflight_images=True):
    """
    this moves the files of the SD-Card (indir) to the outdir and 
    merges them to the folders "FlugXXX/FlirSD" where XXX are ascending integers.   
    """
    dirs = os.listdir(outdir)
    outdirlist = []
    error = False
    lastfile = 0
    flugnr += 1
    if not indir:
        return ([],True)
    for root, dirs, files in sorted(os.walk(indir)):
        (updir,dirbase) =os.path.split(root)
        if not (dirbase[:4]=="FLIR"): continue
        
        for name in sorted(files):
            (base,ext) = os.path.splitext(name) 
            if (ext.lower() == ".raw") or (ext.lower()== ".ara"):
                try:
                    infile = os.path.join(root,name)
                    if remove_noneflight_images:
                        if not is_flying(infile):
                            os.remove(infile)
                            continue
                    if (int(base)<lastfile):
                        flugnr += 1
                    odf = os.path.join(outdir,"Flug%03d"%flugnr)
                    if not os.path.exists(odf):
                        os.makedirs(odf)
                    od = os.path.join(odf,"FlirSD")
                    if not os.path.exists(od):
                        print("Outdir:", od) 
                        os.makedirs(od)
                        outdirlist.append(od)
                    lastfile = int(base)
                    outfileraw = os.path.join(od, base + ".ARA")
                    print(infile)
                    os.rename(infile,outfileraw) #shutil.copy
                except:
                    error = True
                    print(traceback.print_exc())
            else:
                print(base, ext)
                raise Exception("There is an unexpected filetype in the folder")
        try:
            os.rmdir(root)
        except:
            print("%s is not empty" % root)
            error = True
    return (outdirlist,error)

    
# def getSDCardPath(namestart="IR_"):
    # if os.name == 'nt':
        # for element in win32api.GetLogicalDriveStrings().split("\x00")[:-1]:
            # try:
                # driveinfo = win32api.GetVolumeInformation(element)
                # if driveinfo[0][:len(namestart)]==namestart:
                    # return element
            # except:
                # print("Drive %s is not readable" % element)
        # return False
    # else:
        # raise Exception("Automatic detection of SD-Card  on Linux is not yet implemented!")
        # return False
        
def set_filenames(infile,md,YEAR,CAMERA):
    UAVTYPE = md["uav_owner"][0]
    YEAR_ID = YEAR[3]
    (irpath,filename) = os.path.split(infile)
    (campaignpath, irdir) = os.path.split(irpath)
    (rootpath, campaigndir) = os.path.split(campaignpath)
    POS = campaigndir[4:7]
    (fbn,ext) = os.path.splitext(filename)    
    if fbn[:2]== YEAR_ID+UAVTYPE:
        print("Dateiname unveraendert!")
        (base,ext) = os.path.splitext(infile)
        outrawfile = base + ".ARA"
        outfile = base + ".jpg"
        outtxt =  base + ".txt" 
        return (outrawfile,outfile,outtxt)
    IMGNR = fbn[4:]
    #print IMGNR
    if is_number(IMGNR): 
        base = os.path.join(irpath,YEAR_ID+UAVTYPE+POS+IMGNR+CAMERA)
        outrawfile = base + ".ARA"
        outfile = base + ".jpg"
        outtxt =  base + ".txt" 
        return (outrawfile,outfile,outtxt)

        
'''
Convert Dictionaries with Lists in it to Dictionary with enumerated nested Dictionary         
>>>In = {"a":[{"x":1,"y":10},{"x":2,"y":20}],"b":{"c":1,"d":2}}
>>>out = parseDict(In)
>>>print (out)
{'a': {0: {'x': 1, 'y': 10}, 1: {'x': 2, 'y': 20}}, 'b': {'c': 1, 'd': 2}}
'''

def listToDict(l):
    nd = {}
    for k,v in enumerate(l):
        if isinstance(v, list):
            nd[str(k)] = listToDict(v)
        elif isinstance(v, dict):
            nd[str(k)] = parseDict(v)
        else:
            nd[str(k)] = v
    return nd

def parseDict(d):
    nd = {}        
    for k, v in d.items():
        if isinstance(v, list):
            nd[str(k)] = listToDict(v)
        elif isinstance(v, dict):
            nd[str(k)] = parseDict(v)
        else:
            nd[str(k)] = v
    return nd
            