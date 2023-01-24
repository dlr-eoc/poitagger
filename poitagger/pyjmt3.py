import logging
import os
import re
import struct
from collections.abc import Container
from collections import OrderedDict
from fractions import Fraction

from bs4 import BeautifulSoup


def gpslat(value):
    dms = to_deg(value,["S","N"])
    return (*rational(dms[0]),*rational(dms[1]),*rational(dms[2])),bytes(dms[3],"UTF-8")

def gpslon(value):
    dms = to_deg(value,["W","E"])
    return (*rational(dms[0]),*rational(dms[1]),*rational(dms[2])),bytes(dms[3],"UTF-8")

def to_deg(value, loc):
    """convert decimal coordinates into degrees, minutes and seconds tuple
    Keyword arguments: value is float gps-value, loc is direction list ["S", "N"] or ["W", "E"]
    return: tuple like (25, 13, 48.343 ,'N')
    """
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    abs_value = abs(value)
    deg =  int(abs_value)
    t1 = (abs_value-deg)*60
    min = int(t1)
    sec = round((t1 - min)* 60, 5)
    return (deg, min, sec, loc_value)

def rational(number):
    """convert a number to rantional
    Keyword arguments: number
    return: tuple like (1, 2), (numerator, denominator)
    """
    f = Fraction(str(number)).limit_denominator(100000000)
    return (f.numerator, f.denominator)
    
TYPES = {1: {"id":1, "name":"Byte","format":"B","size":1},
        2: {"id":2,  "name":"Ascii","format":"s","size":1},
        3: {"id":3,  "name":"Short","format":"H","size":2},
        4: {"id":4,  "name":"Long","format":"L","size":4},
        5: {"id":5,  "name":"Rational","format":"LL","size":8},
        6: {"id":6,  "name":"SByte","format":"b","size":1},
        7: {"id":7,  "name":"Undefined","format":"B","size":1}, # B
        8: {"id":8,  "name":"SShort","format":"h","size":2},
        9: {"id":9,  "name":"SLong","format":"l","size":4},
        10: {"id":10,"name":"SRational","format":"ll","size":8},
        11: {"id":11,"name":"Float","format":"f","size":4},
        12: {"id":12,"name":"Double","format":"d","size":8},
        }


ENDIAN = {b"II*\x00":{"name":"Little Endian","format":"<","data":b"II*\x00","shortname":"little"},
          b"MM*\x00":{"name":"Big Endian","format":">","data":b"MM*\x00","shortname":"big"}}

IFD_TAG_SIZE = 12 # HHII (TagID (short), Type (short), Count (int),ValueOffset (int) )
NEXT_IFD_OFFSET_SIZE = 4
NUM_OF_INTEROP_SIZE = 2

MARKER_2BYTE = {
    b"\xff\xd8":"SOI"  ,  # Start of Image
    b"\xff\xd9":"EOI"  ,  # End of Image
    b"\xff\xd0":"RST0" ,  # RSTn are used for resync, may be ignored
    b"\xff\xd1":"RST1" ,
    b"\xff\xd2":"RST2" ,
    b"\xff\xd3":"RST3" ,
    b"\xff\xd4":"RST4" ,
    b"\xff\xd5":"RST5" ,
    b"\xff\xd6":"RST6" ,
    b"\xff\xd7":"RST7" ,
    b"\xff\x01":"TEM"  ,
    }

MARKER_2BYTE_REV = {y:x for x,y in MARKER_2BYTE.items()}

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
    b"\xff\xfe":"COM"  # Comment
    }

MARKER_REV = {y:x for x,y in MARKER.items()}

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

