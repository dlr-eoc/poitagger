from .base import *


class ImageFlir(ImageBaseClass,jfif.JFIF):
    bitdepth = 8
    maker = "Flir"
    endian = ">"
    
    @classmethod
    def is_registrar_for(cls, params):
        maker = params["ifd0"].get(piexif.ImageIFD.Make,"Unknown")
        model = params["ifd0"].get(piexif.ImageIFD.Model,None)
        imagenr = params["ifd0"].get(piexif.ImageIFD.ImageNumber,None)
        filepath = params["filepath"]
        if maker in [b'FLIR',b'FLIR Systems AB'] and imagenr == None and not model == b'Boson': 
            return True
        return False
        
    def __init__(self, filepath=None,ifd=None,rawdata= b'',img=None,onlyheader=False):
        super().__init__(filepath,ifd,rawdata,img)
        self.images = []
        self.rawimage = np.array([])
        self.segments = self.main_segments(rawdata)
        self.load_fff()
        self.load_exif()
        self.load_xmp(rawdata)
        self.load_header()
        self.params = {"exif":self.exif,"xmp":self.xmp,"fff":self.fff}
        if not onlyheader:
            self.mainimage = np.array(PILImage.open(BytesIO(rawdata)))
            self.images.append(self.mainimage)
            idx = len(self.images)-1
            nested_set(self.header, ["image","main","Index"],idx)
            self.header["image"]["main"]["BitDepth"] = self.images[idx].itemsize*8
            self.header["image"]["main"]["Channels"] = self.images[idx].shape[2]
        self.load_thumbnail()
        self.set_main_params(0)
        
    def image_header(self,index):
        for k,v in self.header["image"].items():
            if index is v.get("Index"):
                return v
                
    def set_main_params(self,imageid=0):
        current_shape = self.images[imageid].shape
        image_header = self.image_header(imageid)
      #  print(image_header)
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
    
    def latlon(self,key,refkey, defaultref=b"N",ref=[b"S",b"South"],defaultval=((0,1),(0,1),(0,1))):
        ll = self.ifd["GPS"].get(key,defaultval)
        llref = self.ifd["GPS"].get(refkey,defaultref) 
        if llref in ref :
            #dms2dd(ll[0],ll[1],ll[2],llref)
            return -rational2float(ll[0])
        else:
            return rational2float(ll[0])
        
    def alt(self):
        alt = self.ifd["GPS"].get(piexif.GPSIFD.GPSAltitude,(0,1))
        altref = self.ifd["GPS"].get(piexif.GPSIFD.GPSAltitudeRef,0) 
        if altref == 1:
            return -rational2float(alt)
        else:
            return rational2float(alt)
    
    def anyorientation(self):
        backup = self.exif.get("1st",{}).get("Orientation",-1)
        return self.exif.get("0th",{}).get("Orientation",backup)
        
    def combine_flir_segments(self):
        flirdata = []
        start = 10
        for s in self.segments:
            if not s[1]=="APP1": continue
            if s[2]-s[0]<6: continue
            if not self.rawdata[s[0]+4:s[0]+8] == b"FLIR": continue    
            length = 256 * self.rawdata[s[0]+2] + self.rawdata[s[0]+3]
            if start<length:
                flirdata.append(self.rawdata[s[0]+2+start:s[0]+2+length])
        return b"".join(flirdata)
        
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
        bitdepth = geom["pixelSize"]
        
        return img, bitdepth
        
    def load_fff(self):
        fffchunk = self.combine_flir_segments()
        ffh = {}
        if len(fffchunk)<64:  return
        for i in FLIRFILEHEAD:
            val = struct.unpack_from(">"+i[2],fffchunk[0:64],i[0])
            #if "s" in i[2]:
            #    val = val[0].strip(b"\x00")
            name = i[1]
            ffh[name]=val[0]
        
        indexes = ffh["Number of indexes"]
        FFI = []
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
        self.fff = self.decode_struct(fffchunk[basicstart:basicend],FFF,"<",True)
        if not self.onlyheader:
            self.rawimage,self.bitdepth = self.get_raw(fffchunk[rawstart:rawend])
            
            self.images.append(self.rawimage)
            nested_set(self.header, ["image","raw_thermal","Index"],len(self.images)-1)
            self.header["image"]["raw_thermal"]["Camera"] = 0 
            self.header["image"]["raw_thermal"]["BitDepth"] = self.bitdepth*8
            shape = self.rawimage.shape
            channels = 1 if len(shape)<3 else shape[2]
            self.header["image"]["raw_thermal"]["Channels"] = channels
            self.header["image"]["raw_thermal"]["Width"] = shape[1]
            self.header["image"]["raw_thermal"]["Height"] = shape[0]
            
        else:
            self.bitdepth = struct.Struct(">"+i[2]).unpack_from(fffchunk[rawstart:rawstart+2],0)
        
         
    def load_thumbnail(self):
        if self.thumbnail is not None:
            self.header["image"]["thumbnail"] = {}
            self.header["image"]["thumbnail"]["Width"] = self.ifd["1st"].get(piexif.ImageIFD.ImageWidth,-1)
            self.header["image"]["thumbnail"]["Height"] = self.ifd["1st"].get(piexif.ImageIFD.ImageLength,-1)
            self.header["image"]["thumbnail"]["Resolution"] = resolution(self.ifd["1st"])
            self.header["image"]["thumbnail"]["Compression"] = jfif.ExifCompression[self.ifd["1st"].get(piexif.ImageIFD.Compression,0)]
            self.header["image"]["thumbnail"]["Orientation"] = self.exif["1st"].get("Orientation",-1)
            self.header["image"]["thumbnail"]["Camera"] = 0
            self.images.append(self.thumbnail)
            self.header["image"]["thumbnail"]["Index"] = len(self.images)-1

    def load_header(self):
        self.header["camera"][0]["FieldOfView"] = self.fff.get('FieldOfView',[-1])
        self.header["camera"][0]["FrameRate"] = self.fff.get('FrameRate',[-1])
        self.header["camera"][0]["Pitch"] =  evaldiv(self.xmp.get("camera:pitch","0/1"))
        self.header["camera"][0]["Roll"] =  evaldiv(self.xmp.get("camera:roll","0/1"))
        self.header["camera"][0]["Yaw"] =  evaldiv(self.xmp.get("camera:yaw","0/1"))
        self.header["camera"][0]["FocalPlaneXResolution"] =  self.fff.get("Raw Thermal Image Width")
        self.header["camera"][0]["FocalPlaneYResolution"] =  self.fff.get("Raw Thermal Image Height")
        self.header["camera"][0]["Type"] = self.imagetype(0)
        
        if self.header["camera"][0]["Type"]=="thermal":    
            self.header["camera"][0]["Band"] =              self.xmp.get("camera:bandname")
            self.header["camera"][0]["CentralWavelength"] = self.xmp.get("camera:centralwavelength")
            self.header["camera"][0]["WavelengthFwhm"] =  self.xmp.get("camera:wavelengthfwhm")
            self.header["camera"][0]["CoreTemp"] = self.fff.get("Coretemp")
            self.header["camera"][0]["Emissivity"] = self.fff.get("Emissivity")
            self.header["camera"][0]["PlanckR1"] = self.fff.get("PlanckR1")
            self.header["camera"][0]["PlanckB"] = self.fff.get("PlanckB")
            self.header["camera"][0]["PlanckF"] = self.fff.get("PlanckF")
            self.header["camera"][0]["PlanckR2"] = self.fff.get("PlanckR2")
            self.header["camera"][0]["PlanckO"] = self.fff.get("PlanckO")
            self.header["camera"][0]["FocusDistance"] = self.fff.get("FocusDistance")
            self.header["camera"][0]["LensTemp"] = self.fff.get("LensTemp")
            self.header["camera"][0]["RawValueMedian"] = self.fff.get("RawValueMedian")
            self.header["camera"][0]["RawValueRange"] = self.fff.get("RawValueRange")
            self.header["camera"][0]["FocusStepCount"] = self.fff.get("FocusStepCount")
            
            
            self.header["camera"][0]["TLinearGain"] = self.xmp.get("camera:tlineargain")
            self.header["camera"][0]["IsNormalized"] = self.xmp.get("camera:isnormalized")
            self.header["camera"][0]["RelativeHumidity"] = self.fff.get("RelativeHumidity")
            self.header["camera"][0]["ObjectDistance"] = self.fff.get("ObjectDistance")
            self.header["camera"][0]["ReflectedApparentTemperature"] = self.fff.get("ReflectedApparentTemperature")
            self.header["camera"][0]["AtmosphericTemperature"] = self.fff.get("AtmosphericTemperature")
            self.header["camera"][0]["IRWindowTemperature"] = self.fff.get("IRWindowTemperature")
            self.header["camera"][0]["IRWindowTransmission"] = self.fff.get("IRWindowTransmission")
           # self.header["camera"][0][""] = self.fff.get("")
        
        self.header["image"]["main"] = {}
        self.header["image"]["main"]["Width"] = self.ifd["Exif"].get(piexif.ExifIFD.PixelXDimension,-1)
        self.header["image"]["main"]["Height"] = self.ifd["Exif"].get(piexif.ExifIFD.PixelYDimension,-1)
        self.header["image"]["main"]["BitDepth"] = self.ifd["0th"].get(piexif.ImageIFD.BitsPerSample,-1)
        self.header["image"]["main"]["Channels"] = self.ifd["0th"].get(piexif.ImageIFD.SamplesPerPixel,-1)
        self.header["image"]["main"]["Orientation"] = self.anyorientation()
        self.header["image"]["main"]["Resolution"] = resolution(self.ifd["0th"])
        self.header["image"]["main"]["Camera"] = 0 
        
        self.header["time"]["DateTimeOriginal"]= datetime.fromtimestamp(self.fff.get('DateTimeOriginal')).astimezone().isoformat(" ")
        self.header["time"]["GPSTimeStamp"] = "{:02.0f}:{:02.0f}:{:02.0f}".format(*self.exif["GPS"].get("GPSTimeStamp"),(0,0,0))
        self.header["time"]["FileCreated"] = self.header["file"]["Created"]
        self.header["time"]["FileModified"] = self.header["file"]["Modified"]
        
        self.header["position"]["Latitude"] = dms2dd(*self.exif["GPS"]["GPSLatitude"],self.exif["GPS"]["GPSLatitudeRef"])
        self.header["position"]["Longitude"] = dms2dd(*self.exif["GPS"]["GPSLongitude"],self.exif["GPS"]["GPSLongitudeRef"])
        self.header["position"]["Altitude"] = self.alt()
        self.header["position"]["RelAltitude"] = evaldiv(self.xmp.get("flir:mavrelativealtitude"))
        self.header["position"]["FlightPitch"] = evaldiv(self.xmp.get("flir:mavpitchrate"))
        self.header["position"]["FlightRoll"] = evaldiv(self.xmp.get("flir:mavrollrate"))
        self.header["position"]["FlightYaw"] = evaldiv(self.xmp.get("flir:mavyawrate"))
        self.header["position"]["FlightClimbRate"] = evaldiv(self.xmp.get("flir:mavrateofclimb"))
        self.header["position"]["FlightGyroRate"] = evaldiv(self.xmp.get("camera:gyrorate"))
        self.header["position"]["HorAccuracy"] = evaldiv(self.xmp.get("camera:gpsxyaccuracy"))
        self.header["position"]["VerAccuracy"] = evaldiv(self.xmp.get("camera:gpszaccuracy"))

        
        self.header["general"]["Model"] =  self.fff.get("CameraModel").decode("UTF-8")
        self.header["general"]["Make"] =  self.exif["0th"].get("Make")
        self.header["general"]["PartNumber"] =  self.fff.get("CameraPartNumber").decode("UTF-8")
        self.header["general"]["SerialNumber"] = self.fff.get('CameraSerialNumber').decode("UTF-8")
        self.header["general"]["MavVersionId"] = self.xmp.get('flir:mavversionid')
        self.header["general"]["MavComponentId"] = self.xmp.get('flir:mavcomponentid')
        self.header["general"]["CameraSoftware"] = self.fff.get("CameraSoftware").decode("UTF-8")
        
        #DateTimeOriginal': (1589706416, 165, -120),

        #self.header["exif"]["ExifVersion"] = int(self.ifd["Exif"].get(piexif.ExifIFD.ExifVersion,0).decode("UTF-8"))/100
        #self.header["gps"]["DateTime"] = isotimestr(*self.fff.get('DateTimeOriginal',(0,0,0)))
        
    #    self.header["calibration"]["radiometric"]["Emissivity"] = self.fff.get("Emissivity",[-1])
    #    self.header["calibration"]["radiometric"]["ObjectDistance"] = self.fff.get("ObjectDistance",[-1])
    #    
    #    self.header["calibration"]["radiometric"]["R"] = float(self.fff.get("PlanckR1",(0)))
    #    self.header["calibration"]["radiometric"]["F"] = float(self.fff.get("PlanckF",(1)))
     #   self.header["calibration"]["radiometric"]["B"] = float(self.fff.get("PlanckB",(0)))
     #   self.header["calibration"]["radiometric"]["R2"] = float(self.fff.get("PlanckR2",(0)))
     #   self.header["calibration"]["radiometric"]["Coretemp"] = self.fff.get("Coretemp",(1))
          
     #   #self.header["calibration"]["radiometric"]["Timestamp"] = 
     #   self.header["calibration"]["radiometric"]["IRWindowTemperature"] = float(self.fff.get("IRWindowTemperature",(0)))
     #   self.header["calibration"]["radiometric"]["IRWindowTransmission"] = float(self.fff.get("IRWindowTransmission",(1)))
            
