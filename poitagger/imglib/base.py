import os
import struct
from io import BytesIO
from datetime import datetime
import logging

from PIL import Image as PILImage
from PIL import ImageFile
import numpy as np
from bs4 import BeautifulSoup
import xmltodict
from timezonefinder import TimezoneFinder
import pytz

import nested
import piexif
from tags import *
from jfif_utils import *
import jfif

logger = logging.getLogger(__name__)
ImageFile.LOAD_TRUNCATED_IMAGES = True


class ImageBaseClass(object):
    maker = ""
    def __init__(self, filepath=None,ifd=None,rawdata= b'',img=None,onlyheader=False):
        self.header = {"main":{},"general":{},"file":{},"image":{},"camera":{0:{}},"position":{},"time":{},}
        #self.__version__ =  
        self.ifd = ifd
        self.rawdata = rawdata
        self.img = img
        self.thumbnail = None
        self.onlyheader = onlyheader
        self.timezone = TimezoneFinder()
        
        if os.path.exists(filepath): 
            filename = os.path.basename(str(filepath))
            self.header["file"]["Path"]=filepath.replace("\\","/")
            self.header["file"]["Name"]=filename
            self.header["file"]["Extension"]=os.path.splitext(filename)[1]
            self.header["file"]["Modified"]=datetime.fromtimestamp(os.path.getmtime(filepath)).astimezone().isoformat(" ")#.strftime("%Y-%m-%d %H:%M:%S")
            self.header["file"]["Created"]=datetime.fromtimestamp(os.path.getctime(filepath)).astimezone().isoformat(" ")#.strftime("%Y-%m-%d %H:%M:%S")
            size = os.path.getsize(filepath)
            self.header["file"]["Size"]= "{:.2f} kB".format(size/1024)
    
            
    def tzawareDateTime(self,dt):
        lat = self.header["position"]["Latitude"]
        lon = self.header["position"]["Longitude"]
        self.timezone.timezone_at(lng=lon, lat=lat)
    
    def load_xmp(self,rawdata):
            xmp_start = rawdata.lower().find(b"<rdf:rdf")
            xmp_end = rawdata.lower().find(b"</rdf:rdf")
            xmp_str = rawdata[xmp_start:xmp_end+10]
            if len(xmp_str)>0:
                xmp_bs = BeautifulSoup(xmp_str,"lxml")
                xmp_od = xmltodict.parse(bytes(str(xmp_bs.find("rdf:rdf")),"utf-8"))
                self.xmp = nested.Nested(xmp_od.get("rdf:rdf").get("rdf:description"),nested.reduce_rdf, dicttype=dict).data
            else:
                self.xmp = {}
    
    def image(self):
        return self.images[self.header["main"]["CurrentImage"]] 
        
    
    def imagetype(self,cameraid="0"):
        size = self.header["camera"][cameraid].get("FocalPlaneXResolution",0)*self.header["camera"][cameraid].get("FocalPlaneYResolution",0) 
        if size == 0:
            return "undefined"
        elif size < 1000000:
            return "thermal"
        else:
            return "vis"
            
    def load_exif(self):
        self.exif = {}
        for ifdkey, ifd in self.ifd.items():
            if ifdkey == "thumbnail":
                try:
                    self.thumbnail = np.array(PILImage.open(BytesIO(ifd))) 
                except:
                    self.thumbnail = ifd
                    logger.warning("reading thumbnail failed")
                continue
            else:
                self.exif[ifdkey]={}

            if type(ifd)==dict:
                for k,v in ifd.items():
                    typ = piexif.TAGS[ifdkey][k]["type"]
                    #print("EXIF:",piexif.TAGS[ifdkey][k]["name"],v)
                    if typ == piexif.TYPES.Ascii:
                        self.exif[ifdkey][piexif.TAGS[ifdkey][k]["name"]]=v.decode("utf8")
                    elif typ in [piexif.TYPES.Rational, piexif.TYPES.SRational]:
                        self.exif[ifdkey][piexif.TAGS[ifdkey][k]["name"]]=rational2float(v)
                    else:
                        self.exif[ifdkey][piexif.TAGS[ifdkey][k]["name"]]=v
                    
    