ImageIFD = {  "ImageIFD":"__type__",
            "__type__":"ImageIFD",
            11:'ProcessingSoftware',
           254:'NewSubfileType',
           255:'SubfileType',
           256:'ImageWidth',
           257:'ImageLength',
           258:'BitsPerSample',
           259:'Compression',
           262:'PhotometricInterpretation',
           263:'Threshholding',
           264:'CellWidth',
           265:'CellLength',
           266:'FillOrder',
           269:'DocumentName',
           270:'ImageDescription',
           271:'Make',
           272:'Model',
           273:'StripOffsets',
           274:'Orientation',
           277:'SamplesPerPixel',
           278:'RowsPerStrip',
           279:'StripByteCounts',
           282:'XResolution',
           283:'YResolution',
           284:'PlanarConfiguration',
           290:'GrayResponseUnit',
           291:'GrayResponseCurve',
           292:'T4Options',
           293:'T6Options',
           296:'ResolutionUnit',
           301:'TransferFunction',
           305:'Software',
           306:'DateTime',
           315:'Artist',
           316:'HostComputer',
           317:'Predictor',
           318:'WhitePoint',
           319:'PrimaryChromaticities',
           320:'ColorMap',
           321:'HalftoneHints',
           322:'TileWidth',
           323:'TileLength',
           324:'TileOffsets',
           325:'TileByteCounts',
           330:'SubIFDs',
           332:'InkSet',
           333:'InkNames',
           334:'NumberOfInks',
           336:'DotRange',
           337:'TargetPrinter',
           338:'ExtraSamples',
           339:'SampleFormat',
           340:'SMinSampleValue',
           341:'SMaxSampleValue',
           342:'TransferRange',
           343:'ClipPath',
           344:'XClipPathUnits',
           345:'YClipPathUnits',
           346:'Indexed',
           347:'JPEGTables',
           351:'OPIProxy',
           512:'JPEGProc',
           513:'JPEGInterchangeFormat',
           514:'JPEGInterchangeFormatLength',
           515:'JPEGRestartInterval',
           517:'JPEGLosslessPredictors',
           518:'JPEGPointTransforms',
           519:'JPEGQTables',
           520:'JPEGDCTables',
           521:'JPEGACTables',
           529:'YCbCrCoefficients',
           530:'YCbCrSubSampling',
           531:'YCbCrPositioning',
           532:'ReferenceBlackWhite',
           700:'XMLPacket',
           18246:'Rating',
           18249:'RatingPercent',
           32781:'ImageID',
           33421:'CFARepeatPatternDim',
           33422:'CFAPattern',
           33423:'BatteryLevel',
           33432:'Copyright',
           33434:'ExposureTime',
           33437: 'FNumber',
           34377:'ImageResources',
           34665:'ExifTag',
           34675:'InterColorProfile',
           34853:'GPSTag',
           34857:'Interlace',
           34858:'TimeZoneOffset',
           34859:'SelfTimerMode',
           37386: 'FocalLength',
           37387:'FlashEnergy',
           37388:'SpatialFrequencyResponse',
           37389:'Noise',
           37390:'FocalPlaneXResolution',
           37391:'FocalPlaneYResolution',
           37392:'FocalPlaneResolutionUnit',
           37393:'ImageNumber',
           37394:'SecurityClassification',
           37395:'ImageHistory',
           37397:'ExposureIndex',
           37398:'TIFFEPStandardID',
           37399:'SensingMethod',
           40091:'XPTitle',
           40092:'XPComment',
           40093:'XPAuthor',
           40094:'XPKeywords',
           40095:'XPSubject',
           41486: 'FocalPlaneXResolution',
           41487: 'FocalPlaneYResolution',
           41488: 'FocalPlaneResolutionUnit',
           50341:'PrintImageMatching',
           50706:'DNGVersion',
           50707:'DNGBackwardVersion',
           50708:'UniqueCameraModel',
           50709:'LocalizedCameraModel',
           50710:'CFAPlaneColor',
           50711:'CFALayout',
           50712:'LinearizationTable',
           50713:'BlackLevelRepeatDim',
           50714:'BlackLevel',
           50715:'BlackLevelDeltaH',
           50716:'BlackLevelDeltaV',
           50717:'WhiteLevel',
           50718:'DefaultScale',
           50719:'DefaultCropOrigin',
           50720:'DefaultCropSize',
           50721:'ColorMatrix1',
           50722:'ColorMatrix2',
           50723:'CameraCalibration1',
           50724:'CameraCalibration2',
           50725:'ReductionMatrix1',
           50726:'ReductionMatrix2',
           50727:'AnalogBalance',
           50728:'AsShotNeutral',
           50729:'AsShotWhiteXY',
           50730:'BaselineExposure',
           50731:'BaselineNoise',
           50732:'BaselineSharpness',
           50733:'BayerGreenSplit',
           50734:'LinearResponseLimit',
           50735:'CameraSerialNumber',
           50736:'LensInfo',
           50737:'ChromaBlurRadius',
           50738:'AntiAliasStrength',
           50739:'ShadowScale',
           50740:'DNGPrivateData',
           50741:'MakerNoteSafety',
           50778:'CalibrationIlluminant1',
           50779:'CalibrationIlluminant2',
           50780:'BestQualityScale',
           50781:'RawDataUniqueID',
           50827:'OriginalRawFileName',
           50828:'OriginalRawFileData',
           50829:'ActiveArea',
           50830:'MaskedAreas',
           50831:'AsShotICCProfile',
           50832:'AsShotPreProfileMatrix',
           50833:'CurrentICCProfile',
           50834:'CurrentPreProfileMatrix',
           50879:'ColorimetricReference',
           50931:'CameraCalibrationSignature',
           50932:'ProfileCalibrationSignature',
           50934:'AsShotProfileName',
           50935:'NoiseReductionApplied',
           50936:'ProfileName',
           50937:'ProfileHueSatMapDims',
           50938:'ProfileHueSatMapData1',
           50939:'ProfileHueSatMapData2',
           50940:'ProfileToneCurve',
           50941:'ProfileEmbedPolicy',
           50942:'ProfileCopyright',
           50964:'ForwardMatrix1',
           50965:'ForwardMatrix2',
           50966:'PreviewApplicationName',
           50967:'PreviewApplicationVersion',
           50968:'PreviewSettingsName',
           50969:'PreviewSettingsDigest',
           50970:'PreviewColorSpace',
           50971:'PreviewDateTime',
           50972:'RawImageDigest',
           50973:'OriginalRawFileDigest',
           50974:'SubTileBlockSize',
           50975:'RowInterleaveFactor',
           50981:'ProfileLookTableDims',
           50982:'ProfileLookTableData',
           51008:'OpcodeList1',
           51009:'OpcodeList2',
           51022:'OpcodeList3',
           60606:'ZZZTestSlong1',
           60607:'ZZZTestSlong2',
           60608:'ZZZTestSByte',
           60609:'ZZZTestSShort',
           60610:'ZZZTestDFloat'}
ImageIFD_REV = {y:x for x,y in ImageIFD.items()}
           
