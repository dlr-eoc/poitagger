import os
import tifffile as tf
import utm
import flirsd
if os.name == 'nt':
    import win32api
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
import image


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
            if os.path.splitext(i.lower())[1] in image.SUPPORTED_EXTENSIONS:
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

    
def getSDCardPath(namestart="IR_"):
    if os.name == 'nt':
        for element in win32api.GetLogicalDriveStrings().split("\x00")[:-1]:
            try:
                driveinfo = win32api.GetVolumeInformation(element)
                if driveinfo[0][:len(namestart)]==namestart:
                    return element
            except:
                print("Drive %s is not readable" % element)
        return False
    else:
        raise Exception("Automatic detection of SD-Card  on Linux is not yet implemented!")
        return False
        
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

def convert_raw(path, YEAR = '2014', UAV_OWNER = 'DLR',UAV_TYPE = 'Falcon8',CAMERA = 'T'):
    failed = False
    print(path)
    if not path: failed = True
    for root, dirs, files in os.walk(path):
        for name in files:
            (base,ext) = os.path.splitext(name)
            if not((ext.lower() == ".ara") or (ext.lower()== ".raw")): continue
            #print "name: ", name
            inrawfile = os.path.join(root, name)
            try:
                raw = flirsd.ConvertRaw(inrawfile)
                image = raw.normalize()
                meta = mt.Meta()
                meta.from_flirsd(raw.header())
                image.homogenize()
                meta.update("CAMERA", "homogenized", "True")
                meta.update("CAMERA", "owner", raw.calib["owner"])
                meta.update("CAMERA", "type", raw.calib["type"])
                meta.update("UAV","owner",UAV_OWNER)
                meta.update("UAV","type",UAV_TYPE)
                md = meta.to_dict()
                (outrawfile,outfile,outtxt) = set_filenames(inrawfile,md,YEAR,CAMERA)
                base,ofile = os.path.split(outfile)
                print(name, "->", ofile)   
               # print "raw,out,jpg",outrawfile,outfile,outtxt   
                raw.move_to(outrawfile)
                image.save(outfile)
                meta.save(outtxt)
                #print "failed",failed
                failed |= False
            except:
                print(traceback.format_exc())
                print("convert raw failed")
                failed |= True
    return  failed
    
def rename_folder(path):
    error = False
    if not path: error = True
    valid = False
    if re.match(r".*Flug\d{3}_\d{4}-\d\d-\d\d_\d\d-\d\d",path): return (path,error)
    for last in sorted(os.listdir(path),reverse=True):
        if last[-4:]==".txt":
            meta = mt.Meta()
            meta.load(os.path.join(path,last))
            md = meta.to_dict()
            if md["gps-date"]:
                valid = True
                try:
                    (base,lastdir) = os.path.split(path)
                    newtime = "%s-%s" %(md["gps-utc-time"][:2],md["gps-utc-time"][3:5])
                    newend = "_%s_%s" %(md["gps-date"],newtime)
                    os.rename(base,base+newend)
                    newname = base+newend
                    break
                except:
                    print(traceback.format_exc())
                    error = True
    if not valid:
        error = True
    return (newname,error)
    
