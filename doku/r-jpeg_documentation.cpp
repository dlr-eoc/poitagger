FFF_TAGID_BasicData = 0x20,

struct _bidata_t 
{
    GEOMETRIC_INFO_T    GeometricInfo; // 32 bytes = 0x20
    OBJECT_PAR_T        ObjectParameters; // 48 bytes = 0x30
    TEMP_CALIB_T        CalibParameters; // 132 bytes = 0x84
    BYTE		        CalibInfo[564];  // 564 bytes = 0x234
    ADJUST_PAR_T        AdjustParameters;  // 48 bytes = 0x30
    PRES_PAR_T	        PresentParameters; // 
    BYTE				DisplayParameters[28];
    IMAGEINFO_T         ImageInfo;
    DISTR_DATA_T        DistributionData;
};

typedef struct _geometric_info_t
{
                                  /** Size of one pixel in bytes.
                                      Normal size is 2 bytes (16 bit pixels)
                                      or 3 (for colorized YCbCr pixels) */
0x00 *  unsigned short pixelSize;

0x02    unsigned short imageWidth;    //!< Image width in pixels
0x04    unsigned short imageHeight;   //!< Image height in pixels

                                  /** @name Upper left coordinates
                                      X and Y coordinates for upper left corner 
                                      relative original in case this image is a
                                      cutout, normally 0 */
                                  /*@{*/
0x06    unsigned short upperLeftX;   
0x08    unsigned short upperLeftY;    
                                  /*@}*/ 
         
                                  /** @name Valid pixels
                                      The following four number identifies the
				      valid pixels area within the image. 
				      Sometimes the first row and column only 
				      contains calibration pixels that should not
				      be considered as real pixels */
                                  /*@{*/ 
0x0A    unsigned short firstValidX;   //!< Normally 0
0x0C    unsigned short lastValidX;    //!< Normally imageWidth - 1
0x0E    unsigned short firstValidY;   //!< Normally 0
0x10    unsigned short lastValidY;    //!< Normally imageHeight - 1
                                  /*@}*/ 
0x12    unsigned short detectorDeep;  //!< Number of bits from detector A/D
    
                                  /** Type of detector to be able to differ
                                      between technologies if necessary. 
                                      Defined in AppCore/core_imgflow/imgflow_state.hpp */
0x14    unsigned short detectorID;
                                  /**  Type of upsampling from Detector to IR pixels.
                                       Defined in AppCore/core_imgflow/imgflow_state.hpp */
0x16    unsigned short upSampling;
0x18    unsigned short frameCtr;      //!< Image number from frame buffer                                  
0x1A    unsigned short minMeasRadius; //!< See AppCore/core_imgflow/imgflow_state.hpp for reference
0x1C    unsigned char  stripeFields;  //!< Number of striped fields this image consists of
0x1D    unsigned char  reserved;      //!< For future use - should be set to 0
0x1E    unsigned short reserved1;     //!< For future use - should be set to 0
} GEOMETRIC_INFO_T;               //!< sizeof struct == 32 bytes

struct OBJECT_PAR_T 
{
0x20 *  float emissivity;            //!< 0 - 1
0x24 *  float objectDistance;        //!< Meters
0x28 *  float ambTemp;               //!< degrees Kelvin
0x2c *  float atmTemp;               /**< degrees Kelvin 
                                      - should be set == ambTemp for basic S/W */

0x30 *  float extOptTemp;            /**< degrees Kelvin 
                                      - should be set = ambTemp for basic S/W */
0x34 *  float extOptTransm;          //!< 0 - 1: should be set = 1.0 for basic S/W
0x38    float estAtmTransm;          //!< 0 - 1: should be set = 0.0 for basic S/W

0x3C *  float relHum;                //!< relative humidity
0x40    long reserved[4];            //!< For future use - should be set to 0
};                               //!< sizeof struct == 48 bytes = 0x30

struct TEMP_CALIB_T 
{
0x50    long  Reserved1[2];  // size 0x08
0x58 *  float R;                      //!< Calibration constant R
0x5C *  float B;                      //!< Calibration constant B
0x60 *  float F;                      //!< Calibration constant F

0x64    long  Reserved2[11];  // size 44 = 0x2C reserved for AtmosphericTrans !!!

0x90 *  float tmax;                   //!< Upper temp limit [K] when calibrated for
			                   	  //!<   current temp range
0x94 *  float tmin;                   //!< Lower temp limit [K] when calibrated for
				                  //!<   current temp range
0x98 *  float tmaxClip;               //!< Upper temp limit [K] over which the
                                  //!<   calibration becomes invalid
0x9c *  float tminClip;               //!< Lower temp limit [K] under which the
                                  //!<   calibration becomes invalid
0xA0 *  float tmaxWarn;               //!< Upper temp limit [K] over which the
                                  //!<   calibration soon will become invalid
0xA4 *  float tminWarn;               //!< Lower temp limit [K] under which the
                                  //!<   calibration soon will become invalid
0xA8 *  float tmaxSaturated;          //!< Upper temp limit [K] over which pixels 
                                  //!<   should be presented with overflow color
0xAC *  float tminSaturated;          //!< Lower temp limit [K] for saturation 
                                  //!<   (see also ADJUST_PAR_T:ipixOverflow). 
                                  //!<   ipix over/under flow should be calculated
                                  //!<   by imgsrc from tmin/maxSaturated.
                                  //!<   LUT handler should look at ipix
                                  //!<   over/underflow.
0xB0    long Reserved3[9];  // size 36 = 0x24
};                                //!< sizeof struct == 132 bytes = 0x84