ExifIFD= {  "ExifIFD":"__type__",
            "__type__":"ExifIFD",
              700: 'XMP',
            33434: 'ExposureTime',
            33437: 'FNumber',
            34850: 'ExposureProgram',
            34852: 'SpectralSensitivity',
            34855: 'ISOSpeedRatings',
            34856: 'OECF',
            34864: 'SensitivityType',
            34865: 'StandardOutputSensitivity',
            34866: 'RecommendedExposureIndex',
            34867: 'ISOSpeed',
            34868: 'ISOSpeedLatitudeyyy',
            34869: 'ISOSpeedLatitudezzz',
            36864: 'ExifVersion',
            36867: 'DateTimeOriginal',
            36868: 'DateTimeDigitized',
            36880: 'OffsetTime',
            36881: 'OffsetTimeOriginal',
            36882: 'OffsetTimeDigitized',
            37121: 'ComponentsConfiguration',
            37122: 'CompressedBitsPerPixel',
            37377: 'ShutterSpeedValue',
            37378: 'ApertureValue',
            37379: 'BrightnessValue',
            37380: 'ExposureBiasValue',
            37381: 'MaxApertureValue',
            37382: 'SubjectDistance',
            37383: 'MeteringMode',
            37384: 'LightSource',
            37385: 'Flash',
            37386: 'FocalLength',
            37396: 'SubjectArea',
            37500: 'MakerNote',
            37510: 'UserComment',
            37520: 'SubSecTime',
            37521: 'SubSecTimeOriginal',
            37522: 'SubSecTimeDigitized',
            37888: 'Temperature',
            37889: 'Humidity',
            37890: 'Pressure',
            37891: 'WaterDepth',
            37892: 'Acceleration',
            37893: 'CameraElevationAngle',
            40960: 'FlashpixVersion',
            40961: 'ColorSpace',
            40962: 'PixelXDimension',
            40963: 'PixelYDimension',
            40964: 'RelatedSoundFile',
            40965: 'InteroperabilityTag',
            41483: 'FlashEnergy',
            41484: 'SpatialFrequencyResponse',
            41486: 'FocalPlaneXResolution',
            41487: 'FocalPlaneYResolution',
            41488: 'FocalPlaneResolutionUnit',
            41492: 'SubjectLocation',
            41493: 'ExposureIndex',
            41495: 'SensingMethod',
            41728: 'FileSource',
            41729: 'SceneType',
            41730: 'CFAPattern',
            41985: 'CustomRendered',
            41986: 'ExposureMode',
            41987: 'WhiteBalance',
            41988: 'DigitalZoomRatio',
            41989: 'FocalLengthIn35mmFilm',
            41990: 'SceneCaptureType',
            41991: 'GainControl',
            41992: 'Contrast',
            41993: 'Saturation',
            41994: 'Sharpness',
            41995: 'DeviceSettingDescription',
            41996: 'SubjectDistanceRange',
            42016: 'ImageUniqueID',
            42032: 'CameraOwnerName',
            42033: 'BodySerialNumber',
            42034: 'LensSpecification',
            42035: 'LensMake',
            42036: 'LensModel',
            42037: 'LensSerialNumber',
            42240: 'Gamma'}

ExifIFD_REV = {y:x for x,y in ExifIFD.items()}

GPSIFD = {"GPSIFD":"__type__",
          "__type__":"GPSIFD",
          0: 'GPSVersionID', 
          1: 'GPSLatitudeRef',
          2: 'GPSLatitude',
          3: 'GPSLongitudeRef',
          4: 'GPSLongitude',
          5: 'GPSAltitudeRef', 
          6: 'GPSAltitude',
          7: 'GPSTimeStamp',
          8: 'GPSSatellites',
          9: 'GPSStatus',
          10: 'GPSMeasureMode',
          11: 'GPSDOP',
          12: 'GPSSpeedRef',
          13: 'GPSSpeed',
          14: 'GPSTrackRef',
          15: 'GPSTrack',
          16: 'GPSImgDirectionRef',
          17: 'GPSImgDirection',
          18: 'GPSMapDatum',
          19: 'GPSDestLatitudeRef',
          20: 'GPSDestLatitude',
          21: 'GPSDestLongitudeRef',
          22: 'GPSDestLongitude',
          23: 'GPSDestBearingRef',
          24: 'GPSDestBearing',
          25: 'GPSDestDistanceRef',
          26: 'GPSDestDistance',
          27: 'GPSProcessingMethod',
          28: 'GPSAreaInformation',
          29: 'GPSDateStamp',
          30: 'GPSDifferential',
          31: 'GPSHPositioningError'}

GPSIFD_REV = {y:x for x,y in GPSIFD.items()}
  
