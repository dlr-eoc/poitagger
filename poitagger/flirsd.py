from __future__ import print_function
import cv2
import numpy as np
import struct
import os
import traceback
import datetime
import pytz
import utm
import gpstime

__version__ = "0.3.2"
       
CAMERA_CALIBRATION = [
  {
    "owner":"PELZ",
    "camera":"Tau640",
    "type":"IR_CAM",
    "header_size":512,
    "resolution":(640,512),
    "serial":3592, 
    "bad_pixels_v":[],
    "bad_pixels_h":[(192,25),(192,26),(298,329),(298,330),(7,435),(66,412),
        (66,413),(403,506),(403,507),(168,385),(302,256),(403,508),(273,205),
        (288,210),(419,208)],
    "bad_lines_h":[(372,281,512),(144,404,512)],
    "bad_lines_v":[],
    "set_mid_value":[]
  },
  {
    "owner":"DLR",
    "camera":"Quark640",
    "type":"IR_CAM",
    "header_size":512,
    "resolution":(640,512),
    "serial":739551, 
    "bad_pixels_v":[],
    "bad_pixels_h":[],
    "bad_lines_h":[],
    "bad_lines_v":[],
    "set_mid_value":[(0,0,640,9)]
  },
  # {
    # "owner":"DLR",
    # "camera":"Tau640",
    # "type":"IR_CAM",
    # "header_size":512,
    # "resolution":(640,512),
    # "serial":0, 
    # "bad_pixels_v":[(158,33),(159,33)],
    # "bad_pixels_h":[(164,53),(292,71),(347,71),(387,120),(387,121),(435,86),
        # (178,231),(491,393),(358,480),(210,460),(210,461),(631,489)],
    # "bad_lines_v":[],
    # "bad_lines_h":[]
  # },
  # {
    # "owner":"DLR",
    # "camera":"Tau640",
    # "type":"IR_CAM",
    # "header_size":512,
    # "resolution":(640,512),
    # "serial":0, 
    # "bad_pixels_v":[(158,478),(159,478),(434,425),(435,425)],
    # "bad_pixels_h":[(8,22),(281,31),(429,50),(429,51),(461,280),(252,390),
        # (252,391),(347,440),(292,440),(204,425),(475,458),(480,478),(481,478),
        # (358,31),(631,22),(210,50),(210,51),(178,280),(387,390),(387,391),
        # (434,425),(164,458),(491,118)],
    # "bad_lines_v":[],
    # "bad_lines_h":[]
  # },
  {
    "owner":"DLR",
    "camera":"Tau640",
    "type":"IR_CAM",
    "header_size":512,
    "resolution":(640,512),
    "serial":3510, 
    "bad_pixels_v":[(158,478),(159,478),(434,425),(435,425)],
    "bad_pixels_h":[(8,22),(281,31),(429,50),(429,51),(461,280),(252,390),
        (252,391),(347,440),(292,440),(204,425),(475,458),(480,478),(481,478),
        (358,31),(631,22),(210,50),(210,51),(178,280),(387,390),(387,391),
        (434,425),(164,458),(491,118)],
    "bad_lines_v":[],
    "bad_lines_h":[],
    "set_mid_value":[]
  },
  {
    "owner":"UNCALIBRATED",
    "camera":"?",
    "type":"IR_CAM",
    "header_size":512,
    "resolution":(640,512),
    "serial":0, 
    "bad_pixels_v":[],
    "bad_pixels_h":[],
    "bad_lines_v":[],
    "bad_lines_h":[]
  }]


