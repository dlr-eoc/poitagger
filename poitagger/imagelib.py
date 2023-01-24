import os
#import piexif
from io import BytesIO
import logging

from PIL import Image as PILImage
import numpy as np

from imglib import *
from imglib import piexif
import jfif
from  jfif_utils import *
#import nested

logger = logging.getLogger(__name__)

     
class ImageAra(ImageBaseClass):
    maker = "Intel"
    @classmethod
    def is_registrar_for(cls, params):
        maker = params["ifd0"].get(piexif.ImageIFD.Make,"Unknown")
        filepath = params["filepath"]
        base, ext = os.path.splitext(filepath)
        return ext.lower() in ['.ara',".raw"]

class ImageTiff(ImageBaseClass):
    maker = "unknown"
    @classmethod
    def is_registrar_for(cls, params):
        maker = params["ifd0"].get(piexif.ImageIFD.Make,"Unknown")
        filepath = params["filepath"]
        base, ext = os.path.splitext(filepath)
        return ext.lower() in ['.tiff',".tif"]

class ImageJpg(ImageBaseClass,jfif.JFIF):
    maker = "unknown"
    
    @classmethod
    def is_registrar_for(cls, params):
        maker = params["ifd0"].get(piexif.ImageIFD.Make,"Unknown")
        filepath = params["filepath"]
        base, ext = os.path.splitext(filepath)
        return ext.lower() in ['.jpg',".jpeg"]     
    
    def __init__(self, filepath=None,ifd=None,rawdata= b'',img=None,onlyheader=False):
        super().__init__(filepath,ifd,rawdata,img)
        self.images = []
        self.segments = self.main_segments(rawdata)
        self.load_exif()
        self.load_xmp(rawdata)
        self.params = {"exif":self.exif,"xmp":self.xmp}
        self.load_header()
        if not onlyheader:
            self.mainimage = np.array(PILImage.open(BytesIO(rawdata)))
            self.images.append(self.mainimage)
            nested_set(self.header, ["image","main","Index"],len(self.images)-1)
        self.load_thumbnail()
        self.set_main_params(0)
    
    
    def image_header(self,index):
        for k,v in self.header["image"].items():
            if index is v.get("Index"):
                return v
    
    def load_header(self):
        self.header["camera"][0]["Type"] = self.imagetype(0)
            
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
        
            self.header["general"]["Software"] = self.exif["0th"].get("Software")
            self.header["general"]["Make"] = self.exif["0th"].get("Make")
            self.header["general"]["Model"] = self.exif["0th"].get("Model")
        
        
        self.header["image"]["main"]["Camera"] = 0 
            
        self.header["time"]["DateTimeOriginal"]= self.exif["Exif"].get("DateTimeOriginal")
        self.header["time"]["DateTime"] = self.exif["0th"].get("DateTime")
        self.header["time"]["FileCreated"] = self.header["file"]["Created"]
        self.header["time"]["FileModified"] = self.header["file"]["Modified"]
        
        self.header["position"]["Latitude"] = dms2dd(*self.exif["GPS"].get("GPSLatitude",(0,0,0)),self.exif["GPS"].get("GPSLatitudeRef"))
        self.header["position"]["Longitude"] = dms2dd(*self.exif["GPS"].get("GPSLongitude",(0,0,0)),self.exif["GPS"].get("GPSLongitudeRef"))
        
        
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
    
    
    def set_main_params(self,imageid=0):
        current_shape = self.images[imageid].shape
        image_header = self.image_header(imageid)
        cur_camera = self.header["camera"][image_header["Camera"]]
        
        if "0th" in self.exif:
            self.header["main"]["Make"]=self.exif["0th"].get("Make","unknown")
            self.header["main"]["Model"]=self.exif["0th"].get("Model","unknown")
        self.header["main"]["Width"]=current_shape[1]
        self.header["main"]["Height"]=current_shape[0]
        self.header["main"]["DateTime"]=self.header["time"].get("DateTimeOriginal")
        self.header["main"]["Latitude"]=self.header["position"].get("Latitude")
        self.header["main"]["Longitude"]=self.header["position"].get("Longitude")
        self.header["main"]["RelAltitude"]=self.header["position"].get("RelAltitude",0)
        self.header["main"]["Pitch"]=cur_camera.get("Pitch")
        self.header["main"]["Roll"]=cur_camera.get("Roll")
        self.header["main"]["Yaw"]=cur_camera.get("Yaw")
        self.header["main"]["CurrentCamera"]=image_header["Camera"]
        self.header["main"]["CurrentImage"]=imageid
        
def Image(filepath=None,onlyheader=False):
    img = None 
    ifd = {}
    rawdata = b''
    if os.path.exists(filepath):
        with open(filepath,"rb") as f:
            rawdata = f.read()
            try:
                ifd = piexif.load(rawdata)
            except:
                ifd = {}    
        if not onlyheader:
            try:
                img = PILImage.open(BytesIO(rawdata))
            except:
                logger.info("PIL does not identify an image")
    else:
        logger.warning("file does not exist")
    
    ifd0 = ifd.get("0th", {})
    ifd0 = {k:(v.strip(b'\x00') if type(v)== bytes else v) for k,v in ifd0.items()}
    params = {"ifd0":ifd0,"filepath":filepath}
    for cls in ImageBaseClass.__subclasses__():
        if cls.is_registrar_for(params):
            instance =  cls(filepath,ifd,rawdata,img,onlyheader)
            
            return instance
    logger.error("unknown fileformat")
    return None   

if __name__=="__main__":
    import pprint
    pp = pprint.PrettyPrinter(indent=4, width=60, compact=True)
    path = "G:/Geteilte Ablagen/thermal DRONES GmbH/Wildretter-Daten/verschiedene Kameras"
    onlyheader = False 
    #onlyheader = True 
    dji1 = Image(os.path.join(path,"DJI/Testmaterial Mavic 2 Enterprise Advanced/Hausen_2021-08/DJI_0010.JPG"),onlyheader=onlyheader)
    #dji2 = Image(os.path.join(path,"DJI/Testmaterial Mavic 2 Enterprise Advanced/Hausen_2021-08/DJI_0011.JPG"),onlyheader=onlyheader)
    flir = Image(os.path.join(path,"FLIR/FLIR_Vue_640_20200517_110530/20200517_110530_R.jpg"),onlyheader=onlyheader)
    #pp.pprint(dji1.header)
    #pp.pprint(flir.header)
    td = Image("C:/WILDRETTER DATEN/210525_1130_obersöchering_dreieck_kühe/210525_112356_8.jpg")
    pp.pprint(td.header)
    