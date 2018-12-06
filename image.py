import numpy as np
import logging
import doctest
import os
import re
import utm
try:
    import exifread
    from PIL import Image as pilimage
    import struct
    import time
    import tifffile as tf
    import datetime
    import dateutil
except ImportError:
    logging.error("loading a module failed! maybe you can not read all types of images",exc_info=True)

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


    
class Image(object):
    header = {"camera":{},"uav":{},"image":{},"file":{},"gps":{},
         "calibration":{"geometric":{},"radiometric":{},"boresight":{}}
        }
    exif = None
    xmp = None
    
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def factory(imgpath,onlyheader=False):
        root, ext = os.path.splitext(imgpath)
        if ext.lower() in [".raw",".ara",".ar2"]: 
            return ImageAra(imgpath,onlyheader)
        elif ext.lower() in [".tif",".tiff"]: 
            return ImageTiff(imgpath,onlyheader)
        elif ext.lower() in [".jpg",".jpeg"]:     
            return ImageJpg(imgpath,onlyheader)
        
    factory = staticmethod(factory)
     
    
    def evaldiv(self,string):
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

    def extract_xmp(self,string):
        try:
            text = self.evaldiv(self.xmp.find(string).text)
        except ValueError:
            text = self.xmp.find(string).text.strip()
        except AttributeError:
            return None
        return text

    def convert_latlon(self,exif_deg,exif_ref):
        deg = str(self.exif[exif_deg])
        ref = str(self.exif[exif_ref])
        
        p = re.compile(r'[\[, \]]+')
        deglist = p.split(deg)[1:-1]
        return dms2dd(deglist[0],deglist[1],self.evaldiv(deglist[2]),ref)
        
    def extract_exif(self,string):
        try:
            text = self.evaldiv(self.exif.get(string))
        except ValueError:
            text = str(self.exif.get(string)).strip()
        except AttributeError:
            return None
        return text

    def load(self,imgpath,onlyheader=False):
        pass
        
    #self.logger.error("Open file failed", exc_info=True)


