
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
b"\xff\xc8":"JPG"  ,
b"\xff\xf0":"JPG0" ,
b"\xff\xfd":"JPG13",
b"\xff\xcc":"DAC"  , # Define Arithmetic Table, usually unsupport 
b"\xff\xdc":"DNL"  ,
b"\xff\xdd":"DRI"  , # Define Restart Interval
b"\xff\xde":"DHP"  ,
b"\xff\xdf":"EXP"  ,
b"\xff\xd0":"RST0" ,  # RSTn are used for resync, may be ignored
b"\xff\xd1":"RST1" ,
b"\xff\xd2":"RST2" ,
b"\xff\xd3":"RST3" ,
b"\xff\xd4":"RST4" ,
b"\xff\xd5":"RST5" ,
b"\xff\xd6":"RST6" ,
b"\xff\xd7":"RST7" ,
    
b"\xff\x01":"TEM"  ,
b"\xff\xfe":"COM"  } # Comment
# ffd9 is end of image
           
    

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
# b"\xff\xda":"SOS"  ,  # Start of Scan
    
MARKER_2BYTE_REV = {y:x for x,y in MARKER_2BYTE.items()}

MARKER_REV = {y:x for x,y in MARKER.items()}

ExifCompression = {
    0    :"Unknown",
    1    :"Uncompressed",
    2    :"CCITT 1D",
    3    :"T4/Group 3 Fax",
    4    :"T6/Group 4 Fax",
    5    :"LZW",
    6    :"JPEG (old-style)",
    7    :"JPEG",
    8    :"Adobe Deflate",
    9    :"JBIG B&W",
    10   :"JBIG Color",
    99   :"JPEG",
    262  :"Kodak 262",
    32766:"Next",
    32767:"Sony ARW Compressed",
    32769:"Packed RAW",
    32770:"Samsung SRW Compressed",
    32771:"CCIRLEW",
    32772:"Samsung SRW Compressed 2",
    32773:"PackBits",
    32809:"Thunderscan",
    32867:"Kodak KDC Compressed",
    32895:"IT8CTPAD",
    32896:"IT8LW",
    32897:"IT8MP",
    32898:"IT8BL",
    32908:"PixarFilm",
    32909:"PixarLog",
    32946:"Deflate",
    32947:"DCS",
    33003:"Aperio JPEG 2000 YCbCr",
    33005:"Aperio JPEG 2000 RGB",
    34661:"JBIG",
    34676:"SGILog",
    34677:"SGILog24",
    34712:"JPEG 2000",
    34713:"Nikon NEF Compressed",
    34715:"JBIG2 TIFF FX",
    34718:"Microsoft Document Imaging (MDI) Binary Level Codec",
    34719:"Microsoft Document Imaging (MDI) Progressive Transform Codec",
    34720:"Microsoft Document Imaging (MDI) Vector",
    34887:"ESRI Lerc",
    34892:"Lossy JPEG",
    34925:"LZMA2",
    34926:"Zstd",
    34927:"WebP",
    34933:"PNG",
    34934:"JPEG XR",
    65000:"Kodak DCR Compressed",
    65535:"Pentax PEF Compressed"}


ExposureProgram =  {
    0 : "Not defined",
    1 :"Manual",
    2 :"Normal",
    3 :"Aperture priority",
    4 :"Shutter priority",
    5 :"Creative",
    6 :"Action",
    7 :"Portrait",
    8 :"Landscape"
}



AnafiRawImageMeta = [[0x11,"Raw Image Height", "I"],
        [0x16,"Raw Image Width", "I"],
        ]
        

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