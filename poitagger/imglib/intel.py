from .base import *

"""
typedef struct
{
	// FIXME: [optimize] 4byte allign
	// FIXME: [optimize] use falcon packet structs for memcpy -> keep position of u16 version

	// bitmap header
	//u16 bmp_mark;       // IMG_MAGIC_NUMBER aka ESEL
	u32 bmp_filelength; // 2 4 	size of BMP file in bytes (unreliable)
	u32 bmp_reserved01; // 6 2	reserved, must be zero + 8 2	reserved, must be zero
	u32 bmp_offset;	    //10 4 offset to start of image data in bytes 0x200
	u32 bmp_hdrsize;  	//14 4 size of BITMAPINFOHEADER structure, must be 40
	//Header-Laenge 108=0x6c
	//http://www.fileformat.info/format/bmp/egff.htm
	u32 bmp_width_px;   //18
	u32 bmp_height_px;	//22
	u16 bmp_planes;     //26 2 number of planes in the image, must be 1
	u16 bmp_bitperpixel;//28 2	number of bits per pixel (1, 4, 8, or 24)
	u32 bmp_compression;//30 4	compression type (0=none, 3=huff14)
	u32 bmp_data_size;  //34 4 size of image data in bytes (including padding)
	u32 bmp_ppm_x;      //38 4	horizontal resolution in pixels per meter (unreliable)
	u32 bmp_ppm_y;      //42 4	vertical resolution in pixels per meter (unreliable)
	u32 bmp_colors;     //46 4	number of colors in image, or zero
	u32 bmp_colors2;    //50 4	number of important colors, or zero
	//

	// asctec flirsd extended data
	u16 version;		 //54 =IMG_HDR_VERSION TODO: keep position!!!
	u16 checksum;        //56 *-1 der 16bit summe mit checksum=0; Not used in Video-Mode
	u16 mode;            //58 0: nix; 1: video; 2: photo; 3: serienaufnahme; 4: selbsausloeser.... :)
	u16 trigger_counter; //60 user trigger counter since power on
	// frame-counter is the filename
	u16 bit_per_pixel;   //62 cmos sensor 14bit
	u16 byte_per_pixel;  //64 storage format
	u32 color_min;       //66  Not used in Video-Mode !!!not part of checksum!!!
	u32 color_max;       //70  Not used in Video-Mode !!!not part of checksum!!!

	// caminfo
	u32 cam_sernum;     //
	u32 cam_sernum_sensor;
	u32 cam_version;
	u32 cam_fw_version;
	u16 cam_sensortemperature;
	u32 cam_dbg_uart;  // not used
	u32 cam_dbg_dcmi;  // not used
	u8  cam_partnum[32];
	u32 time_ms;  // time since falcon time received
	// gps date and time
	u16 gps_week;  // time from falcon   0 for invalid
	u32 gps_time_ms;// time from falcon  0 for invalid
	// all position data at falcon time
	i32 gps_long; //*10^7
	i32 gps_lat;  //*10^7
	i32 bar_height; //in mm
	u16 gps_hor_accuracy; //in mm
	u16 gps_vert_accuracy;
	u16 gps_speed_accuracy;
	u16 gps_speed_x; //in mm/s
	u16 gps_speed_y;
	// falcon angles
	i16 angle_pitch;      //angles [deg*100]
	i16 angle_roll;
	u16 angle_yaw;
	// cam angles
	i16 cam_angle_pitch; //in deg*100
	i16 cam_angle_roll;
	i16 cam_angle_yaw;// unused

	u16 fw_version_major;
	u16 fw_version_minor;
	u32 fw_version_build_count;
	u32 fw_version_timestamp;
	u8  fw_version_svn_revision[32]; //-4+64

	// startup/takeoff position
	i32 startup_gps_long;         //*10^7
	i32 startup_gps_lat;          //*10^7
	i32 startup_gps_height;       // [mm] height above sea level from gps
	u16 startup_gps_hor_accuracy; // mm
	u16 startup_gps_vert_accuracy;
	u16 startup_gps_speed_accuracy;
	u16 startup_gps_speed_x;       // mm/s
	u16 startup_gps_speed_y;
	//244

	// TLinear Output (R-models only)
	// With TLinear enabled and the resolution known, the 14-bit digital output can be interpreted as
	// temperature with the simple conversion below:
	//    S * Res = T_scene
	// S        Value of the pixel in14-bit digital video counts
	// Res      0.4 Kelvin/count for low resolution, 14-bit data
	//          0.04 Kelvin/count for high resolution, 14-bit data
	// T_scene 	Temperature of the scene in _Kelvin_
	u8 tlinear;           // 0: off; 1: on
	u8 tlinearResolution; // 0: Low; 1: High
	u32 R;
	i32 B1000;
	i32 F1000;
	i32 O1000;
	uint16_t gain_mode; //  0=auto; 1=low; 2=high; 3=manual

	uint16_t reserved1;
	// lens response parameters
	uint16_t lens_number;                // 0-1
	// lens response parameters for calculated responsivity
	uint16_t lens_response_FbyX;         // 4096-65535 (0.5-7.9999)    F/#    1/focal ratio
	uint16_t lens_response_transmission; // 4096-8192  (0.5-1.0)
	uint16_t reserved2;

	// lens response parameters for radiometric calculations
	uint16_t lens_response_rad_emissivity;        // 4096-8192 (0.5-1.00)                 RAD_EMISSIVITY
	uint16_t lens_response_rad_tbkg_x100;         // S15.0 (-50.00-327.67)                RAD_TBKG_X100
	uint16_t lens_response_rad_transmission_win;  // 4096-8192 (0.5-1.0)                  RAD_TRANSMISSION_WIN
	uint16_t lens_response_rad_twin_x100;         // S15.0 (-50.00-327.67)                RAD_TWIN_X100
	uint16_t lens_response_rad_tau_atm;           // 4096-8192 (F3.13 0.5-1.0)            RAD_TAU_ATM
	uint16_t lens_response_rad_tatm_x100;         // S15.0 (-50.00-327.67)                RAD_TATM_X100
	uint16_t lens_response_rad_refl_win;          // 0- RAD_TAU_WIN (F3.13 0.0-tau_win )  RAD_REFL_WIN
	uint16_t lens_response_rad_trefl_x100;        // S15.0 (-50.00-327.67)                RAD_ TREFL _X100

//	uint16_t agc_type;
//	uint16_t agc_threshold;
//	uint16_t agc_sso_percent;
//	uint16_t agc_contrast;
//	uint16_t agc_brightness;
//	uint16_t agc_brightness_bias;
//	//uint32_t agc_tail_size;
//	uint16_t agc_tail_size;
//	uint16_t agc_correct;

}ImageHeader_Typedef;
"""

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