class ImageJpg(Image):
    def __init__(self,imgpath=None,bitsPerPixel=np.uint16,onlyheader=False):
        if imgpath is not None:
            self.load(imgpath,onlyheader=onlyheader)
        
    def load(self,imgpath,onlyheader=False):
        self.header = {"camera":{},"uav":{},"image":{},"file":{},"gps":{},
            "calibration":{"geometric":{},"radiometric":{},"boresight":{}}
            }
        self.imgpath = imgpath
        self.filename = os.path.basename(str(imgpath))
        d, self.exif, self.xmp = self.get_meta(imgpath)
        flirchunk = self.extract_flir_ifd(d)
        if flirchunk is not None:
            width = int(str(self.exif.get("Raw Thermal Image Width",640)))
            height = int(str(self.exif.get("Raw Thermal Image Height",512)))
            if onlyheader:
                self.fff = self.flir_header(flirchunk,width,height)
            else:
                self.rawbody, self.fff = self.flir_data(flirchunk,width,height)
                self.image = self.rawbody
            self.fill_header_flir()
        else:
            if not onlyheader:
                self.image = np.array(pilimage.open(imgpath))
                self.rawbody = self.image
            self.fill_header_dji()
            
    def get_meta(self,imgpath):
        exif = {}
        xmp = ""
        d = []
        try:
            f = open(imgpath,"rb")
            exif = exifread.process_file(f,details=False)
            d = f.read()
            
            xmp_start = d.find(b"<rdf:RDF")
            xmp_end = d.find(b"</rdf:RDF")
            xmp_str = d[xmp_start:xmp_end+10]
            xmp = BeautifulSoup(xmp_str,"lxml")
        except FileNotFoundError as e:
            logging.error(e)
        except:
            logging.error(e)
        return d, exif, xmp

    def extract_flir_ifd(self,bytearr):
        def find_nth(haystack, needle, n):
            start = haystack.find(needle)
            while start >= 0 and n > 1:
                start = haystack.find(needle, start+len(needle))
                n -= 1
            return start
        i,pos =0,0
        rawdata = None
        while pos>-1:
            i+=1
            pos = find_nth(bytearr, b"\xff\xe1", i)
            length = 256 * bytearr[pos+2] + bytearr[pos+3]
            if pos>-1:
                if bytearr[pos+4:pos+8]==b"FLIR":
                    if bytearr[pos+12:pos+15]==b"FFF":
                        rawdata = bytearr[pos+556:pos+length+2]
                    else:    
                        rawdata += bytearr[pos+12:pos+length+2]
                else:
                    return None
        return rawdata
        
    def flir_data(self,rawdata,width,height):    
        fff = {}
        img = np.frombuffer(rawdata, dtype="<u2",count=width*height) 
        img = np.reshape(img,(height,width))
        fffmeta = rawdata[width*height*2:]
        for i in FFF:
            val = struct.Struct("<"+i[2]).unpack_from(fffmeta,i[0])
            if "s" in i[2]:
                val = val[0].strip(b"\x00")
            name = i[1]
            fff[name]=val
        return img, fff    
    
    def flir_header(self,rawdata,width,height):    
        fff = {}
        fffmeta = rawdata[width*height*2:]
        for i in FFF:
            val = struct.Struct("<"+i[2]).unpack_from(fffmeta,i[0])
            if "s" in i[2]:
                val = val[0].strip(b"\x00")
            name = i[1]
            fff[name]=val
        return fff    
        
    def fill_header_flir(self):
        self.header["camera"]["roll"] = self.extract_xmp("camera:roll") 
        self.header["camera"]["yaw"] = self.extract_xmp("camera:yaw")
        self.header["camera"]["pitch"] = self.extract_xmp("camera:pitch") 
        self.header["camera"]["centralwavelength"] = self.extract_xmp("camera:centralwavelength") 
        self.header["camera"]["wavelengthfwhm"] = self.extract_xmp("camera:wavelengthfwhm") 
        self.header["camera"]["detectorbitdepth"] = self.extract_xmp("camera:detectorbitdepth")
        self.header["camera"]["tlineargain"] = self.extract_xmp("camera:tlineargain") 
        self.header["camera"]["gyrorate"] = self.extract_xmp("camera:gyrorate")
        self.header["camera"]["isnormalized"] = self.extract_xmp("camera:isnormalized") 
        self.header["camera"]["fnumber"] = self.extract_exif("Image FNumber")
        self.header["camera"]["focallength"] = self.extract_exif("Image FocalLength")
        self.header["camera"]["make"] = self.extract_exif("Image Make")
        self.header["camera"]["model"] = self.extract_exif("Image Model")
        self.header["camera"]["coretemp"] = self.fff.get("Coretemp",(1))[0]
        
        self.header["file"]["mavversion"] = self.extract_xmp("flir:mavversionid")
        self.header["file"]["mavcomponent"] = self.extract_xmp("flir:mavcomponentid")
        self.header["file"]["exifversion"] = self.extract_exif("EXIF ExifVersion")
        self.header["file"]["name"] = self.filename
        
        
        try:
            self.header["camera"]['PartNumber'] = self.fff.get("CameraPartNumber","").decode("utf-8") 
            self.header["camera"]["serial"] = self.fff.get('CameraSerialNumber',"").decode("utf-8") 
            self.header["file"]["DateTimeOriginal"] = isotimestr(*self.fff.get("DateTimeOriginal",0))
        except:
            self.header["camera"]['PartNumber'] = self.fff.get("CameraPartNumber","")
            self.header["camera"]["serial"] = self.fff.get('CameraSerialNumber',"")
            self.header["file"]["DateTimeOriginal"] = self.fff.get("DateTimeOriginal",0)
        #self.header["file"]["modifydate"] = self.fff.get("DateTimeOriginal",0)
        #self.header["file"]["createdate"] = self.fff.get("DateTimeOriginal",0)
    
        self.header["gps"]["rel_altitude"]= self.extract_xmp("flir:mavrelativealtitude")
        self.header["gps"]["hor_accuracy"]= self.extract_xmp("camera:gpsxyaccuracy")
        self.header["gps"]["ver_accuracy"]= self.extract_xmp("camera:gpszaccuracy")
        self.header["gps"]["climbrate"] = self.extract_xmp("flir:mavrateofclimb") 
        self.header["gps"]["climbrateref"] = self.extract_xmp("flir:mavrateofclimbref")
        self.header["gps"]["abs_altitude"] = self.extract_exif("GPS GPSAltitude")
        self.header["gps"]["abs_altituderef"] = self.extract_exif("GPS GPSAltitudeRef")
        self.header["gps"]["latitude"] = self.convert_latlon("GPS GPSLatitude","GPS GPSLatitudeRef")
        self.header["gps"]["longitude"] = self.convert_latlon("GPS GPSLongitude","GPS GPSLongitudeRef")
        self.header["gps"]["speed"] = self.extract_exif("GPS GPSSpeed")
        self.header["gps"]["speedref"] = self.extract_exif("GPS GPSSpeedRef")
        self.header["gps"]["timestamp"] = self.extract_exif("GPS GPSTimeStamp")
        self.header["gps"]["version"] = self.extract_exif("GPS GPSVersionID")
                
        UTM_Y,UTM_X,ZoneNumber,ZoneLetter = utm.from_latlon(self.header["gps"]["latitude"],self.header["gps"]["longitude"])
        self.header["gps"]["UTM_X"] = UTM_X
        self.header["gps"]["UTM_Y"] = UTM_Y
        self.header["gps"]["UTM_ZoneNumber"] = ZoneNumber
        self.header["gps"]["UTM_ZoneLetter"] = ZoneLetter 
        
        self.header["image"]["height"] = self.extract_exif("Raw Thermal Image Height")
        self.header["image"]["width"] = self.extract_exif("Raw Thermal Image Width")
        self.header["image"]["colorspace"] = self.extract_exif("EXIF ColorSpace")
        self.header["image"]["componentsconfiguration"] = self.extract_exif("EXIF ComponentsConfiguration")
        self.header["image"]["bitdepth"] = 16      
                
        self.header["uav"]["roll"] = self.extract_xmp("flir:mavroll")
        self.header["uav"]["yaw"] = self.extract_xmp("flir:mavyaw") 
        self.header["uav"]["pitch"] = self.extract_xmp("flir:mavpitch") 
        self.header["uav"]["rollrate"] = self.extract_xmp("flir:mavrollrate") 
        self.header["uav"]["yawrate"] = self.extract_xmp("flir:mavyawrate") 
        self.header["uav"]["pitchrate"] = self.extract_xmp("flir:mavpitchrate") 
        
        self.header["calibration"]["radiometric"]["R"] = self.fff.get("PlanckR1",(0))[0]
        self.header["calibration"]["radiometric"]["F"] = self.fff.get("PlanckF",(1))[0]
        self.header["calibration"]["radiometric"]["B"] = self.fff.get("PlanckB",(0))[0]
        self.header["calibration"]["radiometric"]["R2"] = self.fff.get("PlanckR2",(0))[0]
        self.header["calibration"]["radiometric"]["timestamp"] = 0
        self.header["calibration"]["radiometric"]["IRWindowTemperature"] = self.fff.get("IRWindowTemperature",(0))[0]
        self.header["calibration"]["radiometric"]["IRWindowTransmission"] = self.fff.get("IRWindowTransmission",(1))[0]
        
        
        
    def fill_header_dji(self):
        a = self.xmp.find("rdf:description")
        self.header["camera"]["roll"] = a.get("drone-dji:gimbalrolldegree",0)
        self.header["camera"]["yaw"] = a.get("drone-dji:gimbalyawdegree",0)
        self.header["camera"]["pitch"] = a.get("drone-dji:gimbalpitchdegree",0)
        self.header["camera"]["model"] = a.get("tiff:model",0)
        self.header["camera"]["make"] = a.get("tiff:make",0)
        self.header["uav"]["roll"] = a.get("drone-dji:flightrolldegree",0)
        self.header["uav"]["yaw"] = a.get("drone-dji:flightyawdegree",0)
        self.header["uav"]["pitch"] = a.get("drone-dji:flightpitchdegree",0)
        self.header["gps"]["abs_altitude"]=a.get("drone-dji:absolutealtitude",0)
        self.header["gps"]["rel_altitude"]=a.get("drone-dji:relativealtitude",0)
        self.header["file"]["about"]=a.get("rdf:about",0)
        self.header["file"]["modifydate"]=a.get("xmp:modifydate",0)
        self.header["file"]["createdate"]=a.get("xmp:createdate",0)
        self.header["file"]["format"]=a.get("dc:format",0)
        self.header["file"]["version"]=a.get("crs:version",0)
        self.header["file"]["name"] = self.filename
        
        self.header["calibration"]["geometric"]["fx"]=a.get("drone-dji:calibratedfocallength",0)
        self.header["calibration"]["geometric"]["cx"]=a.get("drone-dji:calibratedopticalcenterx",0)
        self.header["calibration"]["geometric"]["cy"]=a.get("drone-dji:calibratedopticalcentery",0)
        
        self.header["image"]["bitdepth"] = 8     
        self.header["image"]["height"] = self.extract_exif("EXIF ExifImageLength")
        self.header["image"]["width"] = self.extract_exif("EXIF ExifImageWidth")
        

