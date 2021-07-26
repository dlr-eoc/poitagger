import numpy as np
import logging
import doctest
import os
import re
import utm
#import traceback

logger = logging.getLogger(__name__)

try:
    import exifread
    from PIL import Image as pilimage
    import struct
    import time
    import math
    import tifffile as tf
    import datetime
    import dateutil
except ImportError:
    logger.error("loading a module failed! maybe you can not read all types of images",exc_info=True)

from bs4 import BeautifulSoup
     
SUPPORTED_EXTENSIONS = [".ara",".ar2",".raw",".jpeg",".jpg",".tif",".tiff"]

class ERRORFLAGS(object):
    ALL_META = 0x0001
    LATLON = 0x0002
    BAROHEIGHT = 0x0004
    START_LATLON = 0x0008
    START_ELEVATION = 0x0010
    FAST_PITCH = 0x0020
    FAST_ROLL = 0x0040

class CHANGEDFLAGS(object):
    LAT = 0x0001
    LON = 0x0002
    BAROHEIGHT = 0x0004
    START_LATLON = 0x0008
    START_ELEVATION = 0x0010

class FLAGS(object):
    MOTORS_ON = 0x0001
    CAM_CHANGED = 0x0002
    FLIPPED_HOR = 0x0004
    FLIPPED_VER = 0x0008

BITDEPTH = {16:np.uint16,8:np.uint8,32:np.uint32,64:np.uint64}
    

def isotimestr(timestamp, millisec,tz_minutes_offset):
    tz = dateutil.tz.tzoffset(None, -tz_minutes_offset*60)
    fulltime = datetime.datetime.fromtimestamp(timestamp, tz) 
    fulltime += datetime.timedelta(milliseconds=millisec)
    return str(fulltime)
        
    
def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60);
    if direction == 'W' or direction == 'S':
        dd *= -1
    return dd;


def convert_rational(exifread_rational):
    rational_str = str(exifread_rational)
    p = re.compile(r'[\(, \)]+|[\[, \]]+')
    Lst1 = p.split(rational_str)[1:-1]
    Lst2 = []
    for i in Lst1:
        try:
            Lst2.append(int(i))
        except ValueError:
            Lst2.append(evaldiv(i))
    return Lst2

def evaldiv(string):
        splitted = str(string).split("/")
        if len(splitted)>2: 
            raise Exception("too many '/' in string")
        elif len(splitted)== 2:
            zaehler, nenner = splitted 
        else:
            zaehler, nenner = splitted[0], 1
        if float(nenner) != 0:    
            return float(zaehler) / float(nenner)
        return float(zaehler)
           
MARKER = {
b"\xff\xe0":"APP0" , # JFIF APP0 segment marker
b"\xff\xe1":"APP1" ,
b"\xff\xe2":"APP2" ,
b"\xff\xe3":"APP3" ,
b"\xff\xe4":"APP4" ,
b"\xff\xe5":"APP5" ,
b"\xff\xe6":"APP6" ,
b"\xff\xe7":"APP7" ,
b"\xff\xe8":"APP8" ,
b"\xff\xe9":"APP9" ,
b"\xff\xea":"APP10",
b"\xff\xeb":"APP11",
b"\xff\xec":"APP12",
b"\xff\xed":"APP13",
b"\xff\xee":"APP14",
b"\xff\xef":"APP15",
b"\xff\xc0":"SOF0" , # Start Of Frame (baseline JPEG) 
b"\xff\xc1":"SOF1" , # Start Of Frame (baseline JPEG) 
b"\xff\xc2":"SOF2" ,
b"\xff\xc3":"SOF3" ,
b"\xff\xc4":"SOF4" ,
b"\xff\xc5":"SOF5" ,
b"\xff\xc6":"SOF6" ,
b"\xff\xc7":"SOF7" ,
b"\xff\xc9":"SOF9" ,
b"\xff\xca":"SOF10",
b"\xff\xcb":"SOF11",
b"\xff\xcd":"SOF13",
b"\xff\xce":"SOF14",
b"\xff\xcf":"SOF15",
b"\xff\xc4":"DHT"  , # Define Huffman Table
b"\xff\xdb":"DQT"  , # Define Quantization Table
b"\xff\xda":"SOS"  ,  # Start of Scan
b"\xff\xc8":"JPG"  ,
b"\xff\xf0":"JPG0" ,
b"\xff\xfd":"JPG13",
b"\xff\xcc":"DAC"  , # Define Arithmetic Table, usually unsupport 
b"\xff\xdc":"DNL"  ,
b"\xff\xdd":"DRI"  , # Define Restart Interval
b"\xff\xde":"DHP"  ,
b"\xff\xdf":"EXP"  ,
b"\xff\xd0":"RST0" ,  # RSTn are used for resync, may be ignored
b"\xff\xd1":"RST1" ,
b"\xff\xd2":"RST2" ,
b"\xff\xd3":"RST3" ,
b"\xff\xd4":"RST4" ,
b"\xff\xd5":"RST5" ,
b"\xff\xd6":"RST6" ,
b"\xff\xd7":"RST7" ,
b"\xff\x01":"TEM"  ,
b"\xff\xfe":"COM"  } # Comment

           
FFF = [[0x02,"Raw Thermal Image Width", "H"],
        [0x04,"Raw Thermal Image Height", "H"],
        [0x20,"Emissivity", "f"],
        [0x24,'ObjectDistance',"f"],
        [0xd4,'CameraModel',"32s"],
        [0xf4, 'CameraPartNumber',"16s"],
        [0x28,'ReflectedApparentTemperature', "f"],
        [0x2c, 'AtmosphericTemperature', "f"],
        [0x30, 'IRWindowTemperature',    "f"],
        [0x34, 'IRWindowTransmission',   "f"],
        [0x3c, 'RelativeHumidity', "f"],
        [0x58 , 'PlanckR1', "f"],
        [0x5c , 'PlanckB',  "f"],
        [0x60 , 'PlanckF',  "f"],
        [0x070 , 'AtmosphericTransAlpha1', "f"],
        [0x074 , 'AtmosphericTransAlpha2', "f"],
        [0x078 , 'AtmosphericTransBeta1',  "f"],
        [0x07c , 'AtmosphericTransBeta2',  "f"],
        [0x080 , 'AtmosphericTransX',      "f"],
        [0x90 , 'CameraTemperatureRangeMax',    "f"],
        [0x94 , 'CameraTemperatureRangeMin',    "f"],
        [0x98 , 'CameraTemperatureMaxClip',     "f"],
        [0x9c , 'CameraTemperatureMinClip',     "f"],
        [0xa0 , 'CameraTemperatureMaxWarn',     "f"],
        [0xa4 , 'CameraTemperatureMinWarn',     "f"],
        [0xa8 , 'CameraTemperatureMaxSaturated',"f"],
        [0xac , 'CameraTemperatureMinSaturated',"f"],
        [0xd4 , 'CameraModel',                  "32s"],
        [0xf4 , 'CameraPartNumber',             "16s"],
        [0x104,  'CameraSerialNumber',          "16s"],
        [0x114,  'CameraSoftware',              "16s"],
        [0x170,  'LensModel',                   "32s"],
        [0x190 , 'LensPartNumber',    '16s'],
        [0x1a0 , 'LensSerialNumber',  '16s'],
        [0x1b4 , 'FieldOfView',       "f"],
        [0x1ec , 'FilterModel',       "16s"],
        [0x1fc , 'FilterPartNumber',  "32s"],
        [0x21c , 'FilterSerialNumber',"32s"],
        [0x308 , 'PlanckO',           'i'],
        [0x30c , 'PlanckR2',          "f"],
        [0x338 , 'RawValueMedian',    "H" ],
        [0x33c , 'RawValueRange',     "H" ],
        [0x384 , 'DateTimeOriginal',  "IIh"], 
        [0x390 , 'FocusStepCount', 'H'],
        [0x394 , 'Coretemp',  'f'],
        [0x3B0 , 'Lenstemp',  'f'],
        [0x45c , 'FocusDistance', "f"],
        [0x464 , 'FrameRate',   'H']]

