from .base import *

DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 512

class ImageDJI(ImageBaseClass,jfif.JFIF):
    bitdepth = 8
    maker = "DJI"
    endian = "<"
    
    @classmethod
    def is_registrar_for(cls, params):
        maker = params["ifd0"].get(piexif.ImageIFD.Make,"Unknown")
        filepath = params["filepath"]
        return maker in [b'DJI',b'Hasselblad']
   
    def __init__(self, filepath=None,ifd=None,rawdata= b'',img=None,onlyheader=False):
        super().__init__(filepath,ifd,rawdata,img)
        self.images = []
        self.rawimage = np.array([])
        self.rawdata = rawdata
        self.segments = self.main_segments(rawdata)
        self.load_exif()
        self.load_xmp(rawdata)
        self.load_makernote()
        self.load_header()
        self.params = {"exif":self.exif,"xmp":self.xmp,"makernote":self.makernote}
        if not onlyheader:
            self.mainimage = np.array(PILImage.open(BytesIO(rawdata)))
            self.images.append(self.mainimage)
            nested_set(self.header, ["image","main","Index"],len(self.images)-1)
            self.load_rawimage()
        self.load_thumbnail()
        self.set_main_params(0)
    
    def get_date(self,src):
        if src == None:
            src = "1970:01:01 00:00:00"
        try:
            dt = datetime.strptime(src, "%Y:%m:%d %H:%M:%S").astimezone().isoformat(" ")
        except ValueError:
            dt = datetime.strptime(src, "%Y-%m-%d %H:%M:%S").astimezone().isoformat(" ")
            
        return dt
        
        
    def alt(self):
        alt = self.exif["GPS"].get("GPSAltitude")
        altref = self.exif["GPS"].get("GPSAltitudeRef")
        if altref == 1:
            return - alt
        else:
            return alt
    
            
    def load_header(self):
        self.header["camera"][0]["Pitch"] = evaldiv(self.xmp.get("@drone-dji:gimbalpitchdegree","0/1"))
        self.header["camera"][0]["Roll"] = evaldiv(self.xmp.get("@drone-dji:gimbalrolldegree","0/1"))
        self.header["camera"][0]["Yaw"] = evaldiv(self.xmp.get("@drone-dji:gimbalyawdegree","0/1"))
        self.header["camera"][0]["GimbalReverse"] = boolstr(self.xmp.get("@drone-dji:gimbalreverse",-1))
        self.header["camera"][0]["CamReverse"] = boolstr(self.xmp.get("@drone-dji:camreverse",-1))
        self.header["camera"][0]["GimbalDegree(Y,P,R)"] = bytes2tuple(self.makernote.get("GimbalDegree(Y,P,R)"))
        
        self.header["camera"][0]["Type"] = self.imagetype("0")
        if self.header["camera"][0]["Type"]=="vis":
            self.header["camera"][0]["FocalLength"] =       self.exif["Exif"].get("FocalLength")
            self.header["camera"][0]["FNumber"] =           self.exif["Exif"].get("FNumber")
            self.header["camera"][0]["ExposureTime"] =      self.exif["Exif"].get("ExposureTime")
            self.header["camera"][0]["ExposureProgram"]=    ExposureProgram[self.exif["Exif"].get("ExposureProgram",0)]
            self.header["camera"][0]["ExposureMode"] =      self.exif["Exif"].get("ExposureMode")
            #self.header["camera"][0]["IsoSpeed"] =          self.exif["Exif"].get("IsoSpeed")
            #self.header["camera"][0]["IsoSpeedRatings"] =   self.exif["Exif"].get("IsoSpeedRatings")
            #self.header["camera"][0]["ExposureBiasValue"]=  self.exif["Exif"].get("ExposureBiasValue")
            #self.header["camera"][0]["ShutterSpeedValue"] = self.exif["Exif"].get("ShutterSpeedValue")
            #self.header["camera"][0]["SensingMode"] =       self.exif["Exif"].get("SensingMode")
            #self.header["camera"][0]["ApertureValue"] =     self.exif["Exif"].get("ApertureValue")
            self.header["camera"][0]["MeteringMode"] =      self.exif["Exif"].get("MeteringMode")
            self.header["camera"][0]["MaxApertureValue"] =  self.exif["Exif"].get("MaxApertureValue")
            self.header["camera"][0]["LightSource"] =       self.exif["Exif"].get("LightSource")
            self.header["camera"][0]["Flash"] =             self.exif["Exif"].get("Flash")
            self.header["camera"][0]["WhiteBalance"] =      self.exif["Exif"].get("WhiteBalance")
            self.header["camera"][0]["GainControl"] =       self.exif["Exif"].get("GainControl")
            self.header["camera"][0]["Contrast"] =          self.exif["Exif"].get("Contrast")
            self.header["camera"][0]["Saturation"] =        self.exif["Exif"].get("Saturation")
            self.header["camera"][0]["Sharpness"] =         self.exif["Exif"].get("Sharpness")
            self.header["camera"][0]["FocalLengthIn35mmFilm"] = self.exif["Exif"].get("FocalLengthIn35mmFilm")
            self.header["camera"][0]["DigitalZoomRatio"] =  self.exif["Exif"].get("DigitalZoomRatio")
            self.header["camera"][0]["LensSpecification"] = self.exif["Exif"].get("LensSpecification")
            
            
        self.header["image"]["main"] = {}
        self.header["image"]["main"]["Width"] = self.ifd["Exif"].get(piexif.ExifIFD.PixelXDimension,-1)
        self.header["image"]["main"]["Height"] = self.ifd["Exif"].get(piexif.ExifIFD.PixelYDimension,-1)
        
        if "0th" in self.exif:
            self.header["camera"][0]["FocalPlaneXResolution"] =  self.exif["0th"].get("ImageWidth",0)
            self.header["camera"][0]["FocalPlaneYResolution"] =  self.exif["0th"].get("ImageLength",0)
            self.header["image"]["main"]["BitDepth"] = self.ifd["0th"].get(piexif.ImageIFD.BitsPerSample,-1)
            self.header["image"]["main"]["Channels"] = self.ifd["0th"].get(piexif.ImageIFD.SamplesPerPixel,-1)
            self.header["image"]["main"]["Orientation"] = self.ifd["0th"].get(piexif.ImageIFD.Orientation,-1)
            self.header["image"]["main"]["Resolution"] = resolution(self.ifd["0th"])
            self.header["image"]["main"]["ChromaPositioning"] = chroma(self.exif["0th"].get("YCbCrPositioning"))
        
        self.header["image"]["main"]["Camera"] = 0 
            
        self.header["time"]["DateTimeOriginal"]= self.get_date(self.exif["Exif"].get("DateTimeOriginal"))
        dtd = self.exif["Exif"].get("DateTimeDigitized")
        if dtd:
            self.header["time"]["DateTimeDigitized"] = self.get_date(dtd)
        self.header["time"]["DateTime"] = self.get_date(self.exif["0th"].get("DateTime"))
        self.header["time"]["FileCreated"] = self.header["file"]["Created"]
        self.header["time"]["FileModified"] = self.header["file"]["Modified"]
        
        self.header["position"]["Latitude"] = dms2dd(*self.exif["GPS"].get("GPSLatitude",(0,0,0)),self.exif["GPS"].get("GPSLatitudeRef"))
        self.header["position"]["Longitude"] = dms2dd(*self.exif["GPS"].get("GPSLongitude",(0,0,0)),self.exif["GPS"].get("GPSLongitudeRef"))
        self.header["position"]["RelAltitude"] = evaldiv(self.xmp.get("@drone-dji:relativealtitude","0/1"))
        self.header["position"]["Altitude"] = self.alt()
        self.header["position"]["FlightPitch"] = float(self.xmp.get("@drone-dji:flightpitchdegree",0))
        self.header["position"]["FlightRoll"] = float(self.xmp.get("@drone-dji:flightrolldegree",0))
        self.header["position"]["FlightYaw"] = float(self.xmp.get("@drone-dji:flightyawdegree",0))
        self.header["position"]["FlightDegree(Y,P,R)"] = bytes2tuple(self.makernote.get("FlightDegree(Y,P,R)"))
        
        self.header["file"]["MimeType"] = self.xmp.get("@dc:format")
        
        self.header["general"]["Software"] = self.exif["0th"].get("Software")
        self.header["general"]["SensorId"] = self.makernote.get("sensor_id",b"").decode("utf-8")
        self.header["general"]["Make"] = self.exif["0th"].get("Make")
        self.header["general"]["Model"] = self.exif["0th"].get("Model")
        
        
    def load_thumbnail(self):
        if self.thumbnail is not None:
            self.header["image"]["thumbnail"] = {}
            self.header["image"]["thumbnail"]["Width"] = self.ifd["1st"].get(piexif.ImageIFD.ImageWidth,-1)
            self.header["image"]["thumbnail"]["Height"] = self.ifd["1st"].get(piexif.ImageIFD.ImageLength,-1)
            self.header["image"]["thumbnail"]["Resolution"] = resolution(self.ifd["1st"])
            self.header["image"]["thumbnail"]["Compression"] = jfif.ExifCompression[self.ifd["1st"].get(piexif.ImageIFD.Compression,0)]
            self.header["image"]["thumbnail"]["Camera"] = 0
            self.images.append(self.thumbnail)
            self.header["image"]["thumbnail"]["Index"] = len(self.images)-1

    def load_makernote(self):
        soup = self.exif["Exif"].get("MakerNote",b'[:]')
        self.makernote = {}
        mnlist = soup[1:-1].split(b"][")
        for line in mnlist:
            splt = line.split(b":")
            if len(splt)>1:
                self.makernote[splt[0].decode("utf-8")] = splt[1].strip(b"\x00")#.decode("utf-8")
        self.exif["Exif"]["MakerNote"] = self.makernote
    
    def image_header(self,index):
        for k,v in self.header["image"].items():
            if index is v.get("Index"):
                return v
    
    def set_main_params(self,imageid=0):
        current_shape = self.images[imageid].shape
        image_header = self.image_header(imageid)
        cur_camera = self.header["camera"][image_header["Camera"]]
        self.header["main"]["Make"]=self.exif["0th"].get("Make")
        self.header["main"]["Model"]=self.exif["0th"].get("Model")
        self.header["main"]["Width"]=current_shape[1]
        self.header["main"]["Height"]=current_shape[0]
        self.header["main"]["DateTime"]=self.header["time"]["DateTimeOriginal"]
        self.header["main"]["Latitude"]=self.header["position"]["Latitude"]
        self.header["main"]["Longitude"]=self.header["position"]["Longitude"]
        self.header["main"]["RelAltitude"]=self.header["position"]["RelAltitude"]
        self.header["main"]["Pitch"]=cur_camera["Pitch"]
        self.header["main"]["Roll"]=cur_camera["Roll"]
        self.header["main"]["Yaw"]=cur_camera["Yaw"]
        self.header["main"]["CurrentCamera"]=image_header["Camera"]
        self.header["main"]["CurrentImage"]=imageid
            
    def load_rawimage(self):
        app3, app4 = [], []
        for s in self.segments:
            if s[1] == "APP3": app3.append(self.rawdata[s[0]+4:s[2]])
            elif s[1] == "APP4": app4.append(self.rawdata[s[0]+4:s[2]])
        raw_app3 = b"".join(app3)        
        raw_app4 = b"".join(app4)        
        
        cnt = self.ifd["Exif"].get(piexif.ExifIFD.PixelXDimension,DEFAULT_WIDTH)*self.ifd["Exif"].get(piexif.ExifIFD.PixelYDimension,DEFAULT_HEIGHT)
        if len(raw_app3) == cnt*2:
            raw = raw_app3
        elif len(raw_app4) == cnt*2:
            raw = raw_app4
        else:
            raw = b''
        if len(raw) == cnt*2:    
            self.rawimage = np.frombuffer(raw, dtype="<u2",count=cnt) 
            self.rawimage = np.reshape(self.rawimage,(self.header["image"]["main"]["Height"],self.header["image"]["main"]["Width"]))
            self.images.append(self.rawimage)
            self.header["image"]["raw_thermal"] = {}
            self.header["image"]["raw_thermal"]["Width"] = self.ifd["Exif"].get(piexif.ExifIFD.PixelXDimension,-1)
            self.header["image"]["raw_thermal"]["Height"] = self.ifd["Exif"].get(piexif.ExifIFD.PixelYDimension,-1)
            self.header["image"]["raw_thermal"]["BitDepth"] = 16
            self.header["image"]["raw_thermal"]["Channels"] = 1
            self.header["image"]["raw_thermal"]["Orientation"] = self.ifd["0th"].get(piexif.ImageIFD.Orientation,-1)
            self.header["image"]["raw_thermal"]["Index"] = len(self.images)-1
            self.header["image"]["raw_thermal"]["Camera"] = 0
            