def UTCFromGps(gpsWeek, SOW, leapSecs=16,gpxstyle=False): 
    """
    SOW = seconds of week 
    gpsWeek is the full number (not modulo 1024) 
    """ 
    secFract = SOW % 1 
    epochTuple = (1980, 1, 6, 0, 0, 0) + (-1, -1, 0)  
    t0 = time.mktime(epochTuple) - time.timezone  #mktime is localtime, correct for UTC 
    tdiff = (gpsWeek * 604800) + SOW - leapSecs 
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
        
    def load(self,imgpath,headersize = 512 ,resolution = (640,512),bitsPerPixel = np.uint16,onlyheader=False):
        self.header = {"camera":{},"uav":{},"image":{},"file":{},"gps":{},
            "calibration":{"geometric":{},"radiometric":{},"boresight":{}}
            }
        self.imgpath = imgpath
        self.filename = os.path.basename(str(imgpath))
        try:
            with open(imgpath, 'rb') as fileobj:
                self.read_header(fileobj,headersize)
                self.get_meta()
                if not onlyheader:
                    self.read_body(fileobj,BITDEPTH[self.header["image"]["bitdepth"]],
                        self.header["image"]["width"],self.header["image"]["height"])
        except FileNotFoundError as e:
            logging.error(e)
        except:
            logging.error("AraHeader read_header() failed", exc_info=True)
            
    def read_body(self, fileobj,bitsPerPixel, im_width,im_height):
        count = im_width * im_height
        self.rawbody = np.fromfile(fileobj, dtype=bitsPerPixel,count=count) 
        self.rawbody = np.reshape(self.rawbody,(im_height,im_width))
        self.image = self.rawbody
   
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
                    "pois":[{"id":h[i],"x":h[i+1],"y":h[i+2]} for i in range(68,95,3) if h[i] is not 0],
                    
                    "changed_flags":h[98],"error_flags":h[99],"radiometric_B":h[100],"radiometric_R":h[101],
                    "radiometric_F":h[102],"radiometric_calib_timestamp":h[103],"geometric_fx":h[104],
                    "geometric_fy":h[105],"geometric_cx":h[106],"geometric_cy":h[107],"geometric_skew":h[108],
                    "geometric_k1":h[109],"geometric_k2":h[110],"geometric_k3":h[111],"geometric_p1":h[112],
                    "geometric_p2":h[113],"geometric_calib_timestamp":h[114],"erkennung":h[115],"flags":h[116],"version_major":h[117],"version_minor":h[118],"geometric_pixelshift_x":h[119],"geometric_pixelshift_y":h[120],"raw_size":h[121],"img_size":h[122],"platzhalter2":h[123]}
                }
            
        except:
            logging.error("read header failed", exc_info=True)
            
    def get_meta(self):
        self.exif = self.rawheader
        self.xmp = ""
        self.header["file"]["size"] = self.rawheader["bitmap"]["filelength"]            
        self.header["image"]["width"] = self.rawheader["bitmap"]["width"]               
        self.header["image"]["height"] = self.rawheader["bitmap"]["height"]       
        self.header["file"]["name"] = self.filename        
        self.header["image"]["bitdepth"] = self.rawheader["bitmap"]["bitperpixel"]      
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
        self.header["camera"]["coretemp"] = self.rawheader["camera"]["sensortemperature"]/10.0
        self.header["camera"]["model"] = self.rawheader["camera"]["partnum"]            
        self.header["camera"]["pixelshift_x"] = 17e-6            
        self.header["camera"]["pixelshift_y"] = 17e-6
        self.header["gps"]["date time"] = UTCFromGps(self.rawheader["falcon"]["gps_week"],
                                                        self.rawheader["falcon"]["gps_time_ms"])
        self.header["gps"]["dateTtime"] = UTCFromGps(self.rawheader["falcon"]["gps_week"],
                                                        self.rawheader["falcon"]["gps_time_ms"])
        
        self.header["gps"]["longitude"] = self.rawheader["falcon"]["gps_long"]/10.0**7      
        self.header["gps"]["latitude"] = self.rawheader["falcon"]["gps_lat"]/10.0**7            
        self.header["gps"]["rel_altitude"] = self.rawheader["falcon"]["baro_height"]/10.0**3        
        self.header["gps"]["hor_accuracy"] = self.rawheader["falcon"]["gps_hor_accuracy"]/10.0**3       
        self.header["gps"]["hor_accuracy"] = self.rawheader["falcon"]["gps_vert_accuracy"]/10.0**3  
        self.header["gps"]["speed_accuracy"] = self.rawheader["falcon"]["gps_speed_accuracy"]/10.0**3   
        self.header["gps"]["speed_x"] = self.rawheader["falcon"]["gps_speed_x"]/10.0**3             
        self.header["gps"]["speed_y"] = self.rawheader["falcon"]["gps_speed_y"]/10.0**3             
        
        self.header["uav"]["pitch"] = self.rawheader["falcon"]["angle_pitch"]/10.0**2              
        self.header["uav"]["roll"] = self.rawheader["falcon"]["angle_roll"]/10.0**2             
        self.header["uav"]["yaw"] = self.rawheader["falcon"]["angle_yaw"]/10.0**2               
        self.header["camera"]["pitch"] = self.rawheader["falcon"]["cam_angle_pitch"]/10.0**2        
        self.header["camera"]["roll"] = self.rawheader["falcon"]["cam_angle_roll"]/10.0**2          
        self.header["camera"]["yaw"] = self.rawheader["falcon"]["cam_angle_yaw"]/10.0**2
        
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
        self.header["gps"]["acc_x"] = self.rawheader["dlr"]["gps_acc_x"]/10.0**3           
        self.header["gps"]["acc_y"] = self.rawheader["dlr"]["gps_acc_y"]/10.0**3
        
        UTM_Y,UTM_X,ZoneNumber,ZoneLetter = utm.from_latlon(self.header["gps"]["latitude"],self.header["gps"]["longitude"])
        
        self.header["gps"]["UTM_X"] = UTM_X
        self.header["gps"]["UTM_Y"] = UTM_Y
        self.header["gps"]["UTM_ZoneNumber"] = ZoneNumber
        self.header["gps"]["UTM_ZoneLetter"] = ZoneLetter 
        
        self.header["calibration"]["changed_flags"] = self.rawheader["dlr"]["changed_flags"]     
        self.header["calibration"]["error_flags"] = self.rawheader["dlr"]["error_flags"]         
        self.header["calibration"]["flags"] = self.rawheader["dlr"]["flags"]  
        self.header["calibration"]["boresight"]["cam_pitch_offset"] = self.rawheader["dlr"]["cam_pitch_offset"]/10.0**3    
        self.header["calibration"]["boresight"]["cam_roll_offset"] = self.rawheader["dlr"]["cam_roll_offset"]/10.0**3    
        self.header["calibration"]["boresight"]["cam_yaw_offset"] = self.rawheader["dlr"]["cam_yaw_offset"]/10.0**3    
        self.header["calibration"]["boresight"]["timestamp"] = self.rawheader["dlr"]["boresight_calib_timestamp"] 
        self.header["calibration"]["radiometric"]["B"] = self.rawheader["dlr"]["radiometric_B"]/10.0**2     
        self.header["calibration"]["radiometric"]["R"] = self.rawheader["dlr"]["radiometric_R"]/10.0**3     
        self.header["calibration"]["radiometric"]["F"] = self.rawheader["dlr"]["radiometric_F"]/10.0**3     
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
            "calibration":{"geometric":{},"radiometric":{},"boresight":{}}
            }
        self.exif = {}
        self.imgpath = imgpath
        self.filename = os.path.basename(str(imgpath))
        try:
            with tf.TiffFile(os.path.normpath(str(imgpath))) as tif:
                if not onlyheader:
                    self.rawbody = tif.asarray()
                    self.image = self.rawbody
                for page in tif.pages:
                    for tag in page.tags.values():
                        self.exif[tag.name] = tag.value
            self.xmp = BeautifulSoup(self.exif["XMP"],"lxml")
            self.get_meta()
        except FileNotFoundError as e:
            logging.error(e)
            
        except:
            logging.error("ImageTiff load image failed", exc_info=True)
        print (self.imgpath, self.image.shape)
        
    def dms2dd(self,dms,ref):
        degrees = float(dms[0])/dms[1]
        minutes = float(dms[2])/dms[3]
        seconds = float(dms[4])/dms[5]
        dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60);
        if ref == 'W' or ref == 'S':
            dd *= -1
        return dd;

    def get_meta(self):
        self.header["file"]["name"] = self.filename
        
        self.header["gps"]["latitude"]  = self.dms2dd(self.exif["GPSTag"]["GPSLatitude"],self.exif["GPSTag"]["GPSLatitudeRef"])
        self.header["gps"]["longitude"] = self.dms2dd(self.exif["GPSTag"]["GPSLongitude"],self.exif["GPSTag"]["GPSLongitudeRef"])
        
        self.header["gps"]["relaltitude"] = self.evaldiv(self.xmp.find("flir:mavrelativealtitude").text)
        self.header["gps"]["absaltitude"] = float(self.exif["GPSTag"]["GPSAltitude"][0])/self.exif["GPSTag"]["GPSAltitude"][1]
        self.header["gps"]["datetime"] = self.exif["ExifTag"]["DateTimeOriginal"]
        
        self.header["uav"]["pitch"] = self.evaldiv(self.xmp.find("flir:mavpitch").text)
        self.header["uav"]["roll"] = self.evaldiv(self.xmp.find("flir:mavroll").text)
        self.header["uav"]["yaw"] = self.evaldiv(self.xmp.find("flir:mavyaw").text)
        
        self.header["camera"]["serial"] = self.exif["CameraSerialNumber"]
        self.header["camera"]["model"] = self.exif["Model"]
        self.header["camera"]["make"] = self.exif["Make"]
        self.header["file"]["fw_version"] = self.exif["Software"]
        
        self.header["camera"]["pitch"] = self.evaldiv(self.xmp.find("camera:pitch").text)
        self.header["camera"]["roll"] = self.evaldiv(self.xmp.find("camera:roll").text)
        self.header["camera"]["yaw"] = self.evaldiv(self.xmp.find("camera:yaw").text)
        
        self.header["image"]["width"] = self.exif["ImageWidth"]
        self.header["image"]["height"] = self.exif["ImageLength"]
        self.header["image"]["bitdepth"] = self.exif["BitsPerSample"]
        self.header["image"]["compression"] = self.exif["Compression"]
            
   
        
            
if  __name__=="__main__":
    #doctest.testmod()
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    import matplotlib.pyplot as plt
    
    a = Image.factory("test/dji_example.jpg")
    pp.pprint(a.header)      
    plt.imshow(a.image)
    plt.show()
    
    a = Image.factory("test/20180523_220000.jpg")
    pp.pprint(a.header)      
    plt.imshow(a.image,"gray")
    plt.show()
    
    a = Image.factory("test/20180919_151905_R.jpg")
    pp.pprint(a.header)      
    plt.imshow(a.image,"gray")
    plt.show()
    
    a = Image.factory("test/20180530_152906.tiff")
    pp.pprint(a.header)      
    plt.imshow(a.image,"gray")
    plt.show()
    
    a = Image.factory("test/BRH08151525_0037.ara")
    pp.pprint(a.header)      
    plt.imshow(a.image,"gray")
    plt.show()
    