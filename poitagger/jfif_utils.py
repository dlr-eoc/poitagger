import piexif

from datetime import datetime,timedelta
import dateutil
from dateutil import tz
from fractions import Fraction
import re
import time


ResolutionUnit = {1:"None",2:"inches",3:"cm"}

def nested_set(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def alt(alt,ref):
    if ref == 1:
        return -rational2float(alt)
    else:
        return rational2float(alt)

def boolstr(myint):
    if int(myint) == 1:
        return "Yes"
    elif int(myint) == 0:
        return "No"
    else:
        return "Unknown"
        
def chroma(pos):
    if pos == 1:
        return "centered"
    elif pos == 2:
        return "cosited"
    else:
        return "invalid"

def bytes2tuple(mybytes,sep=b','):
    if hasattr(mybytes, '__iter__') and sep in mybytes:
        return tuple([int(i) for i in mybytes.split(sep)])
    

def isotimestr(timestamp, millisec,tz_minutes_offset):
    tz = dateutil.tz.tzoffset(None, -tz_minutes_offset*60)
    fulltime = datetime.fromtimestamp(timestamp, tz) 
    fulltime += timedelta(milliseconds=millisec)
    print(millisec,tz_minutes_offset,timestamp)
    return str(fulltime)
        
    
def float2rational(number,string=False):
    """convert a number to rantional
    Keyword arguments: number
    
    return: tuple like (1, 2), (numerator, denominator)
    """
    f = Fraction(str(number)).limit_denominator(100000000)
    if string:
        return "{}/{}".format(f.numerator, f.denominator)
    else:
        return (f.numerator, f.denominator)
    
def convert_rational(rational):
    rational_str = str(rational)
    p = re.compile(r'[\(, \)]+|[\[, \]]+')
    Lst1 = p.split(rational_str)[1:-1]
    Lst2 = []
    for i in Lst1:
        try:
            Lst2.append(int(i))
        except ValueError:
            Lst2.append(evaldiv(i))
    return Lst2


def evaldiv(string):
        splitted = str(string).split("/")
        if len(splitted)>2: 
            raise Exception("too many '/' in string")
        elif len(splitted)== 2:
            zaehler, nenner = splitted 
        else:
            zaehler, nenner = splitted[0], 1
        if float(nenner) != 0:    
            return float(zaehler) / float(nenner)
        return float(zaehler)
           
        
def rational2float(rational):
    floatlist = []
    for i in rational:
        if type(i)==tuple and len(i)==2:
            if all([type(j) == int for j in i]):
                floatlist.append(i[0]/i[1])
        elif type(i)!=int:
            return rational
    if len(rational)==2 and all([type(j) == int for j in rational]):
        if rational[1] == 0: return rational
        return rational[0]/rational[1]
    if len(floatlist)==0:
        return rational
    return tuple(floatlist)

    
def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60);
    if direction in ['W',b'W'] or direction in ['S',b'S']:
        dd *= -1
    return dd;

def resolution(meta):
            xresolution = rational2float(meta.get(piexif.ImageIFD.XResolution,-1))
            yresolution = rational2float(meta.get(piexif.ImageIFD.YResolution,-1))
            unit = ResolutionUnit[meta.get(piexif.ImageIFD.ResolutionUnit,1)]
            return {"x":xresolution,"y":yresolution,"unit":unit}
    

def UTCFromGps(gpsWeek, mSOW, leapSecs=16,gpxstyle=False): 
    """
    mSOW = milliseconds of week 
    gpsWeek is the full number (not modulo 1024) 
    """ 
    secFract = mSOW % 1000 
    epochTuple = (1980, 1, 6, 0, 0, 0) + (-1, -1, 0)  
    t0 = time.mktime(epochTuple) - time.timezone  #mktime is localtime, correct for UTC 
    tdiff = (gpsWeek * 604800) + mSOW/1000.0 - leapSecs 
    t = t0 + tdiff 
    (year, month, day, hh, mm, ss, dayOfWeek, julianDay, daylightsaving) = time.gmtime(t) 
    if gpxstyle==True:
        return "%04d-%02d-%02dT%02d:%02d:%02d"%(year,month,day,hh,mm,ss)
    else:
        return "%04d-%02d-%02d %02d:%02d:%02d"%(year,month,day,hh,mm,ss)


            