FLIRFILEHEAD =  [[0x00,"Fileformat ID", "4s"],
        [0x04,"File origin", "16s"],
        [0x14,"File format version", "L"],
        [0x18,'Pointer to indexes',"L"],
        [0x1c,'Number of indexes',"L"],
        [0x20,'Next free index ID',"L"],
        [0x24,'Swap pattern', "H"],
        [0x26,'Spare', "7H"],
        [0x34,'reserved', "2L"],
        [0x3c,'Checksum', "L"]]

FLIRFILEINDEX = [[0x00,"MainType", "H"],
        [0x02,"SubType", "H"],
        [0x04,"Version", "L"],
        [0x08,'IndexID',"L"],
        [0x0c,'DataPtr',"L"],
        [0x10,'DataSize',"L"],
        [0x14,'Parent', "L"],
        [0x18,'ObjectNr', "L"],
        [0x1c,'Checksum', "L"]]

GEOMETRIC_INFO = [[0x00,"pixelSize", "H"],
        [0x02,"imageWidth", "H"],
        [0x04,"imageHeight", "H"],
        [0x06,'upperLeftX',"H"],
        [0x08,'upperLeftY',"H"],
        [0x0a,'firstValidX',"H"],
        [0x0c,'lastValidX', "H"],
        [0x0e,'firstValidY',"H"],
        [0x10,'lastValidY', "H"],
        [0x12,'detectorDeep',"H"],
        [0x14,'detectorID', "H"],
        [0x16,'upSampling', "H"],
        [0x18,'frameCtr', "H"],
        [0x1a,'minMeasRadius', "H"],
        [0x1c,'stripeFields', "c"],
        [0x1d,'reserved', "c"],
        [0x1e,'reserved1', "H"]]

    
    
class Image(object):
    header = {"camera":{},"uav":{},"image":{},"file":{},"gps":{},
         "calibration":{"geometric":{},"radiometric":{},"boresight":{}},"exif":{},
                    "thumbnail":{},     }
    exif = None
    xmp = None
    
    #def __init__(self):
        #logging.basicConfig(level=logging.INFO)
        #self.logger = logging.getLogger(__name__)
    
    def factory(imgpath,onlyheader=False):
        root, ext = os.path.splitext(imgpath)
        if ext.lower() in [".raw",".ara",".ar2"]: 
            return ImageAra(imgpath,onlyheader)
        elif ext.lower() in [".tif",".tiff"]: 
            return ImageTiff(imgpath,onlyheader)
        elif ext.lower() in [".jpg",".jpeg"]:     
            return ImageJpg(imgpath,onlyheader)
        
    factory = staticmethod(factory)
     
    

    def extract_xmp(self,string):
        try:
            text = evaldiv(self.xmp.find(string).text)
        except ValueError:
            text = self.xmp.find(string).text.strip()
        except AttributeError:
            return None
        return text

    # def convert_latlon(self,exif_deg,exif_ref):
       # # print("LATLONCONVERT",exif_deg,exif_ref)
        # deg = str(self.exif[exif_deg])
        # ref = str(self.exif[exif_ref])
        
        # p = re.compile(r'[\[, \]]+')
        # deglist = p.split(deg)[1:-1]
        # out = dms2dd(deglist[0],deglist[1],evaldiv(deglist[2]),ref)
     # #   print("OUT",out)
        # return out 
    def rational2float(self,rational_strlist):
        rational_str = str(rational_strlist)
        p = re.compile(r'[\(, \)]+|[\[, \]]+')
        return p.split(rational_str)[1:-1]
    
    def convert_latlon(self,exif_deg,exif_ref):
        ref = str(exif_ref)
        deglist = convert_rational(exif_deg)
        if len(deglist)==3:
            return dms2dd(deglist[0],deglist[1],deglist[2],ref)
        if len(deglist)==6:
            return dms2dd(float(deglist[0])/float(deglist[1]),float(deglist[2])/float(deglist[3]),float(deglist[4])/float(deglist[5]),ref)
        else:
            raise("Convert LatLon wrong size of input data")
    
    def extract_exif(self,string):
        try:
            text = evaldiv(self.exif.get(string))
        except ValueError:
            text = str(self.exif.get(string)).strip()
        except AttributeError:
            return None
        return text

    def load(self,imgpath,onlyheader=False):
        pass
        
    #self.logger.error("Open file failed", exc_info=True)