def get_calib(key,value,calibdict=CAMERA_CALIBRATION):
    try:
        return next(entry for entry in calibdict if entry[key] == value)
    except:
       # print "no Calibration found!"
        return calibdict[-1]
        
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
    
    
class Header(object):
    lat,lon = 0.0,0.0
    filename = ""
    UTM_Y,UTM_X,ZoneNumber,ZoneLetter = 0.0,0.0,32,"N"
    baro, ele, pitch, roll, yaw = 0,0,0,0,0
    speed_x, speed_y, acc_x, acc_y = 0,0,0,0
    cam_serial, cam_ser_sensor = 0,0
    cam_version, cam_fw_version = 0,0
    cam_partnum, cam_coretemp = "",0
    cam_crc_err_cnt, cam_dcmi_err_cnt = 0,0
    cam_pitch, cam_roll, cam_yaw = 0,0,0
    start_lat, start_lon, start_elevation = 0,0,0
    start_hor_accur, start_ver_accur, start_speed_accur = 0,0,0
    start_speed_x, start_speed_y = 0,0 
    fw_major, fw_minor = 0,0
    fw_buildcount, fw_timestamp,fw_svnrev = 0,"",""
    asc_version, asc_checksum = 0,0
    asc_mode, asc_trigcnt = 0,0
    asc_bitpix, asc_bytepix = 14,2
    asc_colmin, asc_colmax = 0,0
    cam_pitch_offset, cam_roll_offset,cam_yaw_offset = 0,0,0
    boresight_ts = ""
    radiom_B, radiom_R, radiom_F,radiom_ts = 300,12000,1,""
    geom_fx, geom_fy, geom_cx, geom_cy = 1115,1115,320,256
    geom_k1, geom_k2, geom_k3 = 0,0,0
    geom_skew, geom_p1, geom_p2, geom_ts = 0,0,0,""
    geom_pixelshift_x, geom_pixelshift_y = 17e-6, 17e-6
    platzhalter, platzhalter2,erkennung  = "","","DLR"
    version = "1.0"
    chgflags_lat, chgflags_lon, chgflags_baro = False,False,False
    chgflags_sll, chgflags_sele = False, False
    errflags_allmeta, errflags_ll, errflags_baro = False, False, False
    errflags_sll, errflags_sele = False, False
    errflags_pitch, errflags_roll = False, False
    flags_mot, flags_cam = False, False 
    flags_flipped_hor, flags_flipped_ver = True, False 
    gps_time_ms = 0
    gps_week = 0
    
    
    pois = []#{"id":0,"x":0,"y":0}]
    raw_size = 0
    img_size = 0
    
    