PART = {
    "46640005":{"width":640,"height":512,"fov":126.3, "fnumber": 1.1, "focallength":5.0, "fx":408, "distortion":50 },
    "46640007":{"width":640,"height":512,"fov":130.5, "fnumber": 1.01, "focallength":7.5, "fx":408, "distortion":56 },
    "46640009":{"width":640,"height":512,"fov":65.9, "fnumber": 1.0, "focallength":9.0, "fx":767, "distortion":18 },
    "46640013":{"width":640,"height":512,"fov":42.0, "fnumber": 1.0, "focallength":13.0, "fx":1167, "distortion":3 },
    "46640019":{"width":640,"height":512,"fov":40.7, "fnumber": 1.01, "focallength":19.0, "fx":1133, "distortion":3 },
    "46640025":{"width":640,"height":512,"fov":31.3, "fnumber": 1.04, "focallength":25.0, "fx":1500, "distortion":2 },
    "46640W35":{"width":640,"height":512,"fov":31.3, "fnumber": 1.09, "focallength":35.0, "fx":1500, "distortion":2 },
    "46640035":{"width":640,"height":512,"fov":23.1, "fnumber": 1.0, "focallength":35.0, "fx":2025, "distortion":2 },
    "46640050":{"width":640,"height":512,"fov":15.7, "fnumber": 1.0, "focallength":50.0, "fx":3000, "distortion":1 },
    "46640060":{"width":640,"height":512,"fov":10.3, "fnumber": 1.01, "focallength":60.0, "fx":4583, "distortion":2 },
    "46640100":{"width":640,"height":512,"fov":7.7, "fnumber": 1.05, "focallength":100.0, "fx":6067, "distortion":1 },
    
    "46336005":{"width":336,"height":256,"fov":124.8, "fnumber": 1.0, "focallength":2.3, "fx": 192, "distortion":43},
    "46336007":{"width":336,"height":256,"fov":65.9, "fnumber": 1.0, "focallength":4.3, "fx":358, "distortion":12},
    "46336009":{"width":336,"height":256,"fov":43.6, "fnumber": 1.02, "focallength":6.3, "fx":525, "distortion":1 },
    "46336013":{"width":336,"height":256,"fov":30.6, "fnumber": 1.01, "focallength":9.1, "fx":758, "distortion":1 },
    "46336019":{"width":336,"height":256,"fov":20.4, "fnumber": 1.04, "focallength":13.8, "fx":1150, "distortion":3 },
    "46336025":{"width":336,"height":256,"fov":15.7, "fnumber": 1.0, "focallength":18.0, "fx":1500, "distortion":1 },
    "46336W35":{"width":336,"height":256,"fov":11.6, "fnumber": 1.0, "focallength":24.3, "fx":2025, "distortion":2 },
    "46336035":{"width":336,"height":256,"fov":7.9, "fnumber": 1.01, "focallength":36.0, "fx":3000, "distortion":1 },
    "46336050":{"width":336,"height":256,"fov":5.2, "fnumber": 1.0, "focallength":55.0, "fx":4583, "distortion":1 },
    "46336060":{"width":336,"height":256,"fov":5.2, "fnumber": 1.0, "focallength":55.0, "fx":4583, "distortion":1 },
    "46336100":{"width":336,"height":256,"fov":5.2, "fnumber": 1.0, "focallength":55.0, "fx":4583, "distortion":1 },
    }
        