class ImageJpg(Image):
    bitdepth = 8
    def __init__(self,imgpath=None,bitsPerPixel=np.uint16,onlyheader=False):
        if imgpath is not None:
         #   print("start 0")
         #   self.start = time.time()
            self.load(imgpath,onlyheader=onlyheader)
        
    def load(self,imgpath,onlyheader=False):
        self.header = {"camera":{},"uav":{},"image":{},"file":{},"gps":{},
         "calibration":{"geometric":{},"radiometric":{},"boresight":{}},"exif":{},
                    "thumbnail":{},     }
        self.imgpath = imgpath
        self.filename = os.path.basename(str(imgpath))
        d, self.exif, self.xmp = self.get_meta(imgpath)
        logger.info(self.xmp)
        #self.t1 = time.time()
        #print(self.t1 - self.t6)
            
        self.segments = self.find_segments(d)
        self.width,self.height,self.channels = self.get_size(self.segments,d)
        
       # self.t2 = time.time()
       # print(self.t2 - self.t1)
        
        self.rwidth = int(str(self.exif.get("Raw Thermal Image Width",0)))
        self.rheight = int(str(self.exif.get("Raw Thermal Image Height",0 )))
        
        self.extract_flir(d,onlyheader)
        
        #self.t3 = time.time()
        #print(self.t3 - self.t2)
        #logger.info("IMAGE")
            
        if str(self.exif.get("Image Make","")) in ["DJI", "Hasselblad"]:
            logger.info("DJI")
            self.fill_header_dji()
            logger.info("after DJI FILL HEADER")
        elif str(self.exif.get("Image Make","")) == "FLIR":
            logger.info("FLIR")
            self.fill_header_flir()
        
        if not onlyheader:
            try:
                self.image = np.array(pilimage.open(imgpath))    
                if len(self.image.shape)==3:
                    (self.height, self.width,self.channels) = self.image.shape
                else:
                    (self.height,self.width) = self.image.shape
                    self.channels = 1
            except:
                logger.warning("can not load image %s" % imgpath)
    def find_segments(self,d):
        cpattern = re.compile(b"..|".join(MARKER.keys()))
        segments = []
        parentend = 0
        for m in cpattern.finditer(d):
            if len(m.group())>=4: 
                length = 256 * m.group()[2] + m.group()[3]
                id = MARKER[m.group()[:-2]]
            else:
                length = 0
                id = MARKER[m.group()]
            if m.start()>parentend:
                top = True
                parentend = m.start() + length
            else:
                top = False
            segments.append({"id":id, 
                "pos":m.start(),
                "len" : length,
                "top": top})
        
        return segments
      
    def get_size(self,segments,data):
        Width, Height, Channels = [],[],[]
        try:
            sof = [i for i in segments if i["id"]=="SOF0" and i["top"]==True ] #[0]
            for s in sof:
                p = s["pos"]
                precision = data[p+4]
                Height.append(struct.unpack(">H", data[p+5:p+7])[0])
                Width.append(struct.unpack(">H", data[p+7:p+9])[0])
                Channels.append(data[p+9])
            idx = Width.index(max(Width))
            return (Width[idx],Height[idx],Channels[idx])
        except:
            return (0,0,1)
            
        
    def get_meta(self,imgpath):
        exif = {}
        xmp = ""
        d = []
        try:
            #self.t4 = time.time()
            #print(self.t4 - self.start)
            with open(imgpath,"rb") as f:
                exif = exifread.process_file(f,details=False)
                d = f.read()
                
            #self.t5 = time.time()
            #print(self.t5 - self.t4)
        
            xmp_start = d.lower().find(b"<rdf:rdf")
            xmp_end = d.lower().find(b"</rdf:rdf")
            xmp_str = d[xmp_start:xmp_end+10]
            xmp = BeautifulSoup(xmp_str,"lxml")
           # self.t6 = time.time()
           # print(self.t6 - self.t5)
        
        except FileNotFoundError as e:
            logger.error(e)
        except:
            logger.error(e)
        return d, exif, xmp

    
    def extract_flir(self,bytearr,onlyheader):
        fffchunk = self.combine_flir_segments(bytearr)
        ffh = {}
        if str(self.exif.get("Image Make","")) == "DJI":
            self.endian = "<"
            print ("DJI Image")
        elif str(self.exif.get("Image Make","")) == "FLIR":
            self.endian = ">"
        else: 
            self.endian = ">"
        if len(fffchunk)<64:
            return
        #print (fffchunk[0:68])        
        for i in FLIRFILEHEAD:
            val = struct.unpack_from(">"+i[2],fffchunk[0:64],i[0])
            if "s" in i[2]:
                val = val[0].strip(b"\x00")
            name = i[1]
            ffh[name]=val[0]
        
       # print("FFH",ffh)
        indexes = ffh["Number of indexes"]
        FFI = []
        #print(fffchunk[64+0*32:96+14*32])
        for idx in range(0,indexes):
            ffi = {}
            for i in FLIRFILEINDEX:
                val = struct.Struct(">"+i[2]).unpack_from(fffchunk[64+idx*32:96+idx*32],i[0])
                if "s" in i[2]:
                    val = val[0].strip(b"\x00")
                name = i[1]
                ffi[name]=val[0]
            if ffi["MainType"]== 1:
                rawstart= ffi['DataPtr']
                rawend = rawstart + ffi['DataSize']
            if ffi["MainType"]== 32:
                basicstart= ffi['DataPtr']
                basicend = basicstart + ffi['DataSize']
            FFI.append(ffi)
       # print("FFI:",FFI)
        self.fff = self.flir_header(fffchunk[basicstart:basicend])
       # print("FFF",self.fff)
        
        if not onlyheader:
            self.rawbody = self.get_raw(fffchunk[rawstart:rawend])
        else:
            self.bitdepth = struct.Struct(">"+i[2]).unpack_from(fffchunk[rawstart:rawstart+2],0)
         #   print("BITDEPTH",self.bitdepth)
    def get_raw(self,bytearr):
        geom = {}
        for i in GEOMETRIC_INFO:
            val = struct.Struct("<"+i[2]).unpack_from(bytearr,i[0])
            if "s" in i[2]:
                val = val[0].strip(b"\x00")
            name = i[1]
            geom[name]=val[0]
        img = np.frombuffer(bytearr[32:], dtype="<u"+str(geom['pixelSize']),count=geom['imageWidth']*geom['imageHeight']) 
        img = np.reshape(img,(geom['imageHeight'],geom['imageWidth']))
        self.bitdepth = geom["pixelSize"]
        return img
    
    def flir_header(self,fffmeta):    
        fff = {}
        for i in FFF:
            val = struct.Struct(self.endian+i[2]).unpack_from(fffmeta,i[0])
            if "s" in i[2]:
                val = val[0].strip(b"\x00")
            name = i[1]
            fff[name]=val
        return fff    
    
    def combine_flir_segments(self,bytearr):
        flirdata = []
        start = 10
        arr = bytearr.split(b"\xff\xe1")
        for i in arr:
            if len(i)<6: continue
            if not i[2:6] == b"FLIR": continue    
            length = 256 * i[0] + i[1]
            if start<length:
                flirdata.append(i[start:length])
        return b"".join(flirdata)
        
       
    def correct_latlon(self, lat, lon):
        if abs(lat) > 90: 
            lat = lat * 10e-8
        elif abs(lat) < 1:
            lat = lat * 10e8
        if abs(lon) > 180:
            lon = lon * 10e-8
        elif abs(lon) < 1:
            lon = lon * 10e8
        return lat,lon
 
    def fill_header_flir(self):
        
       # print ("EXIF:", self.exif)
        self.header["file"]["name"] = self.filename
        self.header["image"]["width"] = self.rwidth if self.rwidth else self.width #self.extract_exif("Raw Thermal Image Width")
        self.header["image"]["height"] = self.rheight if self.rheight else self.height #self.extract_exif("Raw Thermal Image Height")
        self.header["image"]["bitdepth"] = self.bitdepth      
        
        self.header["camera"]["roll"] = self.extract_xmp("camera:roll") 
        #self.header["camera"]["yaw"] = self.extract_xmp("camera:yaw")
        self.header["camera"]["pitch"] = self.extract_xmp("camera:pitch") 
        self.header["camera"]["euler_order"] = "ZYX"
        self.header["camera"]["model"] = self.extract_exif("Image Model")
        self.header["camera"]["make"] = self.extract_exif("Image Make")
        self.header["uav"]["roll"] = self.extract_xmp("flir:mavroll")
        self.header["uav"]["yaw"] = self.extract_xmp("flir:mavyaw") 
        try:
            if not self.extract_xmp("td:uavaccx") in [None, ""]: # neues Grabber Skript 
                self.header["camera"]["yaw"] =  self.extract_xmp("camera:yaw")
            else:
                self.header["camera"]["yaw"] = self.extract_xmp("flir:mavyaw") + self.extract_xmp("camera:yaw")
            #self.extract_xmp("flir:mavyaw") +
        except:
            self.header["camera"]["yaw"] = -9999
        self.header["uav"]["pitch"] = self.extract_xmp("flir:mavpitch") 
        self.header["uav"]["euler_order"] = "ZYX"
        try:
            self.header["file"]["DateTimeOriginal"] = self.exif["EXIF DateTimeOriginal"]
        except:  
            print (self.exif)
            logger.warning("fill Date Time Original failed", exc_info=True)
        try:
            self.header["file"]["SubSecTimeOriginal"] = self.exif["EXIF SubSecTimeOriginal"]
        except:  
            logger.warning("fill SubSecTimeOriginal failed", exc_info=True)
        
        try:
            lat = self.convert_latlon(self.exif["GPS GPSLatitude"],self.exif["GPS GPSLatitudeRef"])
            lon = self.convert_latlon(self.exif["GPS GPSLongitude"],self.exif["GPS GPSLongitudeRef"])
            self.header["gps"]["latitude"], self.header["gps"]["longitude"] = self.correct_latlon(lat,lon)
        except:  pass
        try:
            self.header["gps"]["rel_altitude"]= self.extract_xmp("flir:mavrelativealtitude")
        except:  pass
        try:
            self.header["gps"]["abs_altitude"] = self.extract_exif("GPS GPSAltitude")
        except:  pass
        try:
            self.header["gps"]["timestamp"] = ":".join(str(x) for x in convert_rational(self.extract_exif("GPS GPSTimeStamp")))
        except:  pass
        try:
            self.header["gps"]["date"] = "-".join(self.extract_exif("GPS GPSDate").split(":")) 
        except:  pass
        
        try:
            UTM_Y,UTM_X,ZoneNumber,ZoneLetter = utm.from_latlon(self.header["gps"]["latitude"],self.header["gps"]["longitude"])
        except:  pass
        try:
            self.header["gps"]["UTM_X"] = UTM_X
            self.header["gps"]["UTM_Y"] = UTM_Y
            self.header["gps"]["UTM_ZoneNumber"] = ZoneNumber
            self.header["gps"]["UTM_ZoneLetter"] = ZoneLetter 
        except: pass
           
        
        self.header["camera"]["centralwavelength"] = self.extract_xmp("camera:centralwavelength") 
        self.header["camera"]["wavelengthfwhm"] = self.extract_xmp("camera:wavelengthfwhm") 
        self.header["camera"]["detectorbitdepth"] = self.extract_xmp("camera:detectorbitdepth")
        self.header["camera"]["tlineargain"] = self.extract_xmp("camera:tlineargain") 
        self.header["camera"]["gyrorate"] = self.extract_xmp("camera:gyrorate")
        self.header["camera"]["isnormalized"] = self.extract_xmp("camera:isnormalized") 
        self.header["camera"]["fnumber"] = self.extract_exif("Image FNumber")
        self.header["camera"]["focallength"] = self.extract_exif("Image FocalLength")
        
        self.header["file"]["mavversion"] = self.extract_xmp("flir:mavversionid")
        self.header["file"]["mavcomponent"] = self.extract_xmp("flir:mavcomponentid")
        self.header["file"]["exifversion"] = self.extract_exif("EXIF ExifVersion")
        
        try:
            self.header["camera"]['PartNumber'] = self.fff.get("CameraPartNumber","").decode("utf-8") 
            self.header["camera"]["SerialNumber"] = self.fff.get('CameraSerialNumber',"").decode("utf-8") 
        #    self.header["file"]["DateTimeOriginal"] = isotimestr(*self.fff.get("DateTimeOriginal",0))
        except:
            try:
                self.header["camera"]['PartNumber'] = self.fff.get("CameraPartNumber","")
                self.header["camera"]["serial"] = self.fff.get('CameraSerialNumber',"")
         #       self.header["file"]["DateTimeOriginal"] = self.fff.get("DateTimeOriginal",0)
        #self.header["file"]["modifydate"] = self.fff.get("DateTimeOriginal",0)
        #self.header["file"]["createdate"] = self.fff.get("DateTimeOriginal",0)
            except:
                pass
        try:
            self.header["gps"]["hor_accuracy"]= self.extract_xmp("camera:gpsxyaccuracy")
            self.header["gps"]["ver_accuracy"]= self.extract_xmp("camera:gpszaccuracy")
            self.header["gps"]["climbrate"] = self.extract_xmp("flir:mavrateofclimb") 
            self.header["gps"]["climbrateref"] = self.extract_xmp("flir:mavrateofclimbref")
            self.header["gps"]["abs_altituderef"] = self.extract_exif("GPS GPSAltitudeRef")
            self.header["gps"]["speed"] = self.extract_exif("GPS GPSSpeed")
            self.header["gps"]["speedref"] = self.extract_exif("GPS GPSSpeedRef")
            self.header["gps"]["version"] = self.extract_exif("GPS GPSVersionID")
                    
            
            self.header["image"]["colorspace"] = self.extract_exif("EXIF ColorSpace")
            self.header["image"]["componentsconfiguration"] = self.extract_exif("EXIF ComponentsConfiguration")
                    
            self.header["uav"]["rollrate"] = self.extract_xmp("flir:mavrollrate") 
            self.header["uav"]["yawrate"] = self.extract_xmp("flir:mavyawrate") 
            self.header["uav"]["pitchrate"] = self.extract_xmp("flir:mavpitchrate") 
            
            self.header["uav"]["xacc"] = self.extract_xmp("td:uavaccx") 
            self.header["uav"]["yacc"] = self.extract_xmp("td:uavaccy") 
            self.header["uav"]["zacc"] = self.extract_xmp("td:uavaccz") 
        except:
            pass
        
        try:    
            self.header["calibration"]["radiometric"]["R"] = float(self.fff.get("PlanckR1",(0))[0])
            self.header["calibration"]["radiometric"]["F"] = float(self.fff.get("PlanckF",(1))[0])
            self.header["calibration"]["radiometric"]["B"] = float(self.fff.get("PlanckB",(0))[0])
            self.header["calibration"]["radiometric"]["R2"] = float(self.fff.get("PlanckR2",(0))[0])
            self.header["calibration"]["radiometric"]["coretemp"] = self.fff.get("Coretemp",(1))[0]
          
            self.header["calibration"]["radiometric"]["timestamp"] = 0
            self.header["calibration"]["radiometric"]["IRWindowTemperature"] = float(self.fff.get("IRWindowTemperature",(0))[0])
            self.header["calibration"]["radiometric"]["IRWindowTransmission"] = float(self.fff.get("IRWindowTransmission",(1))[0])
        except:
            pass
        
            
        try:
            self.header["camera"]['CoreTemp'] = self.extract_xmp("camera:coretemp") 
            self.header["camera"]['FfcState'] = self.extract_xmp("camera:ffcstate") 
            self.header["camera"]['FfcDesired'] = self.extract_xmp("camera:ffcdesired") 
            self.header["camera"]['FrameCount'] = self.extract_xmp("camera:framecount") 
            self.header["camera"]['FocalLengthPixel'] = self.extract_xmp("camera:focallengthpixel") 
            self.header["camera"]['FOV'] = self.extract_xmp("camera:fov") 
            self.header["camera"]['Distortion'] = self.extract_xmp("camera:distortion") 
            self.header["camera"]['LastFfcFrameCount'] = self.extract_xmp("camera:lastffcframecount")
            self.header["camera"]['PartNumber'] = self.extract_xmp("camera:partnumber") 
            self.header["camera"]["SerialNumber"] = self.extract_xmp("camera:serialnumber") 
            self.header["camera"]['Firmware'] = self.extract_xmp("camera:firmware") 
                            
        except:
            pass
        
    def fill_header_dji(self):
        camroll = 0
        camyaw = 0
        campitch = 0
        uavroll = 0
        uavyaw = 0
        uavpitch = 0
        rel_altitude = 0
        rel_altitude = 0
        a = self.xmp.find("rdf:description")
        #if a == None: 
        #    logger.error("Not a compatible Image")
        #    return
        
        self.header["file"]["name"] = self.filename
        self.header["image"]["width"] = self.rwidth if self.rwidth else self.width #extract_exif("EXIF ExifImageWidth")
        self.header["image"]["height"] = self.rheight if self.rheight else self.height
        self.header["image"]["bitdepth"] = self.bitdepth     
        
        try:
            camroll = self.xmp.find("drone-dji:gimbalrolldegree").contents[0]
            camyaw = self.xmp.find("drone-dji:gimbalyawdegree").contents[0]
            campitch = self.xmp.find("drone-dji:gimbalpitchdegree").contents[0]
            uavroll = self.xmp.find("drone-dji:flightrolldegree").contents[0]
            uavyaw = self.xmp.find("drone-dji:flightyawdegree").contents[0]
            uavpitch = self.xmp.find("drone-dji:flightpitchdegree").contents[0]
            rel_altitude = self.xmp.find("drone-dji:relativealtitude").contents[0]
            abs_altitude = self.xmp.find("drone-dji:absolutealtitude").contents[0]
        except:
            logger.warning("this image either is no DJI image or has an old DJI format")
            
        try:
            self.header["camera"]["roll"] =  float(a.get("drone-dji:gimbalrolldegree",camroll))
            self.header["camera"]["yaw"] =  float(a.get("drone-dji:gimbalyawdegree",camyaw))
            self.header["camera"]["pitch"] = float(a.get("drone-dji:gimbalpitchdegree",campitch))
            self.header["camera"]["euler_order"] = "ZYX"
            self.header["camera"]["model"] = a.get("tiff:model",self.exif["Image Model"])
            self.header["camera"]["make"] = a.get("tiff:make",self.exif["Image Make"])
            self.header["uav"]["roll"] = float(a.get("drone-dji:flightrolldegree",uavroll))
            self.header["uav"]["yaw"] = float(a.get("drone-dji:flightyawdegree",uavyaw))
            self.header["uav"]["pitch"] = float(a.get("drone-dji:flightpitchdegree",uavpitch))
        except:
            logger.warning("no xmp-data",exc_info=true)
            
        self.header["uav"]["euler_order"] = "ZXY"
        self.header["gps"]["latitude"] = self.convert_latlon(self.exif["GPS GPSLatitude"],self.exif["GPS GPSLatitudeRef"])
        self.header["gps"]["longitude"] = self.convert_latlon(self.exif["GPS GPSLongitude"],self.exif["GPS GPSLongitudeRef"])
        try:
            self.header["gps"]["rel_altitude"]=float(a.get("drone-dji:relativealtitude",rel_altitude))
            self.header["gps"]["abs_altitude"]=float(a.get("drone-dji:absolutealtitude",abs_altitude))
        except:
            pass
        
        UTM_Y,UTM_X,ZoneNumber,ZoneLetter = utm.from_latlon(self.header["gps"]["latitude"],self.header["gps"]["longitude"])
        self.header["gps"]["UTM_X"] = UTM_X
        self.header["gps"]["UTM_Y"] = UTM_Y
        self.header["gps"]["UTM_ZoneNumber"] = ZoneNumber
        self.header["gps"]["UTM_ZoneLetter"] = ZoneLetter 
        
        self.header["gps"]["gpsmapdatum"] = self.extract_exif("GPS GPSMapDatum")
        try:
            self.header["camera"]["focallength"] = float(a.get("drone-dji:calibratedfocallength",0))
        
            self.header["file"]["about"]=a.get("rdf:about",0)
            self.header["file"]["modifydate"]=a.get("xmp:modifydate",0)
            self.header["file"]["createdate"]=a.get("xmp:createdate",0)
            self.header["file"]["DateTimeOriginal"]=self.extract_exif("EXIF DateTimeOriginal")
            self.header["file"]["format"]=a.get("dc:format",0)
            self.header["file"]["version"]=a.get("crs:version",0)
        except:
            pass
            
        try:
            #self.header["calibration"]["geometric"]["fx"]=float(a.get("drone-dji:calibratedfocallength"))
            self.header["calibration"]["geometric"]["cx"]=float(a.get("drone-dji:calibratedopticalcenterx",self.header["image"]["width"]/2.0))
            self.header["calibration"]["geometric"]["cy"]=float(a.get("drone-dji:calibratedopticalcentery",self.header["image"]["height"]/2.0))
        except:
            print("no calibration in exif header")
            print (self.extract_exif("EXIF FocalLengthIn35mmFilm"))
            #self.header["calibration"]["geometric"]["fx"] = self.extract_exif("EXIF FocalLength")
            #self.header["calibration"]["geometric"]["cx"] = self.width/2.0
            #self.header["calibration"]["geometric"]["cy"] = self.height/2.0
            
        self.header["image"]["make"] = self.extract_exif("Image Make")
        self.header["image"]["xresolution"] = self.extract_exif("Image XResolution")
        self.header["image"]["yresolution"] = self.extract_exif("Image YResolution")
        self.header["image"]["resolutionunit"] = self.extract_exif("Image ResolutionUnit")
        self.header["image"]["software"] = self.extract_exif("Image Software")
        self.header["image"]["datetime"] = self.extract_exif("Image DateTime")
        self.header["image"]["artist"] = self.extract_exif("Image Artist")
        self.header["image"]["copyright"] = self.extract_exif("Image Copyright")
        self.header["image"]["exifoffset"] = self.extract_exif("Image ExifOffset")
        self.header["image"]["gpsinfo"] = self.extract_exif("Image GPSInfo")
        
        self.header["thumbnail"]["compression"] = self.extract_exif("Thumbnail Compression")
        self.header["thumbnail"]["xresolution"] = self.extract_exif("Thumbnail XResolution")
        self.header["thumbnail"]["yresolution"] = self.extract_exif("Thumbnail YResolution")
        self.header["thumbnail"]["ResolutionUnit"] = self.extract_exif("Thumbnail ResolutionUnit")
        self.header["thumbnail"]["JPEGInterchangeFormat"] = self.extract_exif("Thumbnail JPEGInterchangeFormat")
        self.header["thumbnail"]["JPEGInterchangeFormatLength"] = self.extract_exif("Thumbnail JPEGInterchangeFormatLength")
        
        self.header["exif"]["FNumber"] = self.extract_exif("Exif FNumber")
        self.header["exif"]["DateTimeOriginal"] = self.extract_exif("EXIF DateTimeOriginal")
        self.header["exif"]["ApertureValue"] = self.extract_exif("EXIF ApertureValue")
        self.header["exif"]["FocalLength"] = self.extract_exif("EXIF FocalLength")
        self.header["exif"]["SubSecTimeOriginal"] = self.extract_exif("EXIF SubSecTimeOriginal")
        self.header["exif"]["FocalPlaneResolutionUnit"] = self.extract_exif("EXIF FocalPlaneResolutionUnit")
        
        try:
            self.header["calibration"]["radiometric"]["R"] = float(self.fff.get("PlanckR1",(0,))[0])
            self.header["calibration"]["radiometric"]["F"] = float(self.fff.get("PlanckF",(1,))[0])
            self.header["calibration"]["radiometric"]["B"] = float(self.fff.get("PlanckB",(0,))[0])
            self.header["calibration"]["radiometric"]["R2"] = float(self.fff.get("PlanckR2",(0,))[0])
            self.header["calibration"]["radiometric"]["timestamp"] = 0
            self.header["calibration"]["radiometric"]["IRWindowTemperature"] = float(self.fff.get("IRWindowTemperature",(0,))[0])
            self.header["calibration"]["radiometric"]["IRWindowTransmission"] = float(self.fff.get("IRWindowTransmission",(1,))[0])
            self.header["calibration"]["radiometric"]["Emissivity"] = float(self.fff.get("Emissivity",(1,))[0])
            self.header["calibration"]["radiometric"]["ObjectDistance"] = float(self.fff.get("ObjectDistance",(80,))[0])
            self.header["calibration"]["radiometric"]["ReflectedApparentTemperature"] = float(self.fff.get("ReflectedApparentTemperature",(0,))[0])
            self.header["calibration"]["radiometric"]["AtmosphericTemperature"] = float(self.fff.get("AtmosphericTemperature",(0,))[0])
            self.header["calibration"]["radiometric"]["RelativeHumidity"] = float(self.fff.get("RelativeHumidity",(0.5,))[0])
            self.header["calibration"]["radiometric"]["coretemp"] = float(self.fff.get("Coretemp",(0,))[0])
        except:
            pass #no thermal infrared
            logger.info("no thermal infrared calibration")
        