class ConvertRaw(object): 
    rawheader = []
    def __init__(self,infile,bitsPerPixel=np.uint16):
        self.infile = infile
        self.read_raw(infile,bitsPerPixel = bitsPerPixel)
        self.filename = os.path.basename(str(infile))
        self.header = self.fill_header()
        
    def correct_pixelerrors(self,serialnr= None,calibdict=CAMERA_CALIBRATION):
        if not serialnr == None:
            self.calib = get_calib("serial",serialnr,calibdict)#self.rawheader["camera"]["sernum"]
            #print "calib:",self.calib
            self.blurpixelerrors()
        
    def blur_pixel_h(self, xxx_todo_changeme):
        #print "blur", pixel_x,pixel_y
        (pixel_x,pixel_y) = xxx_todo_changeme
        left = self.rawbody[pixel_y,pixel_x-1]
        right = self.rawbody[pixel_y,pixel_x+1]
        self.rawbody[pixel_y,pixel_x] = (left + right )/2

    def blur_pixel_v(self, xxx_todo_changeme1):
        (pixel_x,pixel_y) = xxx_todo_changeme1
        top = self.rawbody[pixel_y-1,pixel_x]
        bottom = self.rawbody[pixel_y+1,pixel_x]
        self.rawbody[pixel_y,pixel_x] = (top + bottom )/2
            
    def blurline(self, xxx_todo_changeme2):
        (px_x,px_y1,px_y2) = xxx_todo_changeme2
        for i in range(px_y1,px_y2):
            self.blur_pixel_h((px_x,i))

    def blurline_v(self, xxx_todo_changeme3):
        (px_x1,px_x2,px_y) = xxx_todo_changeme3
        for i in range(px_x1,px_x2):
            self.blur_pixel_v((i,px_y))

    def blurpixelerrors(self):
        [self.blur_pixel_h(hpe) for hpe in self.calib["bad_pixels_h"]]
        [self.blur_pixel_v(vpe) for vpe in self.calib["bad_pixels_v"]]
        [self.blurline(hple) for hple in self.calib["bad_lines_h"]]
        [self.blurline_v(vple) for vple in self.calib["bad_lines_v"]]
        [self.set_mid_value(fa) for fa in self.calib["set_mid_value"]]
        
    def set_mid_value(self, xxx_todo_changeme4):
        (x_topleft,y_topleft,x_bottomright,y_bottomright) = xxx_todo_changeme4
        mid = int(self.rawbody.mean())
        #print "midvalue:",mid         
        #print  "vorher", self.rawbody[y_topleft,x_topleft]
        #print self.rawbody[y_topleft+1,x_topleft+1]
        #print self.rawbody[y_bottomright-1,x_bottomright-1]
        #print self.rawbody[y_bottomright,x_bottomright-1]
        self.rawbody[y_topleft:y_bottomright,x_topleft:x_bottomright]= mid
        #print  "nachher", self.rawbody[y_topleft,x_topleft]
        #print self.rawbody[y_topleft+1,x_topleft+1]
        #print self.rawbody[y_bottomright-1,x_bottomright-1]
        #print self.rawbody[y_bottomright,x_bottomright-1]
        
    def normalize(self, xxx_todo_changeme5=(640,512)):
        '''
            just reduction to 8bit
        '''
        (im_width,im_height) = xxx_todo_changeme5
        self.normalized = self.rawbody - self.rawbody.min()
        y,x = np.unravel_index(self.rawbody.argmax(), self.rawbody.shape)
        self.normalized *= 255.0/self.normalized.max() 
        self.arr8b = np.array(self.normalized, dtype=np.uint8) 
        self.arr8b = np.fliplr(np.reshape(self.arr8b, (im_height,im_width))) 
        return Image(self.arr8b)#.transpose())
    
    def normalize2(self, fliphor = True):
        '''
            just reduction to 8bit
        '''
        self.normalized = self.rawbody - self.rawbody.min()
        self.normalized *= 255.0/self.normalized.max() 
        flipped = np.fliplr(self.normalized) if fliphor else self.normalized
        gray = np.array(flipped, dtype=np.uint8) 
        return gray
    
    def analog(self, fliphor = True):
        '''
            reduction to 8bit and cut off the 5% tail rejection
        '''
        ma = self.rawbody.max()
        mi = self.rawbody.min()
        hist,edges = np.histogram(self.rawbody,ma-mi)
        width , height =  self.rawbody.shape

        tailreject = width*height/100*5
        reversed_hist = hist[::-1]
        reversed_edges = edges[::-1]
        tr_ridx = np.argmax(np.cumsum(reversed_hist)>tailreject)
        tr_idx = np.argmax(np.cumsum(hist)>tailreject)

        black = edges[tr_idx]
        white = reversed_edges[tr_ridx]

        compressed = self.rawbody
        compressed[compressed > white] = white
        compressed[compressed < black] = black
        norm = compressed - black
        norm *= 255.0/norm.max()
        flipped = np.fliplr(norm) if fliphor else norm
        gray = np.array(flipped, dtype=np.uint8) 
        return gray
    
    def homogenize(self, aperture_x=149,aperture_y=149, fliphor = True):
        '''
            homogenization in 16 bit and afterwards normalization (reduction to 8 bit)
        '''
        hpf = 16384 - cv2.GaussianBlur(self.rawbody,(aperture_x,aperture_y),0)
        mat = hpf.astype("float")/16384
        img = self.rawbody * mat
        self.normalized = img - img.min()
        self.normalized *= 255.0/self.normalized.max() 
        flipped = np.fliplr(self.normalized) if fliphor else self.normalized
        gray = np.array(flipped, dtype=np.uint8) 
        #self.img = cv2.merge((gray,gray,gray))
        return gray
        
    def save(self,outfile,quality=None):
        try:
            if not quality == None:
                cv2.imwrite(outfile,self.img,[int(cv2.IMWRITE_JPEG_QUALITY), quality])
            else:
                cv2.imwrite(outfile,self.img)
        except:
            print("Save img failed!")
            print(traceback.format_exc())
    
    def saveraw(self,outpath=None):
        self.get_header()
        if outpath==None: outpath = self.infile
        try:
            header = struct.pack(self.fmt, *self.headerarray)
            with open(outpath,"wb") as f:
                f.write(header)
                f.write(self.rawbody)
        except:
            print("saveraw failed")
            print("header",self.headerarray)
            print(traceback.format_exc())
    def get_header(self):
        self.headerarray[0] = self.rawheader["bitmap"]["mark"]                  # H 
        self.headerarray[1] = self.rawheader["bitmap"]["filelength"]            # I
        self.headerarray[2] = self.rawheader["bitmap"]["reserved"]              # I
        self.headerarray[3] = self.rawheader["bitmap"]["offset"]                # I
        self.headerarray[4] = self.rawheader["bitmap"]["hsize"]                 # I
        self.headerarray[5] = self.rawheader["bitmap"]["width"]                 # I
        self.headerarray[6] = self.rawheader["bitmap"]["height"]                # I
        self.headerarray[7] = self.rawheader["bitmap"]["planes"]                # H
        self.headerarray[8] = self.rawheader["bitmap"]["bitperpixel"]           # H
        self.headerarray[9] = self.rawheader["bitmap"]["compression"]           # I
        self.headerarray[10] = self.rawheader["bitmap"]["datasize"]             # I
        self.headerarray[11] = self.rawheader["bitmap"]["ppm_x"]                # I
        self.headerarray[12] = self.rawheader["bitmap"]["ppm_y"]                # I
        self.headerarray[13] = self.rawheader["bitmap"]["colors"]               # I
        self.headerarray[14] = self.rawheader["bitmap"]["colors2"]              # I
        
        self.headerarray[15] = self.rawheader["asctec"]["version"]              # H
        self.headerarray[16] = self.rawheader["asctec"]["checksum"]             # H
        self.headerarray[17] = self.rawheader["asctec"]["mode"]                 # H
        self.headerarray[18] = self.rawheader["asctec"]["trigger_counter"]      # H
        self.headerarray[19] = self.rawheader["asctec"]["bit_per_pixel"]        # H
        self.headerarray[20] = self.rawheader["asctec"]["byte_per_pixel"]       # H
        self.headerarray[21] = self.rawheader["asctec"]["color_min"]            # I
        self.headerarray[22] = self.rawheader["asctec"]["color_max"]            # I
        
        self.headerarray[23] = self.rawheader["camera"]["sernum"]               # I
        self.headerarray[24] = self.rawheader["camera"]["sernum_sensor"]        # I
        self.headerarray[25] = self.rawheader["camera"]["version"]              # I
        self.headerarray[26] = self.rawheader["camera"]["fw_version"]           # I
        self.headerarray[27] = self.rawheader["camera"]["sensortemperature"]    # H
        self.headerarray[28] = self.rawheader["camera"]["crc_error_cnt"]        # I
        self.headerarray[29] = self.rawheader["camera"]["dcmi_error_cnt"]       # I
        self.headerarray[30] = self.rawheader["camera"]["partnum"]              # 32s
        
        self.headerarray[31] = self.rawheader["falcon"]["time_ms"]              # I
        self.headerarray[32] = self.rawheader["falcon"]["gps_week"]             # H
        self.headerarray[33] = self.rawheader["falcon"]["gps_time_ms"]          # I
        self.headerarray[34] = self.rawheader["falcon"]["gps_long"]             # i 10.0**7
        self.headerarray[35] = self.rawheader["falcon"]["gps_lat"]              # i 10.0**7
        self.headerarray[36] = self.rawheader["falcon"]["baro_height"]          # i 10.0**3
        self.headerarray[37] = self.rawheader["falcon"]["gps_hor_accuracy"]         # H 10.0**3
        self.headerarray[38] = self.rawheader["falcon"]["gps_vert_accuracy"]        # H 10.0**3
        self.headerarray[39] = self.rawheader["falcon"]["gps_speed_accuracy"]       # H 10.0**3
        self.headerarray[40] = self.rawheader["falcon"]["gps_speed_x"]              # h 10.0**3
        self.headerarray[41] = self.rawheader["falcon"]["gps_speed_y"]              # h 10.0**3
        self.headerarray[42] = self.rawheader["falcon"]["angle_pitch"]              # h 10.0**2
        self.headerarray[43] = self.rawheader["falcon"]["angle_roll"]               # h 10.0**2
        self.headerarray[44] = self.rawheader["falcon"]["angle_yaw"]                # H 10.0**2
        self.headerarray[45] = self.rawheader["falcon"]["cam_angle_pitch"]          # h 10.0**2
        self.headerarray[46] = self.rawheader["falcon"]["cam_angle_roll"]           # h 10.0**2
        self.headerarray[47] = self.rawheader["falcon"]["cam_angle_yaw"]            # h 10.0**2
        
        self.headerarray[48] = self.rawheader["firmware_version"]["major"]          # H
        self.headerarray[49] = self.rawheader["firmware_version"]["minor"]          # H
        self.headerarray[50] = self.rawheader["firmware_version"]["build_count"]    # I
        self.headerarray[51] = self.rawheader["firmware_version"]["timestamp"]      # I
        self.headerarray[52] = self.rawheader["firmware_version"]["svn_revision"]   # 32s
        
        self.headerarray[53] = self.rawheader["startup_gps"]["long"]                # i 10.0**7
        self.headerarray[54] = self.rawheader["startup_gps"]["lat"]                 # i 10.0**7
        self.headerarray[55] = self.rawheader["startup_gps"]["height"]              # i 10.0**3
        self.headerarray[56] = self.rawheader["startup_gps"]["hor_accuracy"]        # H 10.0**3
        self.headerarray[57] = self.rawheader["startup_gps"]["vert_accuracy"]       # H 10.0**3
        self.headerarray[58] = self.rawheader["startup_gps"]["speed_accuracy"]      # H 10.0**3
        self.headerarray[59] = self.rawheader["startup_gps"]["speed_x"]             # h 10.0**3
        self.headerarray[60] = self.rawheader["startup_gps"]["speed_y"]             # h 10.0**3
        
        self.headerarray[61] = self.rawheader["dlr"]["platzhalter"]         # 100s
        self.headerarray[62] = self.rawheader["dlr"]["cam_pitch_offset"]    # h 10.0**3   
        self.headerarray[63] = self.rawheader["dlr"]["cam_roll_offset"]     # h 10.0**3
        self.headerarray[64] = self.rawheader["dlr"]["cam_yaw_offset"]      # h 10.0**3
        self.headerarray[65] = self.rawheader["dlr"]["boresight_calib_timestamp"] # I timestamp
        self.headerarray[66] = self.rawheader["dlr"]["gps_acc_x"]           # h 10.0**3
        self.headerarray[67] = self.rawheader["dlr"]["gps_acc_y"]           # h 10.0**3
        for k,i in enumerate(range(68,95,3)):                               # BHH pro poi (10 stk)
            if len(self.rawheader["dlr"]["pois"]) > k:
                self.headerarray[i] = self.rawheader["dlr"]["pois"][k]["id"]
                self.headerarray[i+1] = self.rawheader["dlr"]["pois"][k]["x"]
                self.headerarray[i+2] = self.rawheader["dlr"]["pois"][k]["y"]
        self.headerarray[98] = self.rawheader["dlr"]["changed_flags"]       # H see CHANGEDFLAGS
        self.headerarray[99] = self.rawheader["dlr"]["error_flags"]         # H  see ERRORFLAGS
        self.headerarray[100] = self.rawheader["dlr"]["radiometric_B"]       # H 10.0**2
        self.headerarray[101] = self.rawheader["dlr"]["radiometric_R"]      # I 10.0**3
        self.headerarray[102] = self.rawheader["dlr"]["radiometric_F"]      # h 10.0**3
        self.headerarray[103] = self.rawheader["dlr"]["radiometric_calib_timestamp"] # I timestamp
        self.headerarray[104] = self.rawheader["dlr"]["geometric_fx"]       # H 10.0**1
        self.headerarray[105] = self.rawheader["dlr"]["geometric_fy"]       # H 10.0**1
        self.headerarray[106] = self.rawheader["dlr"]["geometric_cx"]       # H 10.0**1
        self.headerarray[107] = self.rawheader["dlr"]["geometric_cy"]       # H 10.0**1
        self.headerarray[108] = self.rawheader["dlr"]["geometric_skew"]     # h 10.0**3
        self.headerarray[109] = self.rawheader["dlr"]["geometric_k1"]       # h 10.0**3
        self.headerarray[110] = self.rawheader["dlr"]["geometric_k2"]       # h 10.0**3
        self.headerarray[111] = self.rawheader["dlr"]["geometric_k3"]       # h 10.0**3
        self.headerarray[112] = self.rawheader["dlr"]["geometric_p1"]       # h 10.0**3
        self.headerarray[113] = self.rawheader["dlr"]["geometric_p2"]       # h 10.0**3
        self.headerarray[114] = self.rawheader["dlr"]["geometric_calib_timestamp"]  # I timestamp
        
        self.headerarray[115] = self.rawheader["dlr"]["erkennung"]  # 03s DLR
        self.headerarray[116] = self.rawheader["dlr"]["flags"]  # H see FLAGS
        self.headerarray[117] = self.rawheader["dlr"]["version_major"]  # B this DLR-Protocol extension version
        self.headerarray[118] = self.rawheader["dlr"]["version_minor"]  # B this DLR-Protocol extension version
        
        self.headerarray[119] = self.rawheader["dlr"]["geometric_pixelshift_x"]       # h 10.0**8
        self.headerarray[120] = self.rawheader["dlr"]["geometric_pixelshift_y"]       # h 10.0**8 
        self.headerarray[121] = self.rawheader["dlr"]["raw_size"]       # I 
        self.headerarray[122] = self.rawheader["dlr"]["img_size"]       # I 
        
        self.headerarray[123] = self.rawheader["dlr"]["platzhalter2"]       # 47s 
        #print "headerarray"
        #print self.headerarray[68]
        #print self.headerarray[69]
        #print self.headerarray[70]
        #print self.headerarray[71]
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
            print("read header failed")
            print(traceback.print_exc())
    
    def fill_header(self):
        #print "fill_header"
        header = Header()
        header.filename = self.filename
        #print type(self.rawheader["falcon"]["gps_lat"])
        header.lat = self.rawheader["falcon"]["gps_lat"]/10.0**7
        header.lon = self.rawheader["falcon"]["gps_long"]/10.0**7
        header.start_lat = self.rawheader["startup_gps"]["lat"]/10.0**7
        header.start_lon = self.rawheader["startup_gps"]["long"]/10.0**7
        try:
            header.UTM_Y,header.UTM_X,header.ZoneNumber,header.ZoneLetter = utm.from_latlon(header.lat,header.lon)
            header.start_UTM_Y,header.start_UTM_X,header.start_ZoneNumber,header.start_ZoneLetter = utm.from_latlon(header.start_lat,header.start_lon)
        except:
            base,file = os.path.split(str(self.infile))
            print("latlon wrong at", file, "lat:", header.lat,"lon:",header.lon)  
        header.baro = self.rawheader["falcon"]["baro_height"]/10.0**3
        header.ele = self.rawheader["falcon"]["baro_height"]/10.0**3 #todo: Hoehenmodell beruecksichtigen!
        header.pitch = self.rawheader["falcon"]["angle_pitch"]/10.0**2
        header.roll = self.rawheader["falcon"]["angle_roll"]/10.0**2
        header.yaw = self.rawheader["falcon"]["angle_yaw"]/10.0**2
        header.speed_x = self.rawheader["falcon"]["gps_speed_x"]/10.0**3
        header.speed_y = self.rawheader["falcon"]["gps_speed_y"]/10.0**3
        header.acc_x = self.rawheader["dlr"]["gps_acc_x"]/10.0**3
        header.acc_y = self.rawheader["dlr"]["gps_acc_y"]/10.0**3
        
        header.cam_serial = self.rawheader["camera"]["sernum"]
        header.cam_ser_sensor = self.rawheader["camera"]["sernum_sensor"]
        header.cam_version = self.rawheader["camera"]["version"]
        header.cam_fw_version = self.rawheader["camera"]["fw_version"]
        header.cam_partnum = self.rawheader["camera"]["partnum"]
        header.cam_crc_err_cnt = self.rawheader["camera"]["crc_error_cnt"]
        header.cam_dcmi_err_cnt = self.rawheader["camera"]["dcmi_error_cnt"]
        header.cam_coretemp = self.rawheader["camera"]["sensortemperature"]/10.0
        header.cam_pitch = self.rawheader["falcon"]["cam_angle_pitch"]/10.0**2
        header.cam_roll = self.rawheader["falcon"]["cam_angle_roll"]/10.0**2
        header.cam_yaw = self.rawheader["falcon"]["cam_angle_yaw"]/10.0**2
        
        header.start_lat = self.rawheader["startup_gps"]["lat"]/10.0**7
        header.start_lon = self.rawheader["startup_gps"]["long"]/10.0**7
        header.start_elevation = self.rawheader["startup_gps"]["height"]/10.0**3
        header.start_hor_accur = self.rawheader["startup_gps"]["hor_accuracy"]/10.0**3
        header.start_ver_accur = self.rawheader["startup_gps"]["vert_accuracy"]/10.0**3
        header.start_speed_accur = self.rawheader["startup_gps"]["speed_accuracy"]/10.0**3
        header.start_speed_x = self.rawheader["startup_gps"]["speed_x"]/10.0**3
        header.start_speed_y = self.rawheader["startup_gps"]["speed_y"]/10.0**3
        
        header.fw_major = self.rawheader["firmware_version"]["major"]
        header.fw_minor = self.rawheader["firmware_version"]["minor"]
        header.fw_buildcount = self.rawheader["firmware_version"]["build_count"]
        header.fw_timestamp = str(datetime.datetime.fromtimestamp(self.rawheader["firmware_version"]["timestamp"]))
        header.fw_svnrev = self.rawheader["firmware_version"]["svn_revision"]
        
        header.asc_version = self.rawheader["asctec"]["version"]
        header.asc_checksum = self.rawheader["asctec"]["checksum"]
        header.asc_mode = self.rawheader["asctec"]["mode"]
        header.asc_trigcnt = self.rawheader["asctec"]["trigger_counter"]
        header.asc_bitpix = self.rawheader["asctec"]["bit_per_pixel"]
        header.asc_bytepix = self.rawheader["asctec"]["byte_per_pixel"]
        header.asc_colmin = self.rawheader["asctec"]["color_min"]
        header.asc_colmax = self.rawheader["asctec"]["color_max"]
        
        utc = gpstime.UTCFromGps(self.rawheader["falcon"]["gps_week"],self.rawheader["falcon"]["gps_time_ms"]/1000)
        header.utc = utc
        header.gps_date = "%04d-%02d-%02d"%(utc[0],utc[1],utc[2])
        header.gps_time = "%02d:%02d:%02d"%(utc[3],utc[4],int(utc[5]))
        header.gps_time_ms = self.rawheader["falcon"]["gps_time_ms"]
        header.gps_week = self.rawheader["falcon"]["gps_week"]
        
        header.erkennung = self.rawheader["dlr"]["erkennung"]
        #print ("header.erkennung",header.erkennung)
        if header.erkennung in ["DLR","DL2",b'DLR'] :
            #print("header=DLR")
            header.version = "%d.%d" % (self.rawheader["dlr"]["version_major"],self.rawheader["dlr"]["version_minor"])
            header.cam_pitch_offset = self.rawheader["dlr"]["cam_pitch_offset"]/10.0**3
            header.cam_roll_offset = self.rawheader["dlr"]["cam_roll_offset"]/10.0**3
            header.cam_yaw_offset = self.rawheader["dlr"]["cam_yaw_offset"]/10.0**3
            header.boresight_ts = str(datetime.datetime.fromtimestamp(self.rawheader["dlr"]["boresight_calib_timestamp"],pytz.utc))
            
            header.radiom_B = self.rawheader["dlr"]["radiometric_B"]/10.0**2
            header.radiom_R = self.rawheader["dlr"]["radiometric_R"]/10.0**3
            header.radiom_F = self.rawheader["dlr"]["radiometric_F"]/10.0**3
            #print (self.rawheader["dlr"]["radiometric_calib_timestamp"])
            header.radiom_ts = str(datetime.datetime.fromtimestamp(self.rawheader["dlr"]["radiometric_calib_timestamp"],pytz.utc))
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
            header.geom_ts = str(datetime.datetime.fromtimestamp(self.rawheader["dlr"]["geometric_calib_timestamp"],pytz.utc))
            
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
        
    def read_body(self, fileobj,bitsPerPixel, xxx_todo_changeme6):
        (im_width,im_height) = xxx_todo_changeme6
        self.rawbody = np.fromfile(fileobj, dtype=bitsPerPixel) 
        self.rawbody = np.reshape(self.rawbody,(im_height,im_width))
        self.image = self.rawbody
    def read_bodyV2(self,fileobj,bitsPerPixel, xxx_todo_changeme7):
        (im_width,im_height) = xxx_todo_changeme7
        cnt1 = self.rawheader["dlr"]["raw_size"]
        cnt2 = self.rawheader["dlr"]["img_size"]
        print(cnt1,cnt2)
        imgraw = np.fromfile(fileobj, dtype=np.uint8,count=cnt1) 
        print("raw", len(imgraw))
        imgcorrected = np.fromfile(fileobj, dtype=np.uint8,count=cnt2) 
        print("img", len(imgcorrected))
        self.rawbody = cv2.imdecode(imgraw,cv2.cv.CV_LOAD_IMAGE_UNCHANGED)
        
        self.rawbody = np.reshape(self.rawbody,(im_height,im_width))
        
        self.image = cv2.imdecode(imgcorrected,cv2.cv.CV_LOAD_IMAGE_UNCHANGED)
        self.image = np.reshape(self.image,(im_height,im_width))
        
    def read_raw(self, filepath,headersize = 512 ,resolution = (640,512) ,bitsPerPixel = np.uint16):    
        try:
            fileobj = open(filepath, 'rb') 
        except:
            print("Open file failed")
            fileobj.close() 
        try:    
            self.read_header(fileobj,headersize)
            if self.rawheader["dlr"]["erkennung"]=="DL2":
                self.read_bodyV2(fileobj,bitsPerPixel,resolution)
            else:
                self.read_body(fileobj,bitsPerPixel,resolution)
            fileobj.close() 
        except:
            print("ConvertRaw read_raw() failed")
            traceback.print_exc()
        