class ImageIntel(ImageBaseClass):
    bitdepth = 8
    maker = "Intel"
    
    @classmethod
    def is_registrar_for(cls, params):
        maker = params["ifd0"].get(piexif.ImageIFD.Make,"Unknown")
        filepath = params["filepath"]
        base, ext = os.path.splitext(filepath)
        return ext.lower() in ['.ara',".raw"]
    
    def __init__(self, filepath=None,ifd=None,rawdata= b'',img=None,onlyheader=False):
        super().__init__(filepath,ifd,rawdata,img)
        self.images = []
        self.read_header(rawdata)
        if not onlyheader:
            self.rawimage = self.read_body(rawdata)
            self.images.append(self.rawimage)
        self.load_header()
        self.set_main_params()
    
    def load_header(self):
        #self.header["camera"][0]["FieldOfView"] = self.xmp.get('camera:fieldofview')
        #self.header["camera"][0]["FocalLengthPixel"] = self.xmp.get("camera:focallengthpixel")
        ascver = self.params["asctec"].get("version")
        coordinatetransform = -1 if ascver < 10 else 1
        self.header["camera"][0]["Pitch"] = coordinatetransform * self.params["falcon"].get("cam_angle_pitch")/100.0 
        self.header["camera"][0]["Roll"] =  self.params["falcon"].get("cam_angle_roll")/100.0
        self.header["camera"][0]["Yaw"] =  self.params["falcon"].get("angle_yaw")/100.0
        self.header["camera"][0]["FocalPlaneXResolution"] =  self.params["bitmap"].get("width",640)
        self.header["camera"][0]["FocalPlaneYResolution"] =  self.params["bitmap"].get("height",512)
        self.header["camera"][0]["BitDepth"] = self.params["bitmap"].get("bitperpixel",16)
        self.header["camera"][0]["Type"] = self.imagetype(0)
        
        self.header["camera"][0]["Band"] = "LWIR"
        self.header["camera"][0]["CentralWavelength"] = "10000"
        self.header["camera"][0]["WavelengthFwhm"] =  "4500"
        self.header["camera"][0]["CoreTemp"] = self.params["camera"].get("sensortemperature")/10.0
        self.header["camera"][0]["ImageNumber"] = self.params["asctec"].get("trigger_counter",None)
        
        if 4096  < self.params["radiometric"].get("emissivity") <= 8192:
            self.header["camera"][0]["Emissivity"] = self.params["radiometric"].get("emissivity")/8192
            self.header["camera"][0]["PlanckR"] = self.params["radiometric"].get("R")
            self.header["camera"][0]["PlanckB"] = self.params["radiometric"].get("B1000")/1000
            self.header["camera"][0]["PlanckF"] = self.params["radiometric"].get("F1000")/1000
            self.header["camera"][0]["PlanckO"] = self.params["radiometric"].get("O1000")/1000
            self.header["camera"][0]["GainMode"] = self.params["radiometric"].get("gain_mode")
            self.header["camera"][0]["TLinear"] = bool(self.params["radiometric"].get("tlinear"))
            self.header["camera"][0]["TLinearResolution"] = "High" if self.params["radiometric"].get("tlinear_resolution") else "Low"
            self.header["camera"][0]["LensNumber"] = self.params["radiometric"].get("lens_number")
            self.header["camera"][0]["AtmosphericTemperature"] =  self.params["radiometric"].get("temp_atm_x100")/100
            self.header["camera"][0]["AtmosphericTransmission"] =  self.params["radiometric"].get("tau_atm")/8192
            self.header["camera"][0]["IRWindowTransmission"] =  self.params["radiometric"].get("transmission_win")/8192
            self.header["camera"][0]["IRWindowReflection"] =  self.params["radiometric"].get("refl_win")
            self.header["camera"][0]["IRWindowTemperature"] =  self.params["radiometric"].get("temp_win_x100")/100
            self.header["camera"][0]["BackgroundTemperature"] =  self.params["radiometric"].get("temp_background_x100")/100
            self.header["camera"][0]["ReflectionTemperature"] =  self.params["radiometric"].get("temp_refl_x100")/100
            
            self.header["camera"][0]["_FbyX"] =  self.params["radiometric"].get("FbyX")
            self.header["camera"][0]["_Transmission"] =  self.params["radiometric"].get("transmission")
        
        self.header["general"]["Erkennung"] = self.params["dlr"].get("erkennung")
            
        if self.params["dlr"]["erkennung"]== "DLR":
            self.header["camera"][0]["PitchOffset"] =  self.params["dlr"].get("cam_pitch_offset")
            self.header["camera"][0]["RollOffset"] =  self.params["dlr"].get("cam_roll_offset")
            self.header["camera"][0]["YawOffset"] =  self.params["dlr"].get("cam_yaw_offset")
            self.header["camera"][0]["BSCalibTimestamp"] = self.params["dlr"].get("boresight_calib_timestamp")
            self.header["position"]["AccX"] = self.params["dlr"].get("gps_acc_x")
            self.header["position"]["AccY"] = self.params["dlr"].get("gps_acc_y")
            self.header["general"]["ChangedFlags"] = self.params["dlr"].get("changed_flags")
            self.header["general"]["ErrorFlags"] = self.params["dlr"].get("error_flags")
            self.header["general"]["Flags"] = self.params["dlr"].get("flags")
            self.header["camera"][0]["PlanckR"] = self.params["dlr"].get("radiometric_R")
            self.header["camera"][0]["PlanckB"] = self.params["dlr"].get("radiometric_B")
            self.header["camera"][0]["PlanckF"] = self.params["dlr"].get("radiometric_F")
            self.header["camera"][0]["RadCalibTimestamp"] = self.params["dlr"].get("radiometric_calib_timestamp")
            self.header["camera"][0]["fx"] = self.params["dlr"].get("geometric_fx")
            self.header["camera"][0]["fy"] = self.params["dlr"].get("geometric_fy")
            self.header["camera"][0]["cx"] = self.params["dlr"].get("geometric_cx")
            self.header["camera"][0]["cy"] = self.params["dlr"].get("geometric_cy")
            self.header["camera"][0]["skew"] = self.params["dlr"].get("geometric_skew")
            self.header["camera"][0]["k1"] = self.params["dlr"].get("geometric_k1")
            self.header["camera"][0]["k2"] = self.params["dlr"].get("geometric_k2")
            self.header["camera"][0]["k3"] = self.params["dlr"].get("geometric_k3")
            self.header["camera"][0]["p1"] = self.params["dlr"].get("geometric_p1")
            self.header["camera"][0]["p2"] = self.params["dlr"].get("geometric_p2")
            self.header["camera"][0]["GeomCalibTimestamp"] = self.params["dlr"].get("geometric_calib_timestamp")
            self.header["camera"][0]["pixelshift_x"] = self.params["dlr"].get("geometric_pixelshift_x")
            self.header["camera"][0]["pixelshift_y"] = self.params["dlr"].get("geometric_pixelshift_y")
            self.header["camera"][0]["rawSize"] = self.params["dlr"].get("raw_size")
            self.header["camera"][0]["imgSize"] = self.params["dlr"].get("img_size")
            self.header["general"]["DLRVersion"] = str(self.params["dlr"].get("version_major"))+"."+str(self.params["dlr"].get("version_minor"))
        
        self.header["image"]["raw_thermal"] = {}
        self.header["image"]["raw_thermal"]["Width"] = self.params["bitmap"].get("width",640)
        self.header["image"]["raw_thermal"]["Height"] = self.params["bitmap"].get("height",512)
        self.header["image"]["raw_thermal"]["BitDepth"] = self.params["bitmap"].get("bitperpixel",16)
        self.header["image"]["raw_thermal"]["Channels"] = 1
        self.header["image"]["raw_thermal"]["Orientation"] = 0
        self.header["image"]["raw_thermal"]["Index"] = len(self.images)-1
        self.header["image"]["raw_thermal"]["Camera"] = 0
        
        self.header["time"]["GPSTimeStamp"] = UTCFromGps(self.params["falcon"].get("gps_week"),self.params["falcon"].get("gps_time_ms")) 
        self.header["time"]["SystemBootTime"] = self.params["falcon"]["time_ms"]/1000
        self.header["time"]["FileCreated"] = self.header["file"]["Created"]
        self.header["time"]["FileModified"] = self.header["file"]["Modified"]
        
        self.header["position"]["Latitude"] = self.params["falcon"].get('gps_lat')/10**7 
        self.header["position"]["Longitude"] = self.params["falcon"].get('gps_long')/10**7 
        self.header["position"]["RelAltitude"] = self.params["falcon"].get('baro_height')/10**3
        self.header["position"]["FlightPitch"] = self.params["falcon"].get('angle_pitch')/10**2
        self.header["position"]["FlightRoll"] = self.params["falcon"].get('angle_roll')/10**2
        self.header["position"]["FlightYaw"] =  self.params["falcon"].get('angle_yaw')/10**2
        self.header["position"]["HorAccuracy"] = self.params["falcon"].get('gps_hor_accuracy')/10**3
        self.header["position"]["VerAccuracy"] = self.params["falcon"].get('gps_vert_accuracy')/10**3
        self.header["position"]["SpeedAccuracy"] = self.params["falcon"].get('gps_speed_accuracy')/10**3
        self.header["position"]["SpeedX"] = self.params["falcon"].get('gps_speed_x')/10**3
        self.header["position"]["SpeedY"] = self.params["falcon"].get('gps_speed_y')/10**3
        
        self.header["position"]["Home_Latitude"] = self.params["startup_gps"].get('lat')/10**7 
        self.header["position"]["Home_Longitude"] = self.params["startup_gps"].get('long')/10**7 
        self.header["position"]["Home_Altitude"] = self.params["startup_gps"].get('height')/10**3 
        self.header["position"]["Home_HorAccuracy"] = self.params["startup_gps"].get('hor_accuracy')/10**3
        self.header["position"]["Home_VerAccuracy"] = self.params["startup_gps"].get('vert_accuracy')/10**3
        self.header["position"]["Home_SpeedAccuracy"] = self.params["startup_gps"].get('speed_accuracy')/10**3
        self.header["position"]["Home_SpeedX"] = self.params["startup_gps"].get('speed_x')/10**3
        self.header["position"]["Home_SpeedY"] = self.params["startup_gps"].get('speed_y')/10**3
        
        self.header["general"]["Model"] =  "Falcon 8/8+ with Tau/Tau2"
        self.header["general"]["Make"] =  "Intel"
        self.header["general"]["PartNumber"] =  self.params["camera"].get('partnum').split(b'\x00', 1)[0]
        self.header["general"]["SerialNumber"] = self.params["camera"].get('sernum')
        self.header["general"]["SensorSerialNumber"] = self.params["camera"].get('sernum_sensor')
        self.header["general"]["CameraVersion"] = self.params["camera"].get('version')
        self.header["general"]["CameraFirmwareVersion"] = self.params["camera"].get('fw_version')
        self.header["general"]["CameraSoftware"] = str(self.params["firmware_version"].get('major'))+"."+str(self.params["firmware_version"].get('minor'))+"."+str(self.params["firmware_version"].get('build_count'))
        self.header["general"]["FirmwareTimestamp"] = datetime.fromtimestamp(self.params["firmware_version"].get('timestamp')).isoformat(" ")
        self.header["general"]["FirmwareSvnRevision"] = self.params["firmware_version"].get('svn_revision').split(b'\x00', 1)[0]
        
    def image_header(self,index):
        for k,v in self.header["image"].items():
            if index is v.get("Index"):
                return v
    
    def set_main_params(self,imageid=0):
        current_shape = self.images[imageid].shape
        image_header = self.image_header(imageid)
        cur_camera = self.header["camera"][image_header["Camera"]]
        self.header["main"]["Make"]=self.header["general"].get("Make")
        self.header["main"]["Model"]=self.header["general"].get("Model")
        self.header["main"]["Width"]=current_shape[1]
        self.header["main"]["Height"]=current_shape[0]
        self.header["main"]["DateTime"]=self.header["time"]["GPSTimeStamp"]
        self.header["main"]["Latitude"]=self.header["position"]["Latitude"]
        self.header["main"]["Longitude"]=self.header["position"]["Longitude"]
        self.header["main"]["RelAltitude"]=self.header["position"]["RelAltitude"]
        self.header["main"]["Pitch"]=cur_camera["Pitch"]
        self.header["main"]["Roll"]=cur_camera["Roll"]
        self.header["main"]["Yaw"]=cur_camera["Yaw"]
        self.header["main"]["CurrentCamera"]=image_header["Camera"]
        self.header["main"]["CurrentImage"]=imageid
            
            
    def read_body(self, bytearr):
        img = np.frombuffer(bytearr[512:], dtype="<u2",count=self.params['bitmap']['width']*self.params['bitmap']['height']) 
        img = np.reshape(img,(self.params['bitmap']['height'],self.params['bitmap']['width']))
        return img
        
    def read_header(self, rawdata, size=512):
        try:
            rawheader = rawdata[0:size]
            self.fmt = '<HIIIIIIHHIIIIII HHHHHHII IIIIHII32s IHIiiiHHHHHhhHhhh HHII32s iiiHHHHH ??IiiiH HHHHH HHHHHHHH 54shhhIhh BHHBHHBHHBHHBHHBHHBHHBHHBHHBHH HHHIhIHHHHhhhhhhI03sHBBhhII47s'
            h = struct.Struct(self.fmt).unpack_from(rawheader)
            self.headerarray = list(h)
            self.params = {
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
                "radiometric":{
                    "tlinear":h[61],"tlinear_resolution":h[62],"R":h[63],
                    "B1000":h[64],"F1000":h[65],"O1000":h[66],
                    "gain_mode":h[67],"reserved1":h[68],"lens_number":h[69],
                    "FbyX":h[70],"transmission":h[71],"reserved2":h[72],
                    "emissivity":h[73],"temp_background_x100":h[74],
                    "transmission_win":h[75],"temp_win_x100":h[76],
                    "tau_atm":h[77],"temp_atm_x100":h[78],"refl_win":h[79],"temp_refl_x100":h[80],
                    },                
                "dlr":{"platzhalter":h[81],"cam_pitch_offset":h[82],"cam_roll_offset":h[83],
                    "cam_yaw_offset":h[84],"boresight_calib_timestamp":h[85],"gps_acc_x":h[86],"gps_acc_y":h[87],
                    "pois":[{"id":h[i],"x":h[i+1],"y":h[i+2]} for i in range(88,115,3) if h[i] != 0],

                    "changed_flags":h[118],"error_flags":h[119],"radiometric_B":h[120],"radiometric_R":h[121],
                    "radiometric_F":h[122],"radiometric_calib_timestamp":h[123],"geometric_fx":h[124],
                    "geometric_fy":h[125],"geometric_cx":h[126],"geometric_cy":h[127],"geometric_skew":h[128],
                    "geometric_k1":h[129],"geometric_k2":h[130],"geometric_k3":h[131],"geometric_p1":h[132],
                    "geometric_p2":h[133],"geometric_calib_timestamp":h[134],"erkennung":h[135],"flags":h[136],"version_major":h[137],"version_minor":h[138],"geometric_pixelshift_x":h[139],"geometric_pixelshift_y":h[140],"raw_size":h[141],"img_size":h[142],"platzhalter2":h[143]}
                }
            
        except:
            logger.error("read header failed", exc_info=True)