class LoadTiff(object):
    Tags = {}
    def __init__(self,infile,bitsPerPixel=np.uint16):
        self.infile = infile
        self.read_raw(infile)
        self.filename = os.path.basename(str(infile))
        self.header = self.fill_header()
        
    def read_raw(self, filepath):
        with tf.TiffFile(os.path.normpath(str(filepath))) as tif:
            self.rawbody = tif.asarray()
            for page in tif.pages:
                for tag in page.tags.values():
                    self.Tags[tag.name] = tag.value
                #self.rawbody = page.asarray()
        # with tf.TiffFile('20180119_114943.tiff') as tif:
            # images = tif.asarray()
            # for page in tif.pages:
                # for tag in page.tags.values():
                    # t = tag.name, tag.value
                    # print (t)
            self.image = self.rawbody
        #print tf.version
    def fill_header(self):    
        header = flirsd.Header()
        header.filename = self.filename
        
        lat = self.Tags["GPSIFD"]["GPSLatitude"]
        lon = self.Tags["GPSIFD"]["GPSLongitude"]
        #print (lat[0], lon[0],self.Tags["GPSIFD"]["GPSLatitudeRef"])
        header.lat = dms2dd(float(lat[0])/lat[1],float(lat[2])/lat[3],float(lat[4])/lat[5],self.Tags["GPSIFD"]["GPSLatitudeRef"])
        header.lon = dms2dd(float(lon[0])/lon[1],float(lon[2])/lon[3],float(lon[4])/lon[5],self.Tags["GPSIFD"]["GPSLongitudeRef"])
        header.start_lat = 0
        header.start_lon = 0
        #header.start_lat = self.rawheader["startup_gps"]["lat"]/10.0**7
        #header.start_lon = self.rawheader["startup_gps"]["long"]/10.0**7
        try:
            header.UTM_Y,header.UTM_X,header.ZoneNumber,header.ZoneLetter = utm.from_latlon(header.lat,header.lon)
            header.start_UTM_Y,header.start_UTM_X,header.start_ZoneNumber,header.start_ZoneLetter = utm.from_latlon(header.start_lat,header.start_lon)
        except:
            base,file = os.path.split(str(self.infile))
            print("latlon wrong at", file, "lat:", header.lat,"lon:",header.lon)  
        
        soup = BeautifulSoup(self.Tags["XMP"],"lxml")
        
        header.baro = evaldiv(soup.find("flir:mavrelativealtitude").text)
        #header.baro = self.rawheader["falcon"]["baro_height"]/10.0**3
        header.ele = float(self.Tags["GPSIFD"]["GPSAltitude"][0])/self.Tags["GPSIFD"]["GPSAltitude"][1]
        #header.ele = self.rawheader["falcon"]["baro_height"]/10.0**3 #todo: Hoehenmodell beruecksichtigen!
        header.pitch = evaldiv(soup.find("flir:mavpitch").text)
        #header.pitch = self.rawheader["falcon"]["angle_pitch"]/10.0**2
        header.roll = evaldiv(soup.find("flir:mavroll").text)
        #header.roll = self.rawheader["falcon"]["angle_roll"]/10.0**2
        header.yaw = evaldiv(soup.find("flir:mavyaw").text)
        #header.yaw = self.rawheader["falcon"]["angle_yaw"]/10.0**2
        header.speed_x = -999
        #header.speed_x = self.rawheader["falcon"]["gps_speed_x"]/10.0**3
        header.speed_y = -999
        #header.speed_y = self.rawheader["falcon"]["gps_speed_y"]/10.0**3
        header.acc_x  = -999
        #header.acc_x = self.rawheader["dlr"]["gps_acc_x"]/10.0**3
        header.acc_y =  -999
        #header.acc_y = self.rawheader["dlr"]["gps_acc_y"]/10.0**3
        header.cam_serial = self.Tags["CameraSerialNumber"]
        #header.cam_serial = self.rawheader["camera"]["sernum"]
        header.cam_ser_sensor =  ""
        #header.cam_ser_sensor = self.rawheader["camera"]["sernum_sensor"]
        header.cam_version = self.Tags["Model"]
        #header.cam_version = self.rawheader["camera"]["version"]
        header.cam_fw_version = self.Tags["Software"]
        #header.cam_fw_version = self.rawheader["camera"]["fw_version"]
        header.cam_partnum = ""
        #header.cam_partnum = self.rawheader["camera"]["partnum"]
        header.cam_crc_err_cnt = ""
        #header.cam_crc_err_cnt = self.rawheader["camera"]["crc_error_cnt"]
        header.cam_dcmi_err_cnt = ""
        #header.cam_dcmi_err_cnt = self.rawheader["camera"]["dcmi_error_cnt"]
        header.cam_coretemp = -999
        #header.cam_coretemp = self.rawheader["camera"]["sensortemperature"]/10.0
        header.cam_pitch = evaldiv(soup.find("camera:pitch").text)
        #header.cam_pitch = self.rawheader["falcon"]["cam_angle_pitch"]/10.0**2
        header.cam_roll = evaldiv(soup.find("camera:roll").text)
        #header.cam_roll = self.rawheader["falcon"]["cam_angle_roll"]/10.0**2
        header.cam_yaw = evaldiv(soup.find("camera:yaw").text)
        #header.cam_yaw = self.rawheader["falcon"]["cam_angle_yaw"]/10.0**2
        
        header.start_lat = 0
        #header.start_lat = self.rawheader["startup_gps"]["lat"]/10.0**7
        header.start_lon = 0
        #header.start_lon = self.rawheader["startup_gps"]["long"]/10.0**7
        header.start_elevation = 0
        #header.start_elevation = self.rawheader["startup_gps"]["height"]/10.0**3
        header.start_hor_accur = 0
        #header.start_hor_accur = self.rawheader["startup_gps"]["hor_accuracy"]/10.0**3
        header.start_ver_accur = 0
        #header.start_ver_accur = self.rawheader["startup_gps"]["vert_accuracy"]/10.0**3
        header.start_speed_accur = 0
        #header.start_speed_accur = self.rawheader["startup_gps"]["speed_accuracy"]/10.0**3
        header.start_speed_x = 0
        #header.start_speed_x = self.rawheader["startup_gps"]["speed_x"]/10.0**3
        header.start_speed_y = 0
        #header.start_speed_y = self.rawheader["startup_gps"]["speed_y"]/10.0**3
        
        header.fw_major = 0
        #header.fw_major = self.rawheader["firmware_version"]["major"]
        header.fw_minor = 0
        #header.fw_minor = self.rawheader["firmware_version"]["minor"]
        header.fw_buildcount = 0
        #header.fw_buildcount = self.rawheader["firmware_version"]["build_count"]
        header.fw_timestamp = 0
        #header.fw_timestamp = str(datetime.datetime.fromtimestamp(self.rawheader["firmware_version"]["timestamp"]))
        header.fw_svnrev = 0
        #header.fw_svnrev = self.rawheader["firmware_version"]["svn_revision"]
        
        #header.asc_version = self.rawheader["asctec"]["version"]
        #header.asc_checksum = self.rawheader["asctec"]["checksum"]
        #header.asc_mode = self.rawheader["asctec"]["mode"]
        #header.asc_trigcnt = self.rawheader["asctec"]["trigger_counter"]
        #header.asc_bitpix = self.rawheader["asctec"]["bit_per_pixel"]
        #header.asc_bytepix = self.rawheader["asctec"]["byte_per_pixel"]
        #header.asc_colmin = self.rawheader["asctec"]["color_min"]
        #header.asc_colmax = self.rawheader["asctec"]["color_max"]
        
        
        tstr = self.Tags["ExifIFD"]["DateTimeOriginal"]
        dt = datetime.datetime.strptime(tstr, "%Y:%m:%d %H:%M:%S")
        #dt = datetime(tstr)
        header.gps_date = dt.strftime("%Y:%m:%d")
        header.gps_time = dt.strftime("%H:%M:%S")
        header.gps_time_ms = 0
        #header.utc = 
        #utc = gpstime.UTCFromGps(self.rawheader["falcon"]["gps_week"],self.rawheader["falcon"]["gps_time_ms"]/1000)
        #utc = gpstime.UTCFromGps(self.rawheader["falcon"]["gps_week"],self.rawheader["falcon"]["gps_time_ms"]/1000)
        #header.utc = utc
        #header.gps_date = "%04d-%02d-%02d"%(utc[0],utc[1],utc[2])
        #header.gps_time = "%02d:%02d:%02d"%(utc[3],utc[4],int(utc[5]))
        #header.gps_time_ms = self.rawheader["falcon"]["gps_time_ms"]
        #header.gps_week = self.rawheader["falcon"]["gps_week"]
        header.erkennung = ""
        #header.erkennung = self.rawheader["dlr"]["erkennung"]
        if header.erkennung in ["DLR","DL2"] :
            header.version = "%d.%d" % (self.rawheader["dlr"]["version_major"],self.rawheader["dlr"]["version_minor"])
            header.cam_pitch_offset = self.rawheader["dlr"]["cam_pitch_offset"]/10.0**3
            header.cam_roll_offset = self.rawheader["dlr"]["cam_roll_offset"]/10.0**3
            header.cam_yaw_offset = self.rawheader["dlr"]["cam_yaw_offset"]/10.0**3
            header.boresight_ts = str(datetime.datetime.fromtimestamp(self.rawheader["dlr"]["boresight_calib_timestamp"]))
            
            header.radiom_B = self.rawheader["dlr"]["radiometric_B"]/10.0**2
            header.radiom_R = self.rawheader["dlr"]["radiometric_R"]/10.0**3
            header.radiom_F = self.rawheader["dlr"]["radiometric_F"]/10.0**3
            header.radiom_ts = str(datetime.datetime.fromtimestamp(self.rawheader["dlr"]["radiometric_calib_timestamp"]))
            
            header.geom_fx = self.rawheader["dlr"]["geometric_fx"]/10.0
            header.geom_fy = self.rawheader["dlr"]["geometric_fy"]/10.0
            header.geom_cx = self.rawheader["dlr"]["geometric_cx"]/10.0
            header.geom_cy = self.rawheader["dlr"]["geometric_cy"]/10.0
            header.geom_skew = self.rawheader["dlr"]["geometric_skew"]/10.0**3
            header.geom_k1 = self.rawheader["dlr"]["geometric_k1"]/10.0**3
            header.geom_k2 = self.rawheader["dlr"]["geometric_k2"]/10.0**3
            header.geom_k3 = self.rawheader["dlr"]["geometric_k3"]/10.0**3
            header.geom_p1 = self.rawheader["dlr"]["geometric_p1"]/10.0**3
            header.geom_p2 = self.rawheader["dlr"]["geometric_p2"]/10.0**3
            header.geom_pixelshift_x = self.rawheader["dlr"]["geometric_pixelshift_x"]/10.0**8
            header.geom_pixelshift_y = self.rawheader["dlr"]["geometric_pixelshift_y"]/10.0**8
            header.geom_ts = str(datetime.datetime.fromtimestamp(self.rawheader["dlr"]["geometric_calib_timestamp"]))
            
            header.platzhalter = self.rawheader["dlr"]["platzhalter"]
            
            header.raw_size = self.rawheader["dlr"]["raw_size"]
            header.img_size = self.rawheader["dlr"]["img_size"]
            
            header.platzhalter2 = self.rawheader["dlr"]["platzhalter2"]
            
            header.chgflags_lat = self.rawheader["dlr"]["changed_flags"] & CHANGEDFLAGS.LAT
            header.chgflags_lon = self.rawheader["dlr"]["changed_flags"] & CHANGEDFLAGS.LON
            header.chgflags_baro = self.rawheader["dlr"]["changed_flags"] & CHANGEDFLAGS.BAROHEIGHT
            header.chgflags_sll = self.rawheader["dlr"]["changed_flags"] & CHANGEDFLAGS.START_LATLON
            header.chgflags_sele = self.rawheader["dlr"]["changed_flags"] & CHANGEDFLAGS.START_ELEVATION
            
            header.errflags_allmeta = self.rawheader["dlr"]["error_flags"] & ERRORFLAGS.ALL_META
            header.errflags_ll = self.rawheader["dlr"]["error_flags"] & ERRORFLAGS.LATLON
            header.errflags_baro = self.rawheader["dlr"]["error_flags"] & ERRORFLAGS.BAROHEIGHT
            header.errflags_sll = self.rawheader["dlr"]["error_flags"] & ERRORFLAGS.START_LATLON
            header.errflags_sele = self.rawheader["dlr"]["error_flags"] & ERRORFLAGS.START_ELEVATION
            header.errflags_pitch = self.rawheader["dlr"]["error_flags"] & ERRORFLAGS.FAST_PITCH
            header.errflags_roll = self.rawheader["dlr"]["error_flags"] & ERRORFLAGS.FAST_ROLL
            
            header.flags_mot = self.rawheader["dlr"]["flags"] & FLAGS.MOTORS_ON
            header.flags_cam = self.rawheader["dlr"]["flags"] & FLAGS.CAM_CHANGED
            header.flags_flipped_hor = self.rawheader["dlr"]["flags"] & FLAGS.FLIPPED_HOR
            header.flags_flipped_ver = self.rawheader["dlr"]["flags"] & FLAGS.FLIPPED_VER
            header.pois = []
            for k,i in enumerate(self.rawheader["dlr"]["pois"]):
                header.pois.append({"id":i["id"],"x":i["x"],"y":i["y"]})
        
        return header

