from __future__ import print_function
from . import utils2
from . import meta as mt

import time
import datetime
import logging

import pyqtgraph as pg  
from pyqtgraph.Qt import QtCore,QtGui,uic
import os
import sys
import PIL
import shutil

#import flirsd
from .image import Image
import traceback
from . import PATHS     
   
class Araloader(QtCore.QThread):   
    log = QtCore.pyqtSignal(str)
    critical = QtCore.pyqtSignal(str)
    info = QtCore.pyqtSignal(str)
    
    progress = QtCore.pyqtSignal(int)
    outdirlist = []    
    eigeneConf = False
    
    # def __init__(self):
        # super().__init__()
        # self.settings = QtCore.QSettings(PATHS["CONF"], QtCore.QSettings.IniFormat)
        # self.settings.setFallbacksEnabled(False) 
        
    def readSDCard(self,dialog,settings):
        sdcardname = "IR_"
        remove = dialog.SDCard_leeren.checkState()
        flying = dialog.nurFlugBilder.checkState()
        #founddir = "d:/test"
       # founddir = utils2.getSDCardPath(sdcardname)
       # if founddir:
       #     self.log.emit("Karte eingesteckt in Laufwerk:" + founddir)
       # else:
       #     self.log.emit("Keine gueltige Karte gefunden")
       #     self.critical.emit("Keine gueltige Karte gefunden, die mit \"%s\" anfaengt!"%sdcardname)
       #     return
        self.type = "SDCard"
        founddir=str(dialog.sourceLE.text())
        outdir = self.prepare(settings,founddir,remove_images=remove,only_flying=flying)  
        
        dialog.st(settings.value("SDCARD/device"),outdir,"")
        ok = dialog.exec_()
        
        if ok == True:
            self.outdir=str(dialog.pathBox.text())
            self.name = str(dialog.nameBox.text())
            self.start()
        else:
            pass
    def readFolder(self,indir,eigeneConf=False):
        print("read Folder")
        self.log.emit("readFolder"+indir)
        self.type = "Folder"
        self.indir = indir
        self.eigeneConf = eigeneConf
        self.start()
    
    def convertFolderJpg(self,indir):
        self.log.emit("convertFolder"+indir)
        self.type = "ConvertJpg"
        self.indir = indir
        self.start()
    
    def createSubimages(self,indir,parameter):
        """
        parameter contains the image processing parameters for detecting the blobs.
        
        """
        self.log.emit("createSubimages in Folder "+indir)
        self.type = "CreateSubimages"
        self.indir = indir
        self.parameter = parameter
        
        self.start()
    
    
    def prepare(self, settings, indir, remove_images=False, year=None, only_flying=False):
        self.settings = settings
        self.indir = str(indir)
        self.remove_images = remove_images
        self.only_flying = only_flying
        self.year = int(time.strftime("%y"))%10 if year == None else year
        print(type(self.settings))
        self.flugnr = int(float(self.settings.value("SYSTEM/flightcounter",0)))
        self.owner_id = self.settings.value("SYSTEM/owner_id","X")
        outdir = self.settings.value("PATHS/rootdir", os.path.join(self.indir,"outdir"))
        self.outdir = str(outdir)
        print(outdir)
        return outdir
        
    def run(self):
        """
        this moves the files of the SD-Card (indir) to the outdir and 
        merges them to the folders "FlugXXX/FlirSD" where XXX are ascending integers.   
        """
        print("run")
        if self.type=="Folder":
            print("Folder")
            self.FolderRead()
        elif self.type=="SDCard":
            print("SDCard")
            self.SDCardRead()
        elif self.type=="ConvertJpg":
            print("ConvertJpg")
            self.ConvertJpg()
        elif self.type=="CreateSubimages":
            print("Create Subimages")
            self.CreateSub()
        
    def CreateSub(self):
        prog = 0.0
        for root, dirs, files in sorted(os.walk(self.indir)):
            (updir,dirbase) = os.path.split(root)
            imgamount = len(files)
            self.log.emit("files"+str(files))
            for name in sorted(files):
                (base,ext) = os.path.splitext(name) 
                prog += 1.0
                if ext.lower() not in [".raw",".ara",".ar2"]: continue
                try:
                    self.infile = os.path.join(root,name)
                    raw = Image.factory(self.infile)
                    self.log.emit(self.infile)
                    
                except:
                    traceback.print_exc()
                self.progress.emit(int(prog/imgamount*100))
        
                    
    def ConvertJpg(self):
        prog = 0.0
        for root, dirs, files in sorted(os.walk(self.indir)):
            (updir,dirbase) = os.path.split(root)
            imgamount = len(files)
            self.log.emit("files"+str(files))
            for name in sorted(files):
                (base,ext) = os.path.splitext(name) 
                prog += 1.0
                if ext.lower() not in [".raw",".ara",".ar2"]: continue
                try:
                    self.infile = os.path.join(root,name)
                    raw = Image.factory(self.infile)
                    self.log.emit(self.infile)
                    outfile = os.path.join(root,"%s.jpg"%(base))
                    outtxt = os.path.join(root,"%s.txt"%(base))
                    outgray = raw.normalize()
                    
                    PIL.Image.fromarray(outgray).save(outfile)
                    #cv2.imwrite(outfile,outgray)
                    
                    meta = mt.Meta()
                    meta.from_flirsd(raw.rawheader)
                    meta.update("CAMERA", "homogenized", "Falstracebacke")
                    md = meta.to_dict()
                    
                    meta.save(outtxt)
                    
                    
                except:
                    traceback.print_exc()
                self.progress.emit(int(prog/imgamount*100))
        
        
    def FolderRead(self): #das ist nur fuer ara korrigieren!!!
        self.flugnr = 1
        self.s_latlon = {"flugnr" : None, "lat": None, "lon": None, "ele": None }
        lastraw = None
        prog = 0.0
        self.log.emit("start folder read")
        for root, dirs, files in sorted(os.walk(self.indir)):
            (updir,dirbase) = os.path.split(root)
            imgamount = len(files)
            self.log.emit("files"+str(files))
            for name in sorted(files):
                (base,ext) = os.path.splitext(name) 
                prog += 1.0
                if ext.lower() not in [".raw",".ara",".ar2"]: continue
                
                try:
                    self.infile = os.path.join(root,name)
                    raw = Image.factory(self.infile)
                    settings = self.find_settings(raw) 
                    self.fill_presets(settings,raw)
                    self.correct_start_latlon(raw)
                    if lastraw is not None:
                        self.compare_with_last(raw,lastraw)
                    lastraw = raw
                    self.log.emit(self.infile)
                    raw.saveraw(self.infile)
                except:
                    traceback.print_exc()
                self.progress.emit(int(prog/imgamount*100))
        print(self.outdirlist)
     
    def readnonAsctecSDCard(self):
        for root, dirs, files in sorted(os.walk(self.indir)):
            for file in files:
                if os.path.splitext(file)[1].lower() not in image.SUPPORTED_EXTENSIONS: continue
                print(file)
                #shutil.copy(os.path.join(root,file),self.outdir)
    def SDCardRead(self):
        self.flugnr = time.time()
        self.s_latlon = {"flugnr" : None, "lat": None, "lon": None, "ele": None }
        lastfile = 0
        lastraw = None
        prog = 0.0
        self.outdirlist = []
        print("IN",self.indir)
        try:
            foldersamount = len([name for name in os.listdir(self.indir) if name[:4]=="FLIR"])
            print ("FOLDERS",foldersamount)
        except:
            self.readnonAsctecSDCard()
            return
        print("start",self.indir)
        
        self.empty = True
        
        try:
            for root, dirs, files in sorted(os.walk(self.indir)):
                (updir,dirbase) = os.path.split(root)
                if not (dirbase[:4]=="FLIR"): continue
                self.prepare_path("",lastfile)
                for name in sorted(files): 
                    print("name",name)
                    (base,ext) = os.path.splitext(name) 
                    if ext.lower() not in [".raw",".ara"]: continue
                    self.infile = os.path.join(root,name)
                    if self.is_not_flying(): continue
                    if (int(base)<lastfile): # !!!!!!!!!!!!!!!! here the first flight ends !!!!!!!!!!!!!!!!!!!!
                        self.rename_files()
                        self.flugnr = time.time()
                    lastfile = int(base)
                    try:
                        raw = Image.factory(self.infile)
                        
                    except:
                        print("ConvertRaw fehlgeschlagen")
                        continue
                    settings = self.find_settings(raw) 
                    self.fill_presets(settings,raw)
                    self.correct_start_latlon(raw)
                    if lastraw is not None:
                        self.compare_with_last(raw,lastraw)
                    lastraw = raw
                    outfilepath = self.prepare_path(name,lastfile)
                    if not (raw.header.start_lat,raw.header.start_lon) == (0,0):
                        self.empty = False
                    raw.saveraw(outfilepath)
                    if self.remove_images:
                        os.remove(self.infile)
                
                prog += 1.0
                self.progress.emit(int(prog/foldersamount*100))
                if len(files)==0: continue
            self.rename_files()
            self.settings.setValue("SYSTEM/flightcounter",str(self.flugnr))
            if self.remove_images:
                for root, dirs, files in os.walk(self.indir):
                    for d in dirs:
                        if d[:4]=="FLIR":
                            shutil.rmtree(os.path.join(root, d))
            
            self.info.emit("Das Einlesen der SD-Karte war erfolgreich!") 
            
        except IndexError:
            try:
                shutil.copytree(self.indir,self.outdir)
            except:
                self.critical.emit("SD-Karte einlesen fehlgeschlagen: SD-Karte scheint leer zu sein")
          
                logging.error("SD einlesen error",exc_info=True)
         
            
        except:
            (type, value, traceback) = sys.exc_info()
            sys.excepthook(type, value, traceback)
            self.critical.emit("SD-Karte einlesen fehlgeschlagen: %s "%value)
                
    def find_settings(self,raw):
        camser = str(raw.rawheader["camera"]["sernum"])  
        camserlist = [os.path.splitext(i)[0] for i in os.listdir(PATHS["CALIB"]) if os.path.splitext(i)[1] == ".ini"]
        if camser in camserlist:
            settings = QtCore.QSettings(os.path.join(PATHS["CALIB"],camser + ".ini"), QtCore.QSettings.IniFormat)
        else:
            settings = QtCore.QSettings(os.path.join(PATHS["CALIB"],"default.ini"), QtCore.QSettings.IniFormat)
        
        if self.eigeneConf:
            settings = self.eigeneConf
        return settings
        
    def rename_files(self): #hier muss noch ueberprueft werden, ob das auch fuer mehrere Fluege auf einer SD-Karte geht!!!!!!
        first = True
        utc = [1980,1,1,0,0,0]
        space = "_"
        for root, dirs, files in sorted(os.walk(self.outdirlist[-1])):
            for name in sorted(files,reverse=True):
                infile = os.path.join(root,name)
                (base,ext) = os.path.splitext(name) 
                if ext.lower() not in [".raw",".ara",".ar2"]: continue
                if first:
                    raw = Image.factory(infile)
                    utc = raw.header.utc
                    first = False
                    if utc[0]==1980:
                        x = datetime.datetime.now()
                        space = "x" # this time is the downloadtime, not the capturetime
                        utc = [x.year,x.month,x.day,x.hour,x.minute,x.second]
                try:    
                    outfile = os.path.join(root,"%02d%02d%02d%02d%c%04d%s"%(utc[1],utc[2],utc[3],utc[4],space,int(base),ext))
                    os.rename(infile, outfile)
                except:
                    traceback.print_exc()
        if first:
            x = datetime.datetime.now()
            space = "x" # this time is the downloadtime, not the capturetime
            utc = [x.year,x.month,x.day,x.hour,x.minute,x.second]
        base2, name2 = os.path.split(self.outdirlist[-1])  
        name2new = "%02d-%02d-%02d_%02d-%02d%c%s" %(utc[0],utc[1],utc[2],utc[3],utc[4],space,self.name)
        outdir = os.path.join(base2,name2new)
        try:
            os.rename(self.outdirlist[-1], outdir)
        except:
            for i in range(1,999):
                pathnew = "%s(%d)"%(outdir,i)
                if not os.path.exists(pathnew):
                    os.rename(self.outdirlist[-1], pathnew)
                    break
            traceback.print_exc()
        
            
    def is_not_flying(self):
        if self.only_flying:
            if not utils2.is_flying(self.infile):
                return True
        return False
        
    def prepare_path(self,name,currentfilenr):
        
        odf = os.path.join(str(self.outdir),"%d%c%s"%(self.year,self.owner_id,self.flugnr))
        if not os.path.exists(odf):
            os.makedirs(odf)
            self.log.emit("Outdir:"+ odf) 
            self.outdirlist.append(odf)
        
        outfilename = "%04d.ARA" %(currentfilenr)
        outfilepath = os.path.join(odf, outfilename)
    
        self.log.emit("%s -> %s"%(name,outfilename))
        return outfilepath 
    
    def correct_start_latlon(self,raw):
        if not (raw.rawheader["startup_gps"]["lat"],raw.rawheader["startup_gps"]["long"]) == (0,0):
            if not self.s_latlon["flugnr"] == self.flugnr:
                self.s_latlon["flugnr"] = self.flugnr
                self.s_latlon["lat"] = raw.rawheader["startup_gps"]["lat"]
                self.s_latlon["long"] = raw.rawheader["startup_gps"]["long"]
                self.s_latlon["ele"] = raw.rawheader["startup_gps"]["height"]
            elif not (raw.rawheader["startup_gps"]["lat"],raw.rawheader["startup_gps"]["long"]) == (self.s_latlon["lat"],self.s_latlon["long"]):
                raw.rawheader["startup_gps"]["lat"] = self.s_latlon["lat"]
                raw.rawheader["startup_gps"]["long"] = self.s_latlon["long"]
                raw.rawheader["startup_gps"]["height"] = self.s_latlon["ele"]
                raw.rawheader["dlr"]["changed_flags"] |= image.CHANGEDFLAGS.START_LATLON
        #raw.fill_header()
        
    def compare_with_last(self,raw,last):
        if raw.rawheader["falcon"]["gps_time_ms"]==last.rawheader["falcon"]["gps_time_ms"]:
            raw.rawheader["dlr"]["error_flags"] |= image.ERRORFLAGS.ALL_META
        if utils2.differs_more(raw.rawheader["falcon"]["gps_lat"],last.rawheader["falcon"]["gps_lat"],4000): # ca. 40 m 
            raw.rawheader["dlr"]["error_flags"] |= image.ERRORFLAGS.LATLON
        if utils2.differs_more(raw.rawheader["falcon"]["gps_long"],last.rawheader["falcon"]["gps_long"],4000): # ca. 40 m
            raw.rawheader["dlr"]["error_flags"] |= image.ERRORFLAGS.LATLON
        if (utils2.differs_more(raw.rawheader["falcon"]["gps_lat"],last.rawheader["falcon"]["gps_lat"],40000) or \
        utils2.differs_more(raw.rawheader["falcon"]["gps_long"],last.rawheader["falcon"]["gps_long"],40000)) and \
        (not last.rawheader["falcon"]["gps_long"]  == 0 and not last.rawheader["falcon"]["gps_lat"] == 0) and \
        (not last.rawheader["dlr"]["error_flags"] & image.ERRORFLAGS.LATLON) : # ca. 400 m
            raw.rawheader["dlr"]["error_flags"] |= image.ERRORFLAGS.LATLON
            raw.rawheader["dlr"]["changed_flags"] |= image.CHANGEDFLAGS.LON
            raw.rawheader["dlr"]["changed_flags"] |= image.CHANGEDFLAGS.LAT
            print(raw.rawheader["falcon"]["gps_lat"],">",last.rawheader["falcon"]["gps_lat"])
            print(raw.rawheader["falcon"]["gps_long"],">",last.rawheader["falcon"]["gps_long"])
            raw.rawheader["falcon"]["gps_lat"] = last.rawheader["falcon"]["gps_lat"]
            raw.rawheader["falcon"]["gps_long"] = last.rawheader["falcon"]["gps_long"]
        if utils2.differs_more(raw.rawheader["falcon"]["cam_angle_pitch"],last.rawheader["falcon"]["cam_angle_pitch"],500):
            raw.rawheader["dlr"]["flags"] |= image.FLAGS.CAM_CHANGED
        if utils2.differs_more(raw.rawheader["startup_gps"]["long"] ,last.rawheader["startup_gps"]["long"] ,1) and \
            last.rawheader["startup_gps"]["long"] == 0 and last.rawheader["startup_gps"]["lat"] == 0 and \
            utils2.differs_more(raw.rawheader["startup_gps"]["lat"] ,last.rawheader["startup_gps"]["lat"] ,1): 
            raw.rawheader["dlr"]["flags"] |= image.FLAGS.MOTORS_ON
        if not -1800000000 <= raw.rawheader["falcon"]["gps_long"] <= 1800000000 or \
        not -900000000 <= raw.rawheader["falcon"]["gps_lat"] <= 900000000:# -90 .. 90 deg
            raw.rawheader["falcon"]["gps_long"] = last.rawheader["falcon"]["gps_long"]
            raw.rawheader["dlr"]["changed_flags"] |= image.CHANGEDFLAGS.LON
            raw.rawheader["falcon"]["gps_lat"] = last.rawheader["falcon"]["gps_lat"]
            raw.rawheader["dlr"]["changed_flags"] |= image.CHANGEDFLAGS.LAT
            raw.rawheader["dlr"]["error_flags"] |= image.ERRORFLAGS.LATLON
        if not -300000 <= raw.rawheader["falcon"]["baro_height"] <= 300000: #300m
            raw.rawheader["falcon"]["baro_height"] = last.rawheader["falcon"]["baro_height"]
            raw.rawheader["dlr"]["changed_flags"] |= image.CHANGEDFLAGS.BAROHEIGHT
            raw.rawheader["dlr"]["error_flags"] |= image.ERRORFLAGS.BAROHEIGHT
        if utils2.differs_more(raw.rawheader["falcon"]["baro_height"],last.rawheader["falcon"]["baro_height"],10000) and \
            raw.rawheader["falcon"]["baro_height"]== 0 : # 10 m diff
            raw.rawheader["falcon"]["baro_height"] = last.rawheader["falcon"]["baro_height"]
            raw.rawheader["dlr"]["changed_flags"] |= image.CHANGEDFLAGS.BAROHEIGHT
            raw.rawheader["dlr"]["error_flags"] |= image.ERRORFLAGS.BAROHEIGHT
        raw.rawheader["dlr"]["gps_acc_x"] = raw.rawheader["falcon"]["gps_speed_x"] - last.rawheader["falcon"]["gps_speed_x"]
        raw.rawheader["dlr"]["gps_acc_y"] = raw.rawheader["falcon"]["gps_speed_y"] - last.rawheader["falcon"]["gps_speed_y"]
        if utils2.differs_more(raw.rawheader["falcon"]["angle_pitch"],last.rawheader["falcon"]["angle_pitch"],1000):
            raw.rawheader["dlr"]["error_flags"] |= image.ERRORFLAGS.FAST_PITCH
        if utils2.differs_more(raw.rawheader["falcon"]["angle_roll"],last.rawheader["falcon"]["angle_roll"],1000):
            raw.rawheader["dlr"]["error_flags"] |= image.ERRORFLAGS.FAST_ROLL
        raw.fill_header()
    
    def fill_presets(self, settings, raw):
        raw.rawheader["dlr"]["cam_roll_offset"] = int(float(settings.value("BORESIGHT_CALIBRATION/rolldiff",0))*1000)
        raw.rawheader["dlr"]["cam_pitch_offset"] = int(float(settings.value("BORESIGHT_CALIBRATION/pitchdiff",0))*1000)
        raw.rawheader["dlr"]["cam_yaw_offset"] = int(float(settings.value("BORESIGHT_CALIBRATION/yawdiff",0))*1000)
        raw.rawheader["dlr"]["boresight_calib_timestamp"] = utils2.to_timestamp(str(settings.value("BORESIGHT_CALIBRATION/date","1970-01-01T00:00:01+00:00")))
        raw.rawheader["dlr"]["radiometric_B"] = int(float(settings.value("RADIOMETRIC_CALIBRATION/B",0))*100)
        raw.rawheader["dlr"]["radiometric_R"] = int(float(settings.value("RADIOMETRIC_CALIBRATION/R",0))*1000)
        raw.rawheader["dlr"]["radiometric_F"] = int(float(settings.value("RADIOMETRIC_CALIBRATION/F",0))*1000)
        raw.rawheader["dlr"]["radiometric_calib_timestamp"] = utils2.to_timestamp(str(settings.value("RADIOMETRIC_CALIBRATION/date","1970-01-01T00:00:01+00:00")))
        
        raw.rawheader["dlr"]["geometric_fx"] = int(float(settings.value("GEOMETRIC_CALIBRATION/fx",0))*10)
        raw.rawheader["dlr"]["geometric_fy"] = int(float(settings.value("GEOMETRIC_CALIBRATION/fy",0))*10)
        raw.rawheader["dlr"]["geometric_cx"] = int(float(settings.value("GEOMETRIC_CALIBRATION/cx",0))*10)
        raw.rawheader["dlr"]["geometric_cy"] = int(float(settings.value("GEOMETRIC_CALIBRATION/cy",0))*10)
        raw.rawheader["dlr"]["geometric_skew"] = int(float(settings.value("GEOMETRIC_CALIBRATION/skew",0))*1000)
        raw.rawheader["dlr"]["geometric_k1"] = int(float(settings.value("GEOMETRIC_CALIBRATION/k1",0))*1000)
        raw.rawheader["dlr"]["geometric_k2"] = int(float(settings.value("GEOMETRIC_CALIBRATION/k2",0))*1000)
        raw.rawheader["dlr"]["geometric_k3"] = int(float(settings.value("GEOMETRIC_CALIBRATION/k3",0))*1000)
        raw.rawheader["dlr"]["geometric_p1"] = int(float(settings.value("GEOMETRIC_CALIBRATION/p1",0))*1000)
        raw.rawheader["dlr"]["geometric_p2"] = int(float(settings.value("GEOMETRIC_CALIBRATION/p2",0))*1000)
        raw.rawheader["dlr"]["geometric_pixelshift_x"] = int(float(settings.value("GEOMETRIC_CALIBRATION/pixelshift_x",0))*10**8)
        raw.rawheader["dlr"]["geometric_pixelshift_y"] = int(float(settings.value("GEOMETRIC_CALIBRATION/pixelshift_y",0))*10**8)
        raw.rawheader["dlr"]["geometric_calib_timestamp"] = utils2.to_timestamp(str(settings.value("GEOMETRIC_CALIBRATION/date","1970-01-01T00:00:01+00:00")))
        
        raw.rawheader["dlr"]["erkennung"] = b'DLR'
        raw.rawheader["dlr"]["version_major"] = 0x01
        raw.rawheader["dlr"]["version_minor"] = 0x02
        raw.rawheader["dlr"]["platzhalter"] = b''
        raw.rawheader["dlr"]["platzhalter2"] = b''
        raw.rawheader["dlr"]["changed_flags"] = 0
        raw.rawheader["dlr"]["error_flags"] = 0
        raw.rawheader["dlr"]["flags"] = 0
        raw.rawheader["dlr"]["pois"]= [{"id":0,"x":0,"y":0 } for k in range(0,9)]
   
   
        
if __name__ == "__main__":
    app = QtCore.QCoreApplication([])
    wf = Araloader()
    settings = QtCore.QSettings("poi_tagger2.ini", QtCore.QSettings.IniFormat)
    settings.setFallbacksEnabled(False) 
    wf.prepare(settings,"test/indir")
    wf.start()
    wf.finished.connect(app.exit)
    sys.exit(app.exec_())
   