class Image(object):
    def __init__(self, img):
        self.img = img      
        #print np.min(self.img)
        #self.img = scv.Image(img).flipHorizontal()
        
    def homogenize(self, aperture_x=31,aperture_y=149):
        #ddepth = cv2.CV_16S
        #self.img2 = cv2.Laplacian(self.img, ddepth, ksize=aperture_x)
        #self.img = self.img2
        import SimpleCV as scv
        self.img = scv.Image(self.img.transpose())
        hpf = self.img.smooth(aperture=(aperture_x,aperture_y),grayscale=True).invert()
        matrix = hpf.getNumpy().astype('float')/255
        img_new = self.img.getNumpy() * matrix
        self.img = scv.Image((img_new).astype('int'))
        
    def homogenize2(self, aperture_x=149,aperture_y=149):
        hpf = 16384 - cv2.GaussianBlur(self.img16,(aperture_x,aperture_y),0)
        mat = hpf.astype("float")/16384
        img = self.img16 * mat
        self.normalized = img - img.min()
        self.normalized *= 255.0/self.normalized.max() 
        flipped = np.fliplr(self.normalized)
        gray = np.array(flipped, dtype=np.uint8) 
        self.img = cv2.merge((gray,gray,gray))
        
    def save(self,outfile,quality=None):
        try:
            if not quality == None:
                cv2.imwrite(outfile,self.img,[int(cv2.IMWRITE_JPEG_QUALITY), quality])
            else:
                cv2.imwrite(outfile,self.img)
        except:#scv-image
            if not quality == None:
                self.img.save(outfile ,quality=quality) 
            else:
                self.img.save(outfile) 