class LoadJpg(object):
    Tags = {}
    def __init__(self,infile,bitsPerPixel=np.uint16):
        self.infile = infile
        self.read_raw(infile)
        self.filename = os.path.basename(str(infile))
        self.header = self.fill_header()
        
    def read_raw(self, filepath):
        with tf.TiffFile(os.path.normpath(str(filepath))) as tif:
            self.rawbody = tif.asarray()
            for page in tif.pages:
                for tag in page.tags.values():
                    self.Tags[tag.name] = tag.value
            self.image = self.rawbody
    def fill_header(self):    
        header = flirsd.Header()
        header.filename = self.filename
        
        lat = self.Tags["GPSIFD"]["GPSLatitude"]
        lon = self.Tags["GPSIFD"]["GPSLongitude"]
        header.lat = dms2dd(float(lat[0])/lat[1],float(lat[2])/lat[3],float(lat[4])/lat[5],self.Tags["GPSIFD"]["GPSLatitudeRef"])
        header.lon = dms2dd(float(lon[0])/lon[1],float(lon[2])/lon[3],float(lon[4])/lon[5],self.Tags["GPSIFD"]["GPSLongitudeRef"])
        header.start_lat = 0
        header.start_lon = 0
        try:
            header.UTM_Y,header.UTM_X,header.ZoneNumber,header.ZoneLetter = utm.from_latlon(header.lat,header.lon)
            header.start_UTM_Y,header.start_UTM_X,header.start_ZoneNumber,header.start_ZoneLetter = utm.from_latlon(header.start_lat,header.start_lon)
        except:
            base,file = os.path.split(str(self.infile))
            print("latlon wrong at", file, "lat:", header.lat,"lon:",header.lon)  
        
        soup = BeautifulSoup(self.Tags["XMP"],"lxml")
        
        header.baro = evaldiv(soup.find("flir:mavrelativealtitude").text)
        header.ele = float(self.Tags["GPSIFD"]["GPSAltitude"][0])/self.Tags["GPSIFD"]["GPSAltitude"][1]
        header.pitch = evaldiv(soup.find("flir:mavpitch").text)
        header.roll = evaldiv(soup.find("flir:mavroll").text)
        header.yaw = evaldiv(soup.find("flir:mavyaw").text)
        header.speed_x = -999
        header.speed_y = -999
        header.acc_x  = -999
        header.acc_y =  -999
        header.cam_serial = self.Tags["CameraSerialNumber"]
        header.cam_ser_sensor =  ""
        header.cam_version = self.Tags["Model"]
        header.cam_fw_version = self.Tags["Software"]
        header.cam_partnum = ""
        header.cam_crc_err_cnt = ""
        header.cam_dcmi_err_cnt = ""
        header.cam_coretemp = -999
        header.cam_pitch = evaldiv(soup.find("camera:pitch").text)
        header.cam_roll = evaldiv(soup.find("camera:roll").text)
        header.cam_yaw = evaldiv(soup.find("camera:yaw").text)
        
        header.start_lat = 0
        header.start_lon = 0
        header.start_elevation = 0
        header.start_hor_accur = 0
        header.start_ver_accur = 0
        header.start_speed_accur = 0
        header.start_speed_x = 0
        header.start_speed_y = 0
        header.fw_major = 0
        header.fw_minor = 0
        header.fw_buildcount = 0
        header.fw_timestamp = 0
        header.fw_svnrev = 0
        
        
        tstr = self.Tags["ExifIFD"]["DateTimeOriginal"]
        dt = datetime.datetime.strptime(tstr, "%Y:%m:%d %H:%M:%S")
        header.gps_date = dt.strftime("%Y:%m:%d")
        header.gps_time = dt.strftime("%H:%M:%S")
        header.gps_time_ms = 0
        header.erkennung = ""
        if header.erkennung in ["DLR","DL2"] :
            header.version = "%d.%d" % (self.rawheader["dlr"]["version_major"],self.rawheader["dlr"]["version_minor"])
            header.cam_pitch_offset = self.rawheader["dlr"]["cam_pitch_offset"]/10.0**3
            header.cam_roll_offset = self.rawheader["dlr"]["cam_roll_offset"]/10.0**3
            header.cam_yaw_offset = self.rawheader["dlr"]["cam_yaw_offset"]/10.0**3
            header.boresight_ts = str(datetime.datetime.fromtimestamp(self.rawheader["dlr"]["boresight_calib_timestamp"]))
            
            header.radiom_B = self.rawheader["dlr"]["radiometric_B"]/10.0**2
            header.radiom_R = self.rawheader["dlr"]["radiometric_R"]/10.0**3
            header.radiom_F = self.rawheader["dlr"]["radiometric_F"]/10.0**3
            header.radiom_ts = str(datetime.datetime.fromtimestamp(self.rawheader["dlr"]["radiometric_calib_timestamp"]))
            
            header.geom_fx = self.rawheader["dlr"]["geometric_fx"]/10.0
            header.geom_fy = self.rawheader["dlr"]["geometric_fy"]/10.0
            header.geom_cx = self.rawheader["dlr"]["geometric_cx"]/10.0
            header.geom_cy = self.rawheader["dlr"]["geometric_cy"]/10.0
            header.geom_skew = self.rawheader["dlr"]["geometric_skew"]/10.0**3
            header.geom_k1 = self.rawheader["dlr"]["geometric_k1"]/10.0**3
            header.geom_k2 = self.rawheader["dlr"]["geometric_k2"]/10.0**3
            header.geom_k3 = self.rawheader["dlr"]["geometric_k3"]/10.0**3
            header.geom_p1 = self.rawheader["dlr"]["geometric_p1"]/10.0**3
            header.geom_p2 = self.rawheader["dlr"]["geometric_p2"]/10.0**3
            header.geom_pixelshift_x = self.rawheader["dlr"]["geometric_pixelshift_x"]/10.0**8
            header.geom_pixelshift_y = self.rawheader["dlr"]["geometric_pixelshift_y"]/10.0**8
            header.geom_ts = str(datetime.datetime.fromtimestamp(self.rawheader["dlr"]["geometric_calib_timestamp"]))
            
            header.platzhalter = self.rawheader["dlr"]["platzhalter"]
            
            header.raw_size = self.rawheader["dlr"]["raw_size"]
            header.img_size = self.rawheader["dlr"]["img_size"]
            
            header.platzhalter2 = self.rawheader["dlr"]["platzhalter2"]
            
            header.chgflags_lat = self.rawheader["dlr"]["changed_flags"] & CHANGEDFLAGS.LAT
            header.chgflags_lon = self.rawheader["dlr"]["changed_flags"] & CHANGEDFLAGS.LON
            header.chgflags_baro = self.rawheader["dlr"]["changed_flags"] & CHANGEDFLAGS.BAROHEIGHT
            header.chgflags_sll = self.rawheader["dlr"]["changed_flags"] & CHANGEDFLAGS.START_LATLON
            header.chgflags_sele = self.rawheader["dlr"]["changed_flags"] & CHANGEDFLAGS.START_ELEVATION
            
            header.errflags_allmeta = self.rawheader["dlr"]["error_flags"] & ERRORFLAGS.ALL_META
            header.errflags_ll = self.rawheader["dlr"]["error_flags"] & ERRORFLAGS.LATLON
            header.errflags_baro = self.rawheader["dlr"]["error_flags"] & ERRORFLAGS.BAROHEIGHT
            header.errflags_sll = self.rawheader["dlr"]["error_flags"] & ERRORFLAGS.START_LATLON
            header.errflags_sele = self.rawheader["dlr"]["error_flags"] & ERRORFLAGS.START_ELEVATION
            header.errflags_pitch = self.rawheader["dlr"]["error_flags"] & ERRORFLAGS.FAST_PITCH
            header.errflags_roll = self.rawheader["dlr"]["error_flags"] & ERRORFLAGS.FAST_ROLL
            
            header.flags_mot = self.rawheader["dlr"]["flags"] & FLAGS.MOTORS_ON
            header.flags_cam = self.rawheader["dlr"]["flags"] & FLAGS.CAM_CHANGED
            header.flags_flipped_hor = self.rawheader["dlr"]["flags"] & FLAGS.FLIPPED_HOR
            header.flags_flipped_ver = self.rawheader["dlr"]["flags"] & FLAGS.FLIPPED_VER
            header.pois = []
            for k,i in enumerate(self.rawheader["dlr"]["pois"]):
                header.pois.append({"id":i["id"],"x":i["x"],"y":i["y"]})
        
        return header

        
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
            