class PyJMT(object):
    
    def __init__(self,filename=None):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.filename = filename
        self.endian = ENDIAN[b"MM*\x00"]
        self.rawexif = None
        self.IFD_1 = None
        self.rawxmp = None
        self.xmp = None
        self.segments = []
        
        if filename is not None:
            self.data = self.__open__()
            self.__load__(self.data)
            self.readExif()
    
    def set_endian(self,endian):
        if endian == "little":
            self.endian = ENDIAN[b"II*\x00"]
        elif endian == "big":
            self.endian = ENDIAN[b"MM*\x00"]
            
    def __structfmt__(self,tagCount,tagType):
        if TYPES[tagType]["name"] in ["Rational","SRational"]:
            return  str(tagCount) + \
                    TYPES[tagType]["format"][0] + \
                    str(tagCount) + \
                    TYPES[tagType]["format"][1]
        else:
            return  str(tagCount)+ \
                    TYPES[tagType]["format"]
    
    def __open__(self):
        data = None
        try:
            with open(self.filename,"rb") as f:
                data = f.read()
        except FileNotFoundError as e:
            logging.error(e)
        except:
            logging.error(e)
        return data
            
    def __load__(self,data):
        if (data[0:2] != MARKER_2BYTE_REV["SOI"]):
            logging.warning("this is not a jpeg file")
        self.segments = self.__find_segments__(data)
        
        last = {"id":"","pos":0,"end":0,"segment":"","paremt":0,"level":0,"data":b""}
        for k,i in enumerate(self.segments):
            if i["level"]!= 0: continue
            if i["pos"]>last["end"]:
                self.segments.insert(k,{"id":'',"pos":last["end"],"end":i["pos"],
                                        "segment":"IMG","type":"",
                                        "data":data[last["end"] : i["pos"]],
                                       "parent": last["parent"], 
                                        "level": last["level"]})
            last = i
        
    def __loadExifHeader__(self):
        try:
            self.endian = ENDIAN[self.rawexif[0:4]]
        except:
            logging.error("This File has no valid Exif Header")
        IFD_0_Offset = struct.Struct(self.endian["format"]+"L").unpack(self.rawexif[4:8])[0]
        return IFD_0_Offset
    
    def __writeExifHeader__(self,exifcontent):
        length = len(exifcontent)+2
        rawexif = [b'\xFF\xE1']
        rawexif.append(struct.Struct(">H").pack(length))
        rawexif.append(exifcontent)
        return b''.join(rawexif)
    
    def __find_segments__(self,data):
        """
        A Jpeg file is normally structured as JFIF.
        JFIF has Segments (see MARKER)
        
        returns the complete File as a Segments-List
        """
        pattern = bytearray(b"..|".join(MARKER.keys()))
        pattern.extend(b"..|")
        pattern.extend(b"|".join(MARKER_2BYTE.keys()))
        cpattern = re.compile(bytes(pattern))
        segments = []
        id = 0
        parent = 0
        for m in cpattern.finditer(data):
            if len(m.group())>=4: 
                seg_length = 256 * m.group()[2] + m.group()[3]
                segment = MARKER[m.group()[:-2]]
            else:
                seg_length = 0
                try:
                    segment = MARKER[m.group()]
                except KeyError:
                    segment = MARKER_2BYTE[m.group()]
                except: 
                    logging.error("find JFIF Segment failed",exc_info=True)
            if segment in ["APP0","APP1"]:
                seg_type = data[m.start()+4:m.start()+8]
            else:
                seg_type = ''
                        
            parent,level = next(((item["id"],item["level"]+1) 
                                for item in reversed(segments) 
                                    if item["end"] > m.start()), (0,0))
            segments.append({"id":id,
                "segment": segment,
                "pos":m.start(),
                "end" : m.start()+seg_length+2,
                "type": seg_type,             
                "parent": parent, 
                "level": level, 
                "data": data[m.start() : m.start() + seg_length+2]   })
            id += 1
        return segments
    
    
    def readExif(self):
        self.rawexif = next((item["data"][10:] 
                             for item in self.segments 
                                 if item["data"][4:8] == b"Exif"),b'')
        try:
            IFD_0_Offset = self.__loadExifHeader__()
        except:
            logging.warning("No Exif found")
            return self.rawexif
        self.IFD_0, nextIFDOffset = self.loadIFD(IFD_0_Offset, ImageIFD)
        if nextIFDOffset > 0: #Thumbnail
            try:
                self.IFD_1, nextIFDOffset = self.loadIFD(nextIFDOffset, ImageIFD)
            except:
                self.IFD_1 = None
                #logging.warning("No Thumbnail found", exc_info=True)
        
        try:
            ExifIFD_Offset = next(item["value"] 
                            for item in self.IFD_0 
                                  if item["name"] == "ExifTag")
            self.ExifIFD, nextIFDOffset = self.loadIFD(ExifIFD_Offset, ExifIFD)
        except:
            logging.warning("No Exif-IFD found", exc_info=True)
        
        try:
            self.rawxmp = next(item["value"] 
                            for item in self.ExifIFD 
                               if item["name"] =="XMP")
        except:
            self.rawxmp = b''
        
        try:
            GPSIFD_Offset = next(item["value"] 
                            for item in self.IFD_0 
                                 if item["name"] == "GPSTag")
            self.GPSIFD, nextIFDOffset = self.loadIFD(GPSIFD_Offset, GPSIFD)
        except:
            self.GPSIFD = None
        return self.rawexif
   
    def __unpackIFDValueOffset__(self,typ,cnt,pos):
        """
        An Exif Header is structured in IFD0, ExifIFD, GPSIFD and IFD1.
        All these IFDs have multiple 12Byte long Entries:
        Tag ID (2Byte), Type(2Byte), Count(4Byte), ValueOffset(4Byte)
        ValueOffset is Value or Offset, depending if value is <=4Byte.
        Offset points to the end of the IFD-Table, where all Values longer than 4Bytes are stored.
        
        returns the Value if value <=4Byte or the offset and the length of the value to identify if it is offset or value
        
        ==============  ================================================================
        **Arguments:**
        typ             the ID of the Datatype defined in TYPES
                        with TYPES[typ] you have more information on the current datatyp
        cnt             is the amount of Value-Datatypes e.g. 3 Rational for GPS Timestamp
                        this is the value in each IFD-Entry
        pos             position from start of Exif-Data (endian marker starts at pos 0, e.g.: "MM*" or "II*")   
        ==============  ================================================================
        """
        bytecnt = TYPES[typ]["size"]*cnt
        if bytecnt > 4:
            tagValueOffset = struct.Struct(
                self.endian["format"]+"I").unpack(
                self.rawexif[pos:pos+4])[0]
        else:
            if bytecnt == 0:
                return 0,0
            tagValueOffset = struct.Struct(
                self.endian["format"]+str(cnt)+TYPES[typ]["format"]).unpack(
                self.rawexif[pos:pos+bytecnt])
            tagValueOffset = tagValueOffset[0]
            if TYPES[typ]["name"] in ["Ascii"]:
                tagValueOffset = tagValueOffset.strip(b"\x00")
        return tagValueOffset, bytecnt
    
    def __fill4Bytes__(self,cnt,tag):
        """
        returns a 4 Byte long value. If Value is shorter it is filled with b"\x00"
        this is needed to get the right sized IFD-Entries
        """
        typ = TYPES[tag["typeid"]]
        bytecnt = cnt * typ["size"]
        data = self.__prepareValuePack__(cnt,tag)
        fmt = str(cnt)+typ["format"]
        if bytecnt<4:
            fmt += str(4-bytecnt)+"B"
            for i in range(0,4-bytecnt): data.append(0)
        return fmt, data
        
            
    def __prepareValuePack__(self,count,tag):
        """
        this is for writing from the IFD-List to the jpeg rawdata
        
        returns the correct format for the value. It is allways a List with one to max. 2x count elements. 
        e.g. an int is [34,]
        a list of 3 rationals (0,1),(1,1),(2,1) is for example [0,1,1,1,2,1]
        """
        typ = TYPES[tag["typeid"]]
        if typ["name"] in ["Rational","SRational"]:
            elem_cnt = 2*count
        else: 
            elem_cnt = count
            
        if isinstance(tag["value"], Container) and typ["name"] != "Ascii":
            cont_size = len(tag["value"])
            if cont_size==1:
                val_cont = [tag["value"]]
            else:
                val_cont = list(tag["value"])
            if cont_size < elem_cnt:
                for i in range(0,elem_cnt-cont_size):
                    val_cont.append(0)
        else:
            val_cont=[tag["value"]]
        
        return val_cont
        
        
    def __packIFDTag__(self,tag,offset):
        """
        packs the data of a tag into binary data. Due to the fact that IFD can only store 4 Byte Values 
        all bigger data are stored in extended. offset is the current position for extended data. 
        (offset 0 is exif start position)
        """
        if tag["type"] in ["Rational","SRational"]:
            try:
                count = len(tag["value"])//2
            except:
                logging.warning("pack tag failed "+str(tag),exc_info=True)
        elif isinstance(tag["value"], Container):
            count = len(tag["value"])
        else:
            count = 1
        typ = TYPES[tag["typeid"]]
        bytecnt = count * typ["size"]
        fmt = self.__structfmt__(count,tag["typeid"])
        bindata = b''
        extended = b''
        if bytecnt > 4:
            try:
                bindata = struct.Struct(
                    self.endian["format"]+"HHII").pack(tag["id"],tag["typeid"],count,offset)
            except:
                logging.error("pack IFD Tag failed, count:"+str(count)+", offset:"+str(offset) +", tag:"+str(tag) ,exc_info=True)
            value = self.__prepareValuePack__(count,tag)
            try:
                extended = struct.Struct(self.endian["format"]+fmt).pack(*value)
            except:
                logging.error("pack IFD Tag failed, fmt:"+fmt+", data:"+str(value) +", tag:"+str(tag) ,exc_info=True)
            
        else:
            try:
                fmt,data = self.__fill4Bytes__(count,tag)
                bindata = struct.Struct(self.endian["format"]+"HHI"+fmt).pack(tag["id"],tag["typeid"],count,*data)
            except:
                logging.error("pack IFD Tag failed, fmt:"+fmt+", data:"+str(data) +", tag:"+str(tag) ,exc_info=True)
        return bindata, extended
    
    
    def loadIFD(self,IFDOffset,IFDTags):
        """
        import from Jpeg raw data to the IFD-List
        """
        NumberOfInteroperability = struct.Struct( # this is the amount of tags in this IFD
        self.endian["format"]+"H").unpack(
                    self.rawexif[IFDOffset:IFDOffset+NUM_OF_INTEROP_SIZE])[0]
        offset = IFDOffset+ NUM_OF_INTEROP_SIZE #IFDOffset + 2 Byte (Number of Interoperability)
        IFD = []
        for i in range(0,IFD_TAG_SIZE*NumberOfInteroperability,IFD_TAG_SIZE):
            tagValPos = offset+i+IFD_TAG_SIZE-4
            (tagId,tagType,tagCount) = struct.Struct(
                    self.endian["format"]+"HHI").unpack(
                    self.rawexif[offset+i:tagValPos])
            
            tagValueOffset, datasize = self.__unpackIFDValueOffset__(tagType,tagCount,tagValPos)
            
            if datasize > 4: #tagValueOffset is an Offset Address
                rawdata = self.rawexif[tagValueOffset:tagValueOffset+datasize]
                value = struct.Struct(self.endian["format"] + self.__structfmt__(tagCount,tagType)).unpack(rawdata)
                if len(value)==1:
                    value = value[0]
                    if isinstance(value, bytearray):
                        value = value.strip(b"\x00")
            else: 
                value = tagValueOffset
                rawdata = self.rawexif[offset+i+IFD_TAG_SIZE-4:offset+i+IFD_TAG_SIZE]
            
            if TYPES[tagType]["name"] in ["Undefined","Byte","SByte"]: #Ascii
                value = rawdata.strip(b"\x00") #self.__asciireadable__(value)
            try:    
                IFD.append({"name":IFDTags[tagId],
                            "id": tagId,
                            "type":TYPES[tagType]["name"],
                            "typeid":tagType,
                            "value":value,
                            "rawdata":rawdata})
            except:
                logging.warning("unknown tag (id:{},value:{}".format(tagId,value))
        rawdata = self.rawexif[offset+IFD_TAG_SIZE*NumberOfInteroperability:offset+IFD_TAG_SIZE*NumberOfInteroperability + 4]
        nextIFDOffset = struct.Struct(self.endian["format"] + "I").unpack(rawdata)[0]
        return IFD,nextIFDOffset
    
    def createExif(self,width,height):
        self.IFD_0 = [{'name': 'BitsPerSample','id': 258,'type': 'Short','typeid': 3,'value': 8},
         {'name': 'Make', 'id': 271,  'type': 'Ascii',  'typeid': 2,  'value': b'FLIR\x00'},
         {'name': 'Model',  'id': 272,  'type': 'Ascii',  'typeid': 2,  'value': b'Boson\x00'},
         {'name': 'XResolution','id': 282,'type': 'Rational','typeid': 5,'value': (72, 1)},
         {'name': 'YResolution','id': 283,'type': 'Rational','typeid': 5,'value': (72, 1)},
         {'name': 'ResolutionUnit','id': 296,'type': 'Short','typeid': 3,'value': 2},
         {'name': 'YCbCrPositioning','id': 531,'type': 'Short','typeid': 3,'value': 1},
         {'name': 'FocalLength','id': 37386,'type': 'Rational','typeid': 5,'value': (1,1)},
         {'name': 'FNumber','id': 33437,'type': 'Rational','typeid': 5,'value': (1,1)},
         {'name': 'ExifTag','id': 34665,'type': 'Long','typeid': 4,'value': 0},
         {'name': 'GPSTag','id': 34853,'type': 'Long','typeid': 4, 'value': 0}]
        self.ExifIFD = [{'name': 'ExifVersion','id': 36864,'type': 'Undefined','typeid': 7,'value': b'0210'},
         {'name': 'ComponentsConfiguration','id': 37121,'type': 'Undefined','typeid': 7,'value': b'\x01\x02\x03'},
         {'name': 'FlashpixVersion','id': 40960,'type': 'Undefined','typeid': 7,'value': b'0100'},
         {'name': 'ColorSpace','id': 40961,'type': 'Short','typeid': 3,'value': 1},
         {'name': 'DateTimeOriginal','id': 36867 ,'type': 'Ascii','typeid': 2,'value': b'\x00'},
         {'name': 'SubSecTimeOriginal','id':  37521 ,'type': 'Ascii','typeid': 2,'value': b'\x00'},
         {'name': 'PixelXDimension','id': 40962,'type': 'Long','typeid': 4,'value': width},
         {'name': 'PixelYDimension','id': 40963,'type': 'Long','typeid': 4,'value': height}]
        self.GPSIFD = [{'name': 'GPSVersionID','id': 0,'type': 'Byte','typeid': 1,'value': b'\x03\x02'},
         {'name': 'GPSLatitudeRef', 'id': 1,  'type': 'Ascii',  'typeid': 2,  'value': b'S'},
         {'name': 'GPSLatitude', 'id': 2, 'type': 'SRational', 'typeid': 10,'value': (0, 1, 0, 1, 0, 10000000)},
         {'name': 'GPSLongitudeRef','id': 3,'type': 'Ascii','typeid': 2,'value': b'W'},
         {'name': 'GPSLongitude','id': 4,'type': 'SRational','typeid': 10,'value': (0, 1, 0, 1, 0, 10000000)},
         {'name': 'GPSAltitudeRef','id': 5,'type': 'Byte','typeid': 1,'value': 0,},
         {'name': 'GPSAltitude','id': 6,'type': 'SRational','typeid': 10,'value': (0, 1000)},
         {'name': 'GPSTimeStamp','id': 7,'type': 'Rational','typeid': 5,'value': (0, 1, 0, 1, 0, 1)},
         {'name': 'GPSDateStamp','id': 7,'type': 'Ascii','typeid': 2,'value': b"2019:05:22\x00"},
         {'name': 'GPSSpeedRef', 'id': 12, 'type': 'Ascii', 'typeid': 2,'value': b'K'},
         {'name': 'GPSSpeed','id': 13,'type': 'Rational','typeid': 5,'value': (0, 1000)},
         {'name': 'GPSTrackRef','id': 14,'type': 'Ascii','typeid': 2,'value': b'T'},
         {'name': 'GPSTrack',  'id': 15, 'type': 'Rational',  'typeid': 5,  'value': (0, 100)}]
       # self.IFD_1 = [{'name': 'Compression',  'id': 259,'type': 'Short','typeid': 3,'value': 6},
       #  {'name': 'Orientation','id': 274,'type': 'Short','typeid': 3,'value': 1},
       #  {'name': 'XResolution','id': 282,'type': 'SRational','typeid': 10,'value': (72, 1)},
       #  {'name': 'YResolution','id': 283,'type': 'SRational','typeid': 10,'value': (72, 1)},
       #  {'name': 'ResolutionUnit','id': 296,'type': 'Short','typeid': 3,'value': 2}]
        
        
        return self.assembleExif()
          
    def tag(self,name):
        """
        when manipulating the value of a tag: choose the right datatype. don't use strings (e.g. "hallo") but bytes (b'hallo')
        
        usage: 
        x = PyJMT()
        x.createExif(640,512)    
        x.tag("Make")["value"]=b"Maker"
        
        """
        for container in [self.IFD_0,self.ExifIFD,self.GPSIFD]:
            try:
                out = next(item for item in container if item["name"] == name)
                if not out:
                    pass
                return out    
            except StopIteration:
                pass
            except:
                logging.error("tag error",exc_info=True)
                
        
    def assembleExif(self):
        rawexif = [b'Exif\x00\x00', self.endian["data"]]
        offset = len(self.endian["data"])+4
        rawexif.append(struct.Struct(self.endian["format"]+"L").pack(offset)) # Offset to the first IFD
        
        IFD_0_Offset = offset
        rawIFD0, rawIFD0ext = self.assembleIFD(IFD_0_Offset,self.IFD_0)
        offset += len(rawIFD0) + len (rawIFD0ext) + 4
        ExifIFD_Offset = offset
        
        rawExifIFD, rawExifIFDext = self.assembleIFD(ExifIFD_Offset,self.ExifIFD)
        offset += len(rawExifIFD) + len (rawExifIFDext) + 4
                
        exiftag = next(i for i in self.IFD_0 if i["name"]=="ExifTag")
        exiftag["value"] = ExifIFD_Offset
        
        if self.GPSIFD:
            GPSIFD_Offset = offset
            rawGPSIFD, rawGPSIFDext = self.assembleIFD(GPSIFD_Offset,self.GPSIFD)
            offset += len(rawGPSIFD) + len (rawGPSIFDext) + 4
        
            gpstag = next(i for i in self.IFD_0 if i["name"]=="GPSTag")
            gpstag["value"] = GPSIFD_Offset

        if self.IFD_1:
            IFD_1Offset = struct.Struct(self.endian["format"]+ "I").pack(offset)
            rawIFD1, rawIFD1ext = self.assembleIFD(offset,self.IFD_1)
            offset += len(rawIFD1) + len (rawGPSIFDext) + 4
        
        rawIFD0, rawIFD0ext = self.assembleIFD(IFD_0_Offset,self.IFD_0)
        
        rawexif.append(rawIFD0)
        if self.IFD_1:
            rawexif.append(IFD_1Offset)
        else:
            rawexif.append(b'\x00\x00\x00\x00')
        rawexif.append(rawIFD0ext)
        rawexif.append(rawExifIFD)
        rawexif.append(b'\x00\x00\x00\x00')
        rawexif.append(rawExifIFDext)
        if self.GPSIFD:
            rawexif.append(rawGPSIFD)
            rawexif.append(b'\x00\x00\x00\x00')
            rawexif.append(rawGPSIFDext)
        return b''.join(rawexif)
    
            
    def assembleIFD(self, IFDOffset, IFDTags):
        NumberOfInteroperability = len(IFDTags) 
        out = [struct.Struct(self.endian["format"]+"H").pack(NumberOfInteroperability)]
        Extension = []
        offset = IFDOffset +  NUM_OF_INTEROP_SIZE + IFD_TAG_SIZE * NumberOfInteroperability + NEXT_IFD_OFFSET_SIZE
     
        for tag in IFDTags:
            currententry, extended = self.__packIFDTag__(tag,offset)
            out.append(currententry)
            Extension.append(extended)
            offset += len(extended)
        
        return b''.join(out), b''.join(Extension)    
    
    def getExifTags(self):
        ExifTagDict = {}
        for i in self.IFD_0:
            ExifTagDict[i["name"]]=i["value"]
        for i in self.ExifIFD:
            if i["name"]=="XMP": continue
            ExifTagDict[i["name"]]=i["value"]
            if i["name"] in ["ExifVersion","FlashpixVersion","ComponentsConfiguration"]:
                ExifTagDict[i["name"]]=i["rawdata"]
        for i in self.GPSIFD:
            ExifTagDict[i["name"]]=i["value"]
        if self.xmp:
            for i in self.xmp.find("rdf:description").children:
                if i.name:
                    ExifTagDict[i.name]=i.string
        return ExifTagDict
        
    def createXmp(self):
        rawxmp = b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\r\n\
        xmlns:Camera="http://pix4d.com/camera/1.0/"\r\nxmlns:FLIR="http://ns.flir.com/xmp/1.0/">\r\n\
        <rdf:Description rdf:about="">\r\n\
        <Camera:BandName>\r\n<rdf:Seq>\r\n<rdf:li>LWIR</rdf:li>\r\n</rdf:Seq>\r\n</Camera:BandName>\r\n\
        <Camera:CentralWavelength>\r\n<rdf:Seq>\r\n<rdf:li>10000</rdf:li>\r\n</rdf:Seq>\r\n</Camera:CentralWavelength>\r\n\
        <Camera:WavelengthFWHM>\r\n<rdf:Seq>\r\n<rdf:li>4500</rdf:li>\r\n</rdf:Seq>\r\n</Camera:WavelengthFWHM>\r\n\
        <Camera:TlinearGain>0.00</Camera:TlinearGain>\r\n\
        <Camera:Yaw>0/100</Camera:Yaw>\r\n\
        <Camera:Pitch>0/100</Camera:Pitch>\r\n\
        <Camera:Roll>0/100</Camera:Roll>\r\n\
        <Camera:GPSXYAccuracy>0</Camera:GPSXYAccuracy>\r\n\
        <Camera:GPSZAccuracy>0</Camera:GPSZAccuracy>\r\n\
        <Camera:GyroRate>0.00</Camera:GyroRate>\r\n\
        <Camera:DetectorBitDepth>16</Camera:DetectorBitDepth>\r\n\
        <Camera:IsNormalized>1</Camera:IsNormalized>\r\n\
        <FLIR:MAVVersionID>0.3.0.0</FLIR:MAVVersionID>\r\n\
        <FLIR:MAVComponentID>100</FLIR:MAVComponentID>\r\n\
        <FLIR:MAVRelativeAltitude>0/1000</FLIR:MAVRelativeAltitude>\r\n\
        <FLIR:MAVRateOfClimbRef>M</FLIR:MAVRateOfClimbRef>\r\n\
        <FLIR:MAVRateOfClimb>0/1000</FLIR:MAVRateOfClimb>\r\n\
        <FLIR:MAVYaw>0/100</FLIR:MAVYaw>\r\n\
        <FLIR:MAVPitch>0/100</FLIR:MAVPitch>\r\n\
        <FLIR:MAVRoll>0/100</FLIR:MAVRoll>\r\n\
        <FLIR:MAVYawRate>0/100</FLIR:MAVYawRate>\r\n\
        <FLIR:MAVPitchRate>0/100</FLIR:MAVPitchRate>\r\n\
        <FLIR:MAVRollRate>0/100</FLIR:MAVRollRate>\r\n\
        </rdf:Description>\r\n</rdf:RDF>'
        self.xmp = BeautifulSoup(rawxmp,features="lxml")
    
    def writeXmp(self):
        if not self.xmp:
            self.createXmp()
        xmp = [b'<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>',b'<?xpacket end="w"?>']
        xmp.insert(1,self.xmp.body.renderContents())
        xmpIFD = next((i for i in self.ExifIFD if i["name"]=="XMP"),False)
        if xmpIFD:
            xmpIFD["value"] = b''.join(xmp)
        else:
            self.ExifIFD.append({'name': 'XMP','id': 700,'type': 'Undefined','typeid': 7,'value':b''.join(xmp)})
        
    def extractXmp(self):
        try:
            self.xmp = BeautifulSoup(self.rawxmp,features="lxml")
            return self.xmp
        except:
            logging.warning("no XMP found", exc_info=True)
            
    def setXmpTag(self,tag,value):
        try:
            self.xmp.find(tag).string = name
        except:
            logging.error("XMP write error", exc_info=True)
        
    def set_ffheader(self, rawdatasize,headersize):
        #ffh ist: 64Byte FLIRFILEHEAD, dann 2x 32Byte FLIRFILEINDEX
        #das erste FFINDEX beschreibt die rawdaten
        ffh = bytearray(b"FFF\x00FLIR\x00\x00\x00\x00\x00\x00\x00\x00")
        ffh.extend(b"\x00\x00\x00\x00\x00\x00\x00\x65\x00\x00\x00\x40\x00\x00\x00\x02")
        ffh.extend(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        ffh.extend(b"\x00\x00\x00\x00\x00\x0A\x0F\x94\x00\x00\x00\x00\x00\x00\x00\x00")
        #ab hier FFINDEX Maintype 1 (RAWDATA=32Byte GeometricInfo + Rawdata (2*width*height))
        ffh.extend(b"\x00\x01\x00\x02\x00\x00\x00\x64\x00\x00\x00\x01\x00\x00\x00\x80")
        ffh.extend(struct.pack(self.endian["format"]+"4L",rawdatasize,0,0,0))
        #ab hier FFINDEX Maintype 32 (Metadata FFF)
        ffh.extend(b"\x00\x20\x00\x01\x00\x00\x00\x6B\x00\x00\x00\x01")
        ffh.extend(struct.pack(self.endian["format"]+"5L",rawdatasize+128,headersize,0,0,0))
        return ffh

    def set_geominfo(self, width,height,upperLeftX=0,upperLeftY=0,firstValidX=0,firstValidY=0):
        #am anfang vor den rawdaten kommt geometric info (32byte)
        geominfo = bytearray(b"\x02\x00")
        geominfo.extend(struct.pack("<4H",width,height,upperLeftX,upperLeftY))
        geominfo.extend(struct.pack("<4H",firstValidX,width-1,firstValidY,height-1))
        geominfo.extend(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        return geominfo

    def fff_segments(self, fffchunk):
        # hier wird der fff-datenblock zerteilt in 65524-Bytehaeppchen und auf APP1-Segmente aufgeteilt mit passendem Header
        # und anschliessend zusammengehaengt und zurueckgegeben
        blocksize = 65524
        Segments = [fffchunk[i:i+blocksize] for i in range(0, len(fffchunk), blocksize)]
        idx = self.find_segment("DQT")
        #print ("INDEX",idx)
        for k,i in enumerate(Segments):
            data = b"\xFF\xE1" + (len(i)+10).to_bytes(length=2, byteorder=self.endian["shortname"]) + \
                            b"FLIR\x00\x01" + k.to_bytes(length=1, byteorder=self.endian["shortname"]) + b"\x0A" + i 
            
            self.segments.insert(idx+k, {"id":'',"pos":'',
                                         "end":'',
                                        "segment":"APP1","type":b"FLIR",
                                        "data":data,
                                       "parent": 0, 
                                        "level": 0})
            
        #return b''.join(Segments)
        
            
    def find_segment(self,segmentname):
        idx = next((k for k,i in enumerate(self.segments) if i["segment"]== segmentname and i["level"]==0),None)
        if idx==None:
            logging.warning("Segment %s not found in this Jpeg." %segmentname)
        return idx
    
    def find_segment_type(self,stype, onlytoplevel = True, quiet=False):
        if onlytoplevel:
            idx = next((k for k,i in enumerate(self.segments) if i["type"]== stype and i["level"]==0),None)
        else:
            idx = next((k for k,i in enumerate(self.segments) if i["type"]== stype),None)
        if idx==None:
            if not quiet:
                logging.warning("Segment %s not found in this Jpeg." %stype)
        return idx
    
    def inject_segment(self,data,index,segment,stype,before=True):
        if not before:
            index += 1
            
        self.segments.insert(index, {"id":'',"pos":'',
                                         "end":'',
                                        "segment":segment,"type":stype,
                                        "data":data,
                                       "parent": 0, 
                                        "level": 0})
        
    def inject_fff(self,rawdata):
        if self.find_segment_type(b"FLIR",quiet=True):
            logging.error("This File has already Thermal RAW Data. Injection aborted")
            return
        fffchunk = self.set_ffheader(rawdata.shape[1]*rawdata.shape[0]*2+32,1126)
        geominfo = self.set_geominfo(rawdata.shape[1],rawdata.shape[0])
        raw = rawdata.tobytes()
        fff = b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
        fffchunk += geominfo + raw +fff
        self.fff_segments(fffchunk)

    def write(self,filename=None,rawexif=None):
        if filename == None:
            filename = self.filename
        out = []
        if not next((s for s in self.segments if s["type"]==b'Exif'),False):
            print("CREATE EXIF")
            exifcontent = self.assembleExif()
            exifraw = self.__writeExifHeader__(exifcontent)
            next((s for s in self.segments if s["segment"]==b'APP0'),False)
            pos,seg = next((k,i) for k,i in enumerate(self.segments) if i["segment"]=="APP0" )
            self.segments.insert(pos+1,{'id': pos+1,'segment': 'APP1','pos':seg["end"] ,'end': seg["end"]+len(exifraw),'type': b'Exif','parent': 0,'level': 0,'data': exifraw})
        #    print ("Ende",pos,seg)
        
        for s in self.segments :
            if s["level"]==0:
                if s["type"]==b'Exif': 
                    if rawexif==None:
                        exifcontent = self.assembleExif()
                        out.append(self.__writeExifHeader__(exifcontent))
                    else: 
                        out.append(rawexif)
                else:
                    out.append(s["data"])
        
        
        
            
        with open(filename,"wb") as f:
            f.write(b''.join(out))