def UTCFromGps(gpsWeek, mSOW, leapSecs=16,gpxstyle=False): 
    """
    mSOW = milliseconds of week 
    gpsWeek is the full number (not modulo 1024) 
    """ 
    secFract = mSOW % 1000 
    epochTuple = (1980, 1, 6, 0, 0, 0) + (-1, -1, 0)  
    t0 = time.mktime(epochTuple) - time.timezone  #mktime is localtime, correct for UTC 
    tdiff = (gpsWeek * 604800) + mSOW/1000.0 - leapSecs 
    t = t0 + tdiff 
    (year, month, day, hh, mm, ss, dayOfWeek, julianDay, daylightsaving) = time.gmtime(t) 
    if gpxstyle==True:
        return "%04d-%02d-%02dT%02d:%02d:%02d"%(year,month,day,hh,mm,ss)
    else:
        return "%04d-%02d-%02d %02d:%02d:%02d"%(year,month,day,hh,mm,ss)


class ImageAra(Image):
    def __init__(self,imgpath=None,bitsPerPixel=np.uint16,onlyheader=False):
        if imgpath is not None:
            self.load(imgpath,onlyheader=onlyheader)
        
    def load(self,imgpath,headersize = 512 ,resolution = (640,512),bitsPerPixel = np.uint16,onlyheader=False,old=True):
        self.header = {"camera":{},"uav":{},"image":{},"file":{},"gps":{},
         "calibration":{"geometric":{},"radiometric":{},"boresight":{}},"exif":{},
                    "thumbnail":{},     }
    
        self.imgpath = imgpath
        self.filename = os.path.basename(str(imgpath))
        
        try:
            with open(imgpath, 'rb') as fileobj:
                self.read_header(fileobj,headersize)
                self.get_meta(old)
                if not onlyheader:
                    self.read_body(fileobj,BITDEPTH[self.header["image"]["bitdepth"]],
                        self.header["image"]["width"],self.header["image"]["height"])
        except FileNotFoundError as e:
            logger.error(e)
        except:
            logger.error("AraHeader read_header() failed", exc_info=True)
    
    
    def read_body(self, fileobj,bitsPerPixel, im_width,im_height):
        count = im_width * im_height
        self.rawbody = np.fromfile(fileobj, dtype=bitsPerPixel,count=count) 
        self.rawbody = np.reshape(self.rawbody,(im_height,im_width))
        #self.normalize()
        #self.image = self.rawbody
   
    
    def normalize(self):
        '''
            just reduction to 8bit
        '''
        self.normalized = self.rawbody - self.rawbody.min()
        za = np.array(self.normalized, dtype=np.float32) 
        za *= 255.0/float(self.normalized.max())
        self.image = np.array(za, dtype=np.uint8) 
        return self.image
    
   
          
    def read_header(self, fileobj, size):
        try:
            rawheader = fileobj.read(size)
            self.fmt = '<HIIIIIIHHIIIIII HHHHHHII IIIIHII32s IHIiiiHHHhhhhHhhh HHII32s iiiHHHhh 100shhhIhh BHHBHHBHHBHHBHHBHHBHHBHHBHHBHH HHHIhIHHHHhhhhhhI03sHBBhhII47s'
            h = struct.Struct(self.fmt).unpack_from(rawheader)
            self.headerarray = list(h)
            self.rawheader = {
                "bitmap":{
                    "mark":h[0],"filelength":h[1],"reserved":h[2],"offset":h[3], 
                    "hsize":h[4],"width":h[5],"height":h[6], "planes":h[7], 
                    "bitperpixel":h[8],"compression":h[9], "datasize":h[10], 
                    "ppm_x":h[11],"ppm_y":h[12],"colors":h[13],"colors2":h[14]},
                "asctec":{
                    "version":h[15],"checksum":h[16],"mode":h[17],
                    "trigger_counter":h[18],"bit_per_pixel":h[19],
                    "byte_per_pixel":h[20],"color_min":h[21],"color_max":h[22]},
                "camera":{
                    "sernum":h[23], "sernum_sensor":h[24], "version":h[25],
                    "fw_version":h[26], "sensortemperature":h[27],
                    "crc_error_cnt":h[28],"dcmi_error_cnt":h[29],"partnum":h[30]},
                "falcon":{
                    "time_ms":h[31], "gps_week":h[32],"gps_time_ms":h[33], 
                    "gps_long":h[34], "gps_lat":h[35], "baro_height":h[36],
                    "gps_hor_accuracy":h[37], "gps_vert_accuracy":h[38],
                    "gps_speed_accuracy":h[39], "gps_speed_x":h[40],
                    "gps_speed_y":h[41], "angle_pitch":h[42],"angle_roll":h[43],
                    "angle_yaw":h[44],"cam_angle_pitch":h[45], 
                    "cam_angle_roll":h[46], "cam_angle_yaw":h[47]},
                "firmware_version":{
                    "major":h[48], "minor":h[49], "build_count":h[50], 
                    "timestamp":h[51], "svn_revision":h[52] },
                "startup_gps":{
                    "long":h[53], "lat":h[54], "height":h[55], 
                    "hor_accuracy":h[56], "vert_accuracy":h[57], 
                    "speed_accuracy":h[58],"speed_x":h[59], "speed_y":h[60]},
                "dlr":{"platzhalter":h[61],"cam_pitch_offset":h[62],"cam_roll_offset":h[63],
                    "cam_yaw_offset":h[64],"boresight_calib_timestamp":h[65],"gps_acc_x":h[66],"gps_acc_y":h[67],
                    "pois":[{"id":h[i],"x":h[i+1],"y":h[i+2]} for i in range(68,95,3) if h[i] != 0],
                    
                    "changed_flags":h[98],"error_flags":h[99],"radiometric_B":h[100],"radiometric_R":h[101],
                    "radiometric_F":h[102],"radiometric_calib_timestamp":h[103],"geometric_fx":h[104],
                    "geometric_fy":h[105],"geometric_cx":h[106],"geometric_cy":h[107],"geometric_skew":h[108],
                    "geometric_k1":h[109],"geometric_k2":h[110],"geometric_k3":h[111],"geometric_p1":h[112],
                    "geometric_p2":h[113],"geometric_calib_timestamp":h[114],"erkennung":h[115],"flags":h[116],"version_major":h[117],"version_minor":h[118],"geometric_pixelshift_x":h[119],"geometric_pixelshift_y":h[120],"raw_size":h[121],"img_size":h[122],"platzhalter2":h[123]}
                }
            
        except:
            logger.error("read header failed", exc_info=True)
            
    def get_meta(self,old=True):
        self.exif = self.rawheader
        self.xmp = ""
        
        self.header["file"]["name"] = self.filename        
        self.header["image"]["width"] = self.rawheader["bitmap"]["width"]               
        self.header["image"]["height"] = self.rawheader["bitmap"]["height"]       
        self.header["image"]["bitdepth"] = self.rawheader["bitmap"]["bitperpixel"]      
        
        if old:
            self.header["camera"]["roll"] = self.rawheader["falcon"]["cam_angle_roll"]/10.0**2          
            self.header["camera"]["yaw"] = self.rawheader["falcon"]["angle_yaw"]/10.0**2   
                                        #self.rawheader["falcon"]["cam_angle_yaw"]/10.0**2
            self.header["camera"]["pitch"] = self.rawheader["falcon"]["cam_angle_pitch"]/10.0**2    
        else:
            self.header["camera"]["roll"] = self.rawheader["falcon"]["cam_angle_roll"]/10.0**2          
            self.header["camera"]["yaw"] = self.rawheader["falcon"]["angle_yaw"]/10.0**2   
                                        #self.rawheader["falcon"]["cam_angle_yaw"]/10.0**2
            self.header["camera"]["pitch"] = self.rawheader["falcon"]["cam_angle_pitch"]/10.0**2    
        self.header["camera"]["euler_order"] = "ZXY"
                
        self.header["camera"]["model"] = str(self.rawheader["camera"]["partnum"].strip(b"\x00"))
        self.header["camera"]["make"] = "Intel"
        
        self.header["uav"]["roll"] = self.rawheader["falcon"]["angle_roll"]/10.0**2             
        self.header["uav"]["yaw"] = self.rawheader["falcon"]["angle_yaw"]/10.0**2               
        self.header["uav"]["pitch"] = self.rawheader["falcon"]["angle_pitch"]/10.0**2              
        self.header["uav"]["euler_order"] = "ZYX"
        
        self.header["gps"]["latitude"] = self.rawheader["falcon"]["gps_lat"]/10.0**7            
        self.header["gps"]["longitude"] = self.rawheader["falcon"]["gps_long"]/10.0**7      
        self.header["gps"]["rel_altitude"] = self.rawheader["falcon"]["baro_height"]/10.0**3        
        #self.header["gps"]["abs_altitude"] = -9999
        
        self.header["gps"]["date time"] = UTCFromGps(self.rawheader["falcon"]["gps_week"],
                                                        self.rawheader["falcon"]["gps_time_ms"])
        
        UTM_Y,UTM_X,ZoneNumber,ZoneLetter = utm.from_latlon(self.header["gps"]["latitude"],self.header["gps"]["longitude"])
        
        self.header["gps"]["UTM_X"] = UTM_X
        self.header["gps"]["UTM_Y"] = UTM_Y
        self.header["gps"]["UTM_ZoneNumber"] = ZoneNumber
        self.header["gps"]["UTM_ZoneLetter"] = ZoneLetter 
        
        
        self.header["gps"]["hor_accuracy"] = self.rawheader["falcon"]["gps_hor_accuracy"]/10.0**3       
        self.header["gps"]["hor_accuracy"] = self.rawheader["falcon"]["gps_vert_accuracy"]/10.0**3  
        self.header["gps"]["speed_accuracy"] = self.rawheader["falcon"]["gps_speed_accuracy"]/10.0**3   
        self.header["gps"]["speed_x"] = self.rawheader["falcon"]["gps_speed_x"]/10.0**3             
        self.header["gps"]["speed_y"] = self.rawheader["falcon"]["gps_speed_y"]/10.0**3             
        
        
        self.header["file"]["size"] = self.rawheader["bitmap"]["filelength"]            
        self.header["image"]["compression"] = self.rawheader["bitmap"]["compression"]       
        
        self.header["file"]["asctec_version"] = self.rawheader["asctec"]["version"]         
        self.header["file"]["asctec_checksum"] = self.rawheader["asctec"]["checksum"]       
        self.header["file"]["asctec_mode"] = self.rawheader["asctec"]["mode"]               
        self.header["file"]["asctec_trigger_counter"] = self.rawheader["asctec"]["trigger_counter"]      
        
        self.header["image"]["colormin"] = self.rawheader["asctec"]["color_min"]            
        self.header["image"]["colormax"]  = self.rawheader["asctec"]["color_max"]            
        
        self.header["camera"]["serial"] = self.rawheader["camera"]["sernum"]               
        self.header["camera"]["serial_sensor"] = self.rawheader["camera"]["sernum_sensor"]        
        self.header["camera"]["version"] = self.rawheader["camera"]["version"]              
        self.header["camera"]["fw_version"] = self.rawheader["camera"]["fw_version"]        
        self.header["camera"]["pixelshift_x"] = 17e-6            
        self.header["camera"]["pixelshift_y"] = 17e-6
        self.header["gps"]["dateTtime"] = UTCFromGps(self.rawheader["falcon"]["gps_week"],
                                                        self.rawheader["falcon"]["gps_time_ms"])
        self.header["file"]["DateTimeOriginal"] = self.header["gps"]["dateTtime"]  # a must have parameter
        
        self.header["file"]["asctec_fw_version"] = {"major":self.rawheader["firmware_version"]["major"],
                                                    "minor":self.rawheader["firmware_version"]["minor"],
                                                    "built_count": self.rawheader["firmware_version"]["build_count"],
                                                    "timestamp": self.rawheader["firmware_version"]["timestamp"],
                                                    "svn_rev": self.rawheader["firmware_version"]["svn_revision"]} 
        
        self.header["gps"]["start_lon"] = self.rawheader["startup_gps"]["long"]/10.0**7             
        self.header["gps"]["start_lat"] = self.rawheader["startup_gps"]["lat"]/10.0**7              
        self.header["gps"]["start_altitude"] = self.rawheader["startup_gps"]["height"]/10.0**3      
        self.header["gps"]["start_hor_accuracy"] = self.rawheader["startup_gps"]["hor_accuracy"]/10.0**3    
        self.header["gps"]["start_ver_accuracy"] = self.rawheader["startup_gps"]["vert_accuracy"]/10.0**3   
        self.header["gps"]["start_speed_accuracy"] = self.rawheader["startup_gps"]["speed_accuracy"]/10.0**3    
        self.header["gps"]["start_speed_x"] = self.rawheader["startup_gps"]["speed_x"]/10.0**3      
        self.header["gps"]["start_speed_y"] = self.rawheader["startup_gps"]["speed_y"]/10.0**3  
        #if self.header["file"]["asctec_fw_version"]["major"]== 1 and self.header["file"]["asctec_fw_version"]["minor"]>=9:
        #    self.header["uav"]["yaw"] = self.rawheader["intel"]["yaw"] /10.0**2 
        #    self.header["camera"]["yaw"] = self.rawheader["intel"]["yaw"] /10.0**2 
        self.header["gps"]["acc_x"] = self.rawheader["dlr"]["gps_acc_x"]/10.0**3           
        self.header["gps"]["acc_y"] = self.rawheader["dlr"]["gps_acc_y"]/10.0**3
        
        
        self.header["calibration"]["changed_flags"] = self.rawheader["dlr"]["changed_flags"]     
        self.header["calibration"]["error_flags"] = self.rawheader["dlr"]["error_flags"]         
        self.header["calibration"]["flags"] = self.rawheader["dlr"]["flags"]  
        self.header["calibration"]["boresight"]["cam_pitch"] = self.rawheader["dlr"]["cam_pitch_offset"]/10.0**3    
        self.header["calibration"]["boresight"]["cam_roll"] = self.rawheader["dlr"]["cam_roll_offset"]/10.0**3    
        self.header["calibration"]["boresight"]["cam_yaw"] = self.rawheader["dlr"]["cam_yaw_offset"]/10.0**3    
        self.header["calibration"]["boresight"]["cam_euler_order"] = "ZYX" 
        self.header["calibration"]["boresight"]["timestamp"] = self.rawheader["dlr"]["boresight_calib_timestamp"] 
        self.header["calibration"]["radiometric"]["B"] = self.rawheader["dlr"]["radiometric_B"]/10.0**2     
        self.header["calibration"]["radiometric"]["R"] = self.rawheader["dlr"]["radiometric_R"]/10.0**3     
        self.header["calibration"]["radiometric"]["F"] = self.rawheader["dlr"]["radiometric_F"]/10.0**3     
        self.header["calibration"]["radiometric"]["coretemp"] = self.rawheader["camera"]["sensortemperature"]/10.0
        
        self.header["calibration"]["radiometric"]["timestamp"] = self.rawheader["dlr"]["radiometric_calib_timestamp"] 
        
        self.header["calibration"]["geometric"]["fx"] = self.rawheader["dlr"]["geometric_fx"]/10.0**1       
        self.header["calibration"]["geometric"]["fy"] = self.rawheader["dlr"]["geometric_fy"]/10.0**1       
        self.header["calibration"]["geometric"]["cx"] = self.rawheader["dlr"]["geometric_cx"]/10.0**1       
        self.header["calibration"]["geometric"]["cy"] = self.rawheader["dlr"]["geometric_cy"]/10.0**1       
        self.header["calibration"]["geometric"]["skew"] = self.rawheader["dlr"]["geometric_skew"]/10.0**3     
        self.header["calibration"]["geometric"]["k1"] = self.rawheader["dlr"]["geometric_k1"]/10.0**3
        self.header["calibration"]["geometric"]["k2"] = self.rawheader["dlr"]["geometric_k2"]/10.0**3
        self.header["calibration"]["geometric"]["k3"] = self.rawheader["dlr"]["geometric_k3"]/10.0**3
        self.header["calibration"]["geometric"]["p1"] = self.rawheader["dlr"]["geometric_p1"]/10.0**3
        self.header["calibration"]["geometric"]["p2"] = self.rawheader["dlr"]["geometric_p2"]/10.0**3
        self.header["calibration"]["geometric"]["pixelshift_x"] = self.rawheader["dlr"]["geometric_pixelshift_x"]/10.0**8
        self.header["calibration"]["geometric"]["pixelshift_x"] = self.rawheader["dlr"]["geometric_pixelshift_y"]/10.0**8
        self.header["calibration"]["geometric"]["timestamp"] = self.rawheader["dlr"]["geometric_calib_timestamp"]
        
        self.header["file"]["dlr_protokoll"] = {"erkennung":self.rawheader["dlr"]["erkennung"],
                                              "version_major":self.rawheader["dlr"]["version_major"],
                                              "version_minor":self.rawheader["dlr"]["version_minor"]}
    