class Folder(object):
    def __init__(self, path, remove_empty=True, output_prefix="Flug", input_prefix="FLIR"):
        self.folderid = 0
        self.lastfileid = 0
        self.path = path
        self.remove_empty = remove_empty
        self.output_prefix = output_prefix
        self.input_prefix = input_prefix
        
    def set_output_folder_id(self): 
        dirs = [entry for entry in os.listdir(self.path) if os.path.isdir(os.path.join(self.path,entry))]
        outdirs = [d for d in dirs if d[0:len(self.output_prefix)] == self.output_prefix]
        for d in outdirs:
            try:
                nbr = int(d[len(self.output_prefix):]) 
                if nbr > self.folderid:
                    self.folderid = nbr
            except:
                print("outdirname's suffix is not a number")
        outdir = os.path.join(self.path,"%s%03d" % (self.output_prefix,self.folderid))    
        try:
            outfolderfilelist = [f for f in os.listdir(outdir) if os.path.isfile(os.path.join(outdir,f))]
            filenr = sorted([int(os.path.splitext(entry)[0]) for entry in outfolderfilelist])
            self.lastfileid = filenr[-1] 
        except:
            self.lastfileid = 0
        #print self.lastfileid,self.folderid#,filenr,outfolderfilelist
        
    def prepare_outdir(self,imgnumber):
        try:
            nbr = int(imgnumber)
            if nbr <  self.lastfileid: 
                self.folderid += 1
            self.lastfileid = nbr
        except: 
            print("filename is not a number", imgnumber)
        outdir = os.path.join(self.path,"%s%03d" %(self.output_prefix,self.folderid))
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        return outdir
        
    def extract(self, move=True):
        self.set_output_folder_id()
        for entry in os.listdir(self.path):
            if os.path.isdir(os.path.join(self.path,entry)):
                curdir = os.path.join(self.path,entry)
                if not entry[0:len(self.input_prefix)] == self.input_prefix:
                    continue
                print(entry)
                subdir = os.listdir(curdir)
                for name in subdir:
                    curfile = os.path.join(curdir, name)
                    imgnumber, imgext = os.path.splitext(name)
                    outdir = self.prepare_outdir(imgnumber)
                    try:
                        if move : os.rename(curfile,os.path.join(outdir,name))
                    except:
                        outdir = self.prepare_outdir(int(imgnumber)-1)
                        if move : os.rename(curfile,os.path.join(outdir,name))
                if self.remove_empty:
                    subdir = os.listdir(curdir)
                    if not subdir: os.rmdir(curdir)
            
def main():
    path = "./test/00000134.ARA"
    outpng = "./test/00000134.png"
    outjpg = "./test/00000134.jpg"
    outtxt = "./test/00000134.txt"
    raw = ConvertRaw(path)
    raw.correct_pixelerrors(739551)
    image = raw.normalize()
    
    image.save(outpng)
    image.homogenize()
    image.save(outjpg,100)
    
    path = "./test/Folders"
    flirfolders = Folder(path)
    flirfolders.extract(False)#remove the False to really move the files
    raw.rawheader["falcon"]["cam_angle_roll"]=21.4
    raw.saveraw("./test/outraw.ARA")
    
if __name__ == "__main__":
    main()
        