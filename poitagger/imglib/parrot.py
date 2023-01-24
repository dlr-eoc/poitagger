from .base import *

class ImageParrot(ImageBaseClass,jfif.JFIF):
    bitdepth = 8
    maker = "Parrot"
    
    @classmethod
    def is_registrar_for(cls, params):
        maker = params["ifd0"].get(piexif.ImageIFD.Make,"Unknown")
        filepath = params["filepath"]
        return maker in [b'Parrot',]
    
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
            nested_set(self.header, ["image","main","index"],len(self.images)-1)
            self.load_rawimage()
            
    def load_header(self):
        self.header["image"]["width"]= self.ifd["0th"].get(piexif.ImageIFD.ImageWidth,-1)
        self.header["image"]["height"]= self.ifd["0th"].get(piexif.ImageIFD.ImageLength,-1)
        self.header["image"]["bitdepth"]= self.ifd["0th"].get(piexif.ImageIFD.BitsPerSample,-1)
        self.header["image"]["channels"]= self.ifd["0th"].get(piexif.ImageIFD.SamplesPerPixel,-1)
        self.header["image"]["orientation"]= self.ifd["0th"].get(piexif.ImageIFD.Orientation,-1)
        
    def load_rawimage(self):
        raw_thermal_chunk = []
        raw_vis_chunk = []
        start = 10
        for s in self.segments:
            if not s[1]=="APP1": continue
            if s[2]-s[0]<6: continue
            length = 256 * self.rawdata[s[0]+2] + self.rawdata[s[0]+3]
            if self.rawdata[s[0]+4:s[0]+8] == b"PART":
                raw_thermal_chunk.append(self.rawdata[s[0]+2+start:s[0]+2+length])        
            elif self.rawdata[s[0]+4:s[0]+8] == b"PARV": 
                raw_vis_chunk.append(self.rawdata[s[0]+2+start:s[0]+2+length])        
        self.raw_thermal = b"".join(raw_thermal_chunk)
        self.raw_vis = b"".join(raw_vis_chunk)
        
        endian = ENDIAN[self.raw_thermal[0:4]]
        length = struct.Struct(endian["format"]+"I").unpack_from(self.raw_thermal[4:8])[0]
        raw_thermal_body = self.raw_thermal[8:length]
        self.raw_thermal_header = self.decode_struct(self.raw_thermal[length:],AnafiRawImageMeta)
        self.raw_thermal_image = np.frombuffer(raw_thermal_body, dtype="<u2",count=self.raw_thermal_header["Raw Image Width"]*self.raw_thermal_header["Raw Image Height"]) 
        self.raw_thermal_image = np.reshape(self.raw_thermal_image,(self.raw_thermal_header["Raw Image Height"],self.raw_thermal_header["Raw Image Width"]))
        self.images.append(self.raw_thermal_image)
        nested_set(self.header, ["image","raw_thermal","index"],len(self.images)-1)
        self.raw_vis_image = np.array(PILImage.open(BytesIO(self.raw_vis)))
        self.images.append(self.raw_vis_image)
        nested_set(self.header, ["image","raw_vis","index"],len(self.images)-1)
        