class ImageTiff(Image):

    def __init__(self,imgpath=None,bitsPerPixel=np.uint16,onlyheader=False):
        if imgpath is not None:
            self.load(imgpath,onlyheader=onlyheader)
        
    def load(self,imgpath,onlyheader=False):
        self.header = {"camera":{},"uav":{},"image":{},"file":{},"gps":{},
         "calibration":{"geometric":{},"radiometric":{},"boresight":{}},"exif":{},
                    "thumbnail":{},     }
        self.exif = {}
        self.imgpath = imgpath
        self.filename = os.path.basename(str(imgpath))
        try:
            with tf.TiffFile(os.path.normpath(str(imgpath))) as tif:
                if not onlyheader:
                    self.rawbody = tif.asarray()
                    #self.image = self.rawbody
                for page in tif.pages:
                    for tag in page.tags.values():
                        self.exif[tag.name] = tag.value
            self.xmp = BeautifulSoup(self.exif["XMP"],"lxml")
           # print ("EXIF",self.exif)      
           # print ("XMP",self.xmp)      
           # print("IMAGE")
            if str(self.exif.get("Make","")) == "DJI":
           #     print("DJI")
                self.fill_header_dji()
            elif str(self.exif.get("Make","")) == "FLIR":
            #    print("FLIR")
                self.fill_header_flir()
                
        except FileNotFoundError as e:
            logger.error(e,exc_info=True)
            
        except:
            logger.error("ImageTiff load image failed", exc_info=True)
     #   print (self.imgpath, self.image.shape)
        
    def dms2dd(self,dms,ref):
        degrees = float(dms[0])/dms[1]
        minutes = float(dms[2])/dms[3]
        seconds = float(dms[4])/dms[5]
        dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60);
        if ref == 'W' or ref == 'S':
            dd *= -1
        return dd;

    def fill_header_flir(self):
        self.header["file"]["name"] = self.filename
        self.header["image"]["width"] = self.exif["ImageWidth"]
        self.header["image"]["height"] = self.exif["ImageLength"]
        self.header["image"]["bitdepth"] = self.exif["BitsPerSample"]
        
        self.header["camera"]["roll"] = self.extract_xmp("camera:roll")
        self.header["camera"]["yaw"] = self.extract_xmp("camera:yaw")
        self.header["camera"]["pitch"] = self.extract_xmp("camera:pitch")
        self.header["camera"]["euler_order"] = "ZYX"
        self.header["camera"]["model"] = self.exif["Model"]
        self.header["camera"]["make"] = self.exif["Make"]
        self.header["uav"]["roll"] = self.extract_xmp("flir:mavroll")
        self.header["uav"]["yaw"] = self.extract_xmp("flir:mavyaw")
        self.header["uav"]["pitch"] = self.extract_xmp("flir:mavpitch")
        self.header["uav"]["euler_order"] = "ZYX"
        self.header["gps"]["latitude"]  = self.convert_latlon(self.exif["GPSTag"]["GPSLatitude"],self.exif["GPSTag"]["GPSLatitudeRef"])
        self.header["gps"]["longitude"] = self.convert_latlon(self.exif["GPSTag"]["GPSLongitude"],self.exif["GPSTag"]["GPSLongitudeRef"])
        self.header["gps"]["rel_altitude"] = self.extract_xmp("flir:mavrelativealtitude")
        self.header["gps"]["abs_altitude"] = float(self.exif["GPSTag"]["GPSAltitude"][0])/self.exif["GPSTag"]["GPSAltitude"][1]
        
        self.header["image"]["compression"] = self.exif["Compression"]
        self.header["gps"]["datetime"] = self.exif["ExifTag"]["DateTimeOriginal"]
        self.header["camera"]["serial"] = self.exif["CameraSerialNumber"]
        self.header["file"]["fw_version"] = self.exif["Software"]
        
 
    def fill_header_dji(self):
        a = self.xmp.find("rdf:description")
        if a == None: return
        self.header["file"]["name"] = self.filename
        self.header["image"]["width"] = self.extract_exif("ImageWidth")#self.width #extract_exif("EXIF ExifImageWidth")
        self.header["image"]["height"] = self.extract_exif("ImageLength")#self.height
        self.header["image"]["bitdepth"] = self.extract_exif("BitsPerSample")     
        
        self.header["camera"]["roll"] = float(a.get("drone-dji:gimbalrolldegree",0))
        self.header["camera"]["yaw"] = float(a.get("drone-dji:gimbalyawdegree",0))
        self.header["camera"]["pitch"] = float(a.get("drone-dji:gimbalpitchdegree",0))
        self.header["camera"]["euler_order"] = "ZXY"
        self.header["camera"]["model"] = a.get("tiff:model",0)
        self.header["camera"]["make"] = a.get("tiff:make",0)
        self.header["uav"]["roll"] = float(a.get("drone-dji:flightrolldegree",0))
        self.header["uav"]["yaw"] = float(a.get("drone-dji:flightyawdegree",0))
        self.header["uav"]["pitch"] = float(a.get("drone-dji:flightpitchdegree",0))
        self.header["uav"]["euler_order"] = "ZYX"
        self.header["gps"]["latitude"] = self.convert_latlon(self.exif["GPSTag"]["GPSLatitude"],self.exif["GPSTag"]["GPSLatitudeRef"])
        self.header["gps"]["longitude"] = self.convert_latlon(self.exif["GPSTag"]["GPSLongitude"],self.exif["GPSTag"]["GPSLongitudeRef"])
        self.header["gps"]["rel_altitude"]=float(a.get("drone-dji:relativealtitude",0))
        self.header["gps"]["abs_altitude"]=float(a.get("drone-dji:absolutealtitude",0))
        self.header["gps"]["gpsmapdatum"] = self.exif["GPSTag"]["GPSMapDatum"]
            
        UTM_Y,UTM_X,ZoneNumber,ZoneLetter = utm.from_latlon(self.header["gps"]["latitude"],self.header["gps"]["longitude"])
        self.header["gps"]["UTM_X"] = UTM_X
        self.header["gps"]["UTM_Y"] = UTM_Y
        self.header["gps"]["UTM_ZoneNumber"] = ZoneNumber
        self.header["gps"]["UTM_ZoneLetter"] = ZoneLetter 
        
        self.header["file"]["about"]=a.get("rdf:about",0)
        self.header["file"]["modifydate"]=a.get("xmp:modifydate",0)
        self.header["file"]["createdate"]=a.get("xmp:createdate",0)
        self.header["file"]["DateTimeOriginal"] = a.get("xmp:createdate",0)
        self.header["file"]["format"]=a.get("dc:format",0)
        self.header["file"]["version"]=a.get("crs:version",0)
         
        self.header["calibration"]["geometric"]["fx"]=float(a.get("drone-dji:calibratedfocallength",0))
        self.header["calibration"]["geometric"]["cx"]=float(a.get("drone-dji:calibratedopticalcenterx",0))
        self.header["calibration"]["geometric"]["cy"]=float(a.get("drone-dji:calibratedopticalcentery",0))
        
        self.header["image"]["make"] = self.extract_exif("Make")
        self.header["image"]["xresolution"] = self.extract_exif("Image XResolution")
        self.header["image"]["yresolution"] = self.extract_exif("Image YResolution")
        self.header["image"]["resolutionunit"] = self.extract_exif("Image ResolutionUnit")
        self.header["image"]["software"] = self.extract_exif("Image Software")
        self.header["image"]["datetime"] = self.extract_exif("Image DateTime")
        self.header["image"]["artist"] = self.extract_exif("Image Artist")
        self.header["image"]["copyright"] = self.extract_exif("Image Copyright")
        self.header["image"]["exifoffset"] = self.extract_exif("Image ExifOffset")
        self.header["image"]["gpsinfo"] = self.extract_exif("Image GPSInfo")
        
        self.header["thumbnail"]["compression"] = self.extract_exif("Thumbnail Compression")
        self.header["thumbnail"]["xresolution"] = self.extract_exif("Thumbnail XResolution")
        self.header["thumbnail"]["yresolution"] = self.extract_exif("Thumbnail YResolution")
        self.header["thumbnail"]["ResolutionUnit"] = self.extract_exif("Thumbnail ResolutionUnit")
        self.header["thumbnail"]["JPEGInterchangeFormat"] = self.extract_exif("Thumbnail JPEGInterchangeFormat")
        self.header["thumbnail"]["JPEGInterchangeFormatLength"] = self.extract_exif("Thumbnail JPEGInterchangeFormatLength")
        
        self.header["exif"]["FNumber"] = self.extract_exif("Exif FNumber")
        self.header["exif"]["DateTimeOriginal"] = self.extract_exif("EXIF DateTimeOriginal")
        self.header["exif"]["ApertureValue"] = self.extract_exif("EXIF ApertureValue")
        self.header["exif"]["FocalLength"] = self.extract_exif("EXIF FocalLength")
        self.header["exif"]["SubSecTimeOriginal"] = self.extract_exif("EXIF SubSecTimeOriginal")
        self.header["exif"]["FocalPlaneResolutionUnit"] = self.extract_exif("EXIF FocalPlaneResolutionUnit")
    
        
            
if  __name__=="__main__":
    #doctest.testmod()
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    import matplotlib.pyplot as plt
    
   # a = Image.factory("test/dji_example.jpg")
   # pp.pprint(a.header)      
   # plt.imshow(a.image)
   # plt.show()
    
 #   a = Image.factory("test/20180523_220000.jpg")
 #   pp.pprint(a.header)      
 #   plt.imshow(a.image,"gray")
 #   plt.show()
    
    a = Image.factory("test/Duo_Pro_R.jpg")
    #a = Image.factory("test/20190327_104730_R.jpg")
   # pp.pprint(a.header)      
    
   # plt.imshow(a.image,"gray")
   # plt.show()
    
   # a = Image.factory("test/20180530_152906.tiff")
   # pp.pprint(a.header)      
   # plt.imshow(a.image,"gray")
   # plt.show()
    
   # a = Image.factory("test/BRH08151525_0037.ara")
   # pp.pprint(a.header)      
   # plt.imshow(a.image,"gray")
   # plt.show()
    