struct CalibInfo
{                                
0xD4 *  BYTE		        CalibInfo[564];  // 564 bytes = 0x234
} CalibInfo;                                //!< sizeof struct == 132 bytes = 0x84


typedef struct _adjust_par_t {
0x308 *  long  normOffset;                 /* Temperature compensation offset  !!!! PlanckO !!!!
                                         (globalOffset) */
0x30C *  float normGain;                   /* Temperature compensation gain    !!!! PlanckR2 !!!!
                                         (globalGain) */ 
0x30E    unsigned short ipixUnderflow; /* Image pixel underflow limit */
0x310    unsigned short ipixOverflow;  /* Image pixel overflow limit */
0x314    long Reserved2[9];
} ADJUST_PAR_T;                   /* sizeof struct == 48 bytes = 0x30 */


typedef struct _pres_par_t {
0x338 *  signed long level;           /* Level as normalized pixel value (apix), Level is defined as middle of 
				                    span (in pixel units) */
0x33C *   signed long span;            /* Span as normalized pixel value (apix) */
0x340	BYTE reserved[40];           // 0x28
} PRES_PAR_T;                    /* sizeof struct == 48 bytes = 0x30 */


typedef struct DisplayParameters {
0x368    BYTE				DisplayParameters[28];
} DisplayParameters;   /* sizeof struct == 28 bytes = 0x1C */


struct IMAGEINFO_T
{
0x384 *  unsigned long imageTime;      //!< Time in seconds since 1970-01-01 00:00 (UTC)
0x388    unsigned long imageMilliTime; //!< Milliseconds since last second

0x38C    short timeZoneBias;           //!< Time zone bias in minutes
                                  //!    UTC = local time + bias
0x38E    short swReserved1;            //!< filler == 0
0x390 *  long focusPos;                //!< Focus position as counter value
0x394    float fTSTemp[7];     // 0x1C      !< Temp sensor values converted to Kelvin
0x3B0    float fTSTempExt[4];  // 0x10      !< Lens temp sensors et.c. Converted to Kelvin
0x3C0    unsigned short trigInfoType;  //!< 0 = No info, 1 = THV 900 type info
0x3C2    unsigned short trigHit;       //!< hit count - microsecs from trig
                                  //!    reference
0x3C4    unsigned short trigFlags;     //!< trig flags, type dependent
0x3C6    unsigned short reserved1;
0x3C8    unsigned long  trigCount;     //!< trig counter
0x3CB    short manipulType;            //!< defines how to interpret manipFactors
0x3CE    short manipFactors[5];        //!< Used average factors
    /** Detecor settings - camera type dependent */
0x3D8    long detectorPars[20];        //!< Currently used detector parameters like  
                                  //!    used bias, offsets. Usage is camera
                                  //!    dependent
0x428    long reserved[5];             //!< For future use
    
};                                //!< sizeof struct == 184 bytes = 0xB8 
 

struct DISTR_DATA_T
{
    /** Framegrab independent distribution data */
0x43C    char imgName[16];  /* (4 longs) */
    
0x44C    unsigned short distrLive;         //!< TRUE (1) when image distribution is
				      //!	'LIVE'. FALSE (0) otherwise
0x44E    unsigned short distrRecalled;     //!< TRUE (1) when image distribution is
                                      //!       recalled. FALSE (0) otherwise.
                                      //!< TRUE also implies that distrLive ==
                                      //!       FALSE
0x450    long curGlobalOffset;
0x454    float curGlobalGain;              //!< globalOffset/Gain to generate LUT from
                                      //!  updated continously when live only
#define regulationOn 1
0x458    unsigned short regulMethodMask;   //!< Method used for o/g calculation  
0x45A    unsigned short visualImage;       //!< TRUE (1) for TV (visual)
                                      //!  FALSE (0) for IR image
0x45C *  float focusDistance;              //!< focusDistance in meters.
				      //!    0 means not defined.
				      //!    NOT calculated by image source

0x460    unsigned short StripeHeight;      //!< 0 = not striped
0x462    unsigned short StripeStart;       //!< Striping start line if striped
0x464 *  unsigned short imageFreq;         //!< Image frequency, defines the nominal
                                      //!    image frequency in Hz
0x466    unsigned short typePixStreamCtrlData;
                                      //!< 0 = no such data,
                                      //!    other types TBD
0x468    unsigned short PixStreamDataLine;
                                      //!< At which line to find
                                      //!    PixStreamCtrlData if any

#define IMGSMSK_NUC       0x20	      //!< Bit set means that NUC is in progress

0x46A    short errStatus;                  //!< bit field, mask definitions above
    
0x46C    unsigned short imageMilliFreq;    //!< Image frequency, milliHz part of imageFreq
    
0x46E    short reserved;                   //!< For future use
0x470    long reserved2[3];
};                                    //!< sizeof struct == 64 bytes = 0x40
