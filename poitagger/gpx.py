from lxml import etree
import os

class GpxGenerator(object):
    latmin = None
    latmax = None
    lonmin = None
    lonmax = None
    def __init__(self,path,session="None"):
        if os.path.isdir(path):
            self.create(path,session)
        else:
            self.load(path,session)
        
    def create(self,path,session="None"):
        self.root = etree.Element("gpx")
        self.fwr = etree.SubElement(self.root, "fwr")
        etree.SubElement(self.fwr,"session").text = session
        #print path
        etree.SubElement(self.fwr,"path").text = path
        self.path = path
        
    def rename_path(self,path):
        etree.SubElement(self.fwr,"path").text = path
        self.path = path
        
    def add_wpt(self,lat,lon,ele,time,name,type,desc="",src="",cmt=""):
        wpt = etree.SubElement(self.root, "wpt")
        wpt.set("lat",lat )
        wpt.set("lon",lon)
        if self.latmin == None: self.latmin = lat
        if self.latmax == None: self.latmax = lat
        if self.lonmin == None: self.lonmin = lon
        if self.lonmax == None: self.lonmax = lon
        if lat < self.latmin: self.latmin = lat
        if lat > self.latmax: self.latmax = lat
        if lon < self.lonmin: self.lonmin = lon
        if lon > self.lonmax: self.lonmax = lon
        etree.SubElement(wpt, "name").text = name
        etree.SubElement(wpt, "cmt").text = cmt
        etree.SubElement(wpt, "time").text = time
        etree.SubElement(wpt, "ele").text = ele
        etree.SubElement(wpt, "type").text = type
        etree.SubElement(wpt, "desc").text = desc
        etree.SubElement(wpt, "src").text = src
    
    def add_imglist(self,imglist):
        imgs = etree.SubElement(self.root, "images")
        for i in imglist:
            img = etree.SubElement(imgs, "image")
            img.set("id",str(i["id"]))
            img.set("label",i["filename"])
        
    def load(self,filename,session="None"):
        self.path,file = os.path.split(os.path.abspath(filename))
        try:
            with open(filename,"r") as filehandler:
                tree = etree.parse(filehandler)
            self.root = tree.getroot()    
            self.fwr = self.root.find("fwr")
            self.fwr.find("path").text = self.path
        except:
            self.create(self.path,session)
            
    def save(self,filename,bounding=True):
        #print "save gpx",os.path.join(self.path,filename),str(self.get_bounding())
        if bounding:
            etree.SubElement(self.fwr,"bounding").text = str(self.get_bounding())
            
        with open(os.path.join(self.path,filename),"w") as f:
            f.write(etree.tostring(self.root, xml_declaration=True, encoding="utf-8", pretty_print=True ).decode("utf-8"))
    
    def printtree(self):
        print(etree.tostring(self.root, xml_declaration=True, encoding="utf-8", pretty_print=True ).decode("utf-8"))
    def get_bounding(self):
        return self.latmin,self.lonmin,self.latmax,self.lonmax
    def clear(self):
        self.root.clear()
        
def main():
    import meta as mt

    path = "C:\\WILDRETTER\\2014_DLR\\Flug013_2014-03-22_11-17\\FlirSD"
    gg = GpxGenerator(path)
    
    for file in sorted(os.listdir(path)):
        (base,ext) = os.path.splitext(file)
        if ext ==".txt":
            meta = mt.Meta()
            meta.load(os.path.join(path,file))
            md = meta.to_dict()
            if md["gps-date"]:
                time = "%sT%s" %(md["gps-date"],md["gps-utc-time"])
                if (md["lat"] == 0 and md["lon"] == 0): continue
                gg.addwpt(md["latlon"],md["height"],time,base,"uavpos")
                
    gg.save("imagepos.gpx")
    
if __name__ == "__main__":
    main()
        
        
