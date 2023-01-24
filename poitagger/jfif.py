import struct
from tags import *

class JFIF(object):
    """
    This is a Class for Image file data extraction. Many images are organized in segments as the JFIF or the newer Exif standard describes it.
    There are so called segments with names like APP0 , APP1 SOS DQT and so on. 
    have a look at https://de.wikipedia.org/wiki/JPEG_File_Interchange_Format for more details
    """
    rawdata = b''
    
    def all_segments(self,data):
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
        seemless = True
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
            
            if len(segments)>0:
                seemless = True if m.start() == segments[-1]["end"] else False
                
            segments.append({"id":id,
                "segment": segment,
                "pos":m.start(),
                "end" : m.start()+seg_length+2,
                "type": seg_type,             
                "parent": parent, 
                "level": level, 
                "seemless": seemless,             
                "data": data[m.start() : m.start() + seg_length+2]   })
            id += 1
        return segments

    def main_segments(self,data=None):
        Seg = []
        pos = 0
        if not data == None:
            self.rawdata = data
            
        while True:
            current = pos
            pos = self.rawdata.find(b"\xFF",current)
            if pos == -1: break
            marker = self.rawdata[pos:pos+2]
            if marker in MARKER.keys():
                name = MARKER[marker]
                length = self.rawdata[pos+2:pos+4]
                pos = pos + 256 * length[0] + length[1] + 2
                Seg.append((current,name,pos))     
            elif marker in MARKER_2BYTE.keys():
                name = MARKER_2BYTE[marker]
                pos = pos + 2
                Seg.append((current,name,pos)) 
            else:
                pos = pos + 1
                if marker == b"\xff\xda": # Start of Scan has not a known length
                    Seg.append((current,"SOS",pos)) 
        self.segments = Seg
        return Seg

    def decode_struct(self,rawdata,structure,endian="<",strip=False):    
        params = {}
        for i in structure:
            val = struct.Struct(endian+i[2]).unpack_from(rawdata,i[0])[0]
            name = i[1]
            if strip and i[2][-1]=="s": 
                val = val.strip(b"\x00")
            params[name]=val
        return params    
    