from .base import *
   
class ImageYuneec(ImageBaseClass,jfif.JFIF):
    bitdepth = 8
    maker = "Yuneec"
    
    @classmethod
    def is_registrar_for(cls, params):
        maker = params["ifd0"].get(piexif.ImageIFD.Make,"Unknown")
        filepath = params["filepath"]
        return maker in [b'YUNEE',b'Yuneec']
    
    def __init__(self, filepath=None,ifd=None,rawdata= b'',img=None,onlyheader=False):
        super().__init__(filepath,ifd,rawdata,img)
        self.images = []
        self.segments = self.main_segments(rawdata)
        self.load_exif()
        self.load_xmp(rawdata)
        self.params = {"exif":self.exif,"xmp":self.xmp}
        self.load_header()
    #    if not onlyheader:
    #        self.rawimage,self.bitdepth = get_raw(fffchunk)
    
    def load_header(self):
        self.header["image"]["width"]= self.ifd["0th"].get(piexif.ImageIFD.ImageWidth,-1)
        self.header["image"]["height"]= self.ifd["0th"].get(piexif.ImageIFD.ImageLength,-1)
        self.header["image"]["bitdepth"]= self.ifd["0th"].get(piexif.ImageIFD.BitsPerSample,-1)
        self.header["image"]["channels"]= self.ifd["0th"].get(piexif.ImageIFD.SamplesPerPixel,-1)
        self.header["image"]["orientation"]= self.ifd["0th"].get(piexif.ImageIFD.Orientation,-1)
