from __future__ import print_function
import numpy as np
import os
import logging
import sys
import utm
import collections
import datetime
from . import camera2
from . import gpx
import math
import xml.etree.ElementTree as ET
from . import image
from . import PATHS
import traceback
from ast import literal_eval

from . import upload

from PyQt5 import QtGui,QtCore,uic
        
        
class PoiModel(QtCore.QObject):
    sigPois =  QtCore.pyqtSignal(list)
    #sig_reprojected =  QtCore.pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.Cam = camera2.Camera()
        self.CamR = camera2.Camera()
            
    def setMeta(self,param):
        self.p = param
    
    def __loadPoisList(self):
        layer = self.p.children()
        self.pois = []
        try:
            for L in layer:
                pois = L.child("data").children()
                for poi in pois:
                    for view in poi.children():
                        val = literal_eval(view.value())
                        self.pois.append({"name":poi.name(),"x":val[0],"y":val[1],"layer":L.name(),"filename":view.name()})
        except:
            logging.warning("loadPoisList failed",exc_info=True)
        
        
    def getPois(self,filename):
        #self.pois = [{"name":"Kitz1","x":234,"y":510,"layer":0,"filename":"021345.ARA"}]
        self.__loadPoisList()
        #print(self.pois)
        Direct = []
        Reprojected = []
        for i in self.pois:
            if i["filename"]==filename:
                Direct.append(i)
            else:
                Reprojected.append(i)
                
        self.sigPois.emit(self.pois)

    def project(self,x,y,cam):#muesste eigentlich reproject heissen, weil vom pixel auf 3d-Punkt zurueckprojiziert wird.
            #erzeugt latitude, longitude und elevation  
        try:
            #rp = self.Cam.reproject(np.array([[x],[y]]))
            poi = cam.poi(x,y,0) #Todo: hier wird angenommen, dass das DEM eine Ebene bei Z = 0 ist.
            if poi.any() == None:
                print("any(POI) = None",poi)
           #     return (0,0,0)
            ll = utm.to_latlon(poi[1],poi[0],self.ara.header["gps"]["UTM_ZoneNumber"],self.ara.header["gps"]["UTM_ZoneLetter"])
            return str("%2.6f"%ll[0]),str("%2.6f"%ll[1]),str(poi[2][0])
        except:
            logging.error("project did not work", exc_info=True)    
   # def getReprojected(self,filename):
   #     pois = [{"name":"Kitz1","x":234,"y":510,"layer":0,"filename":"0102344_0324.ARA"}]
   #     self.sig_reprojected.emit(pois)


    
    # def reload_poilist(self):
        # #falls die Kalibrierung nach dem Setzen der Pois geschieht, wird hiermit die projektion in der poiliste korrigiert.
        # myCam = camera2.Camera()
        # print ("reload_poi",self.indir)
        
        # reloaded_poilist = []
        # for entry in self.poilist:
            # filename = entry[1]
            # x_geo,y_geo = self.checkcamorientation(entry[3],entry[4])
            # curfilepath = os.path.join(self.indir,filename)
            # raw = image.Image.factory(curfilepath)
            # if self.calib.actionEigeneWerte.isChecked():
                # pitch_offset = self.calib.dlr_cam_pitch_offset_2.value()
                # roll_offset = self.calib.dlr_cam_roll_offset_2.value()
                # yaw_offset = self.calib.dlr_cam_yaw_offset_2.value()
            # else:
                # pitch_offset = ara.header["calibration"]["boresight"].get("cam_pitch_offset",0)
                # roll_offset = ara.header["calibration"]["boresight"].get("cam_roll_offset",0)
                # yaw_offset = ara.header["calibration"]["boresight"].get("cam_yaw_offset",0)
            
            # myCam.pose(0,0,ara.header["uav"]["yaw"],ara.header["gps"].get("UTM_X",0),ara.header["gps"].get("UTM_Y",0),ara.header["gps"].get("rel_altitude",0))
            # myCam.gimbal(roll=ara.header["camera"]["roll"],pitch=ara.header["camera"]["pitch"],yaw=ara.header["camera"]["yaw"],dx=0.2,dy=0,dz=0,dir="ZXY")
            # myCam.boresight(self.yaw_offset, self.pitch_offset, self.roll_offset,0,0,0)
            # myCam.intrinsics(640,512,1115,320,256)
            # myCam.transform()
            # lat,lon,ele = self.project(x_geo,y_geo,myCam)
            # row = [entry[0],filename,entry[2],x_geo,y_geo,lat,lon,ele,entry[8],entry[9],entry[10],entry[11],entry[12],self.pitch_offset,self.roll_offset,self.yaw_offset, raw.header.gps_date+"T"+raw.header.gps_time, int(raw.header.start_hor_accur*1000) ]
            # reloaded_poilist.append(row)
        # return reloaded_poilist
        
   
        
    # def reproject(self,poi):
    # # Wir machen das hier nur , um in echtzeit aenderungen an yaw_offset, pitch_offset und roll_offset sichtbar zu machen
       # # print("REPROJECT: ",poi)
        # #print self.ara.header.gps_time
        # #poi: [id,filename,name,x,y,lat,lon,ele,uav_lat,uav_lon,uav_ele,uav_yaw,cam_pitch]
        # UTM_Y,UTM_X,ZoneNumber,ZoneLetter = utm.from_latlon(poi[8],poi[9])
        # self.CamR.pose(0,0,poi[11],UTM_X,UTM_Y,poi[10])
        # self.CamR.gimbal(roll=0,pitch=poi[12],yaw=0,dx=0.2,dy=0,dz=0,dir="ZXY")
        # self.CamR.boresight(self.yaw_offset, self.pitch_offset, self.roll_offset,0,0,0)
        # self.CamR.intrinsics(640,512,1115,320,256)
        # self.CamR.transform()
        # x_geo,y_geo = self.checkcamorientation(poi[3],poi[4])
        # #x_geo = poi[3]
        # #y_geo = poi[4]
        # try:
            # lat,lon,ele = self.project(x_geo,y_geo,self.CamR) #-------------------------------- bis hier hin
        # except:
            # lat,lon,ele = 0,0,0
            # logging.error("reproject did not work", exc_info=True)
        # #self.Cam.project()
        
        # #print "latlon",lat,lon,ele,type(lat),type(lon),type(ele)
        # u = utm.from_latlon(float(lat),float(lon))#,self.ara.header.ZoneNumber)
        
        # V = np.array([[u[1]],[u[0]],[float(ele)],[1]])
       # # print ("V",V, self.Cam.position(),self.Cam.R_gimbal,self.Cam.R_uav)
        # X = self.Cam.project(V)
       # # print ("X",X)
        # if self.Cam.visible(X):
            # q = []
            # q[:] = poi[:]
            # q[3] = X[0][0]
            # q[4] = X[1][0]
            # q.append(2)
            # return q
            # #            pois_vis.append(q)
            
            
    # def load_data(self,ara,imgname,calib):
        # """
        # zu jedem Bild das geladen wird wird diese Methode aufgerufen
        # """
        # self.imgname = imgname
        # self.calib = calib
        # self.currentlist = [entry for entry in self.poilist if entry[1] == ara.filename] 
        # try:
            
            # if calib.actionEigeneWerte.isChecked():
                # self.pitch_offset = calib.dlr_cam_pitch_offset_2.value()
                # self.roll_offset = calib.dlr_cam_roll_offset_2.value()
                # self.yaw_offset = calib.dlr_cam_yaw_offset_2.value()
            # else:
                # self.pitch_offset = ara.header["calibration"]["boresight"].get("cam_pitch_offset",0)
                # self.roll_offset = ara.header["calibration"]["boresight"].get("cam_roll_offset",0)
                # self.yaw_offset = ara.header["calibration"]["boresight"].get("cam_yaw_offset",0)
            # self.ara = ara
            # self.filename = ara.filename
      
            # self.Cam.pose(0,0,ara.header["uav"]["yaw"],ara.header["gps"].get("UTM_X",0),ara.header["gps"].get("UTM_Y",0),ara.header["gps"].get("rel_altitude",0))
            # self.Cam.gimbal(roll=ara.header["camera"]["roll"],pitch=ara.header["camera"]["pitch"],yaw=ara.header["camera"]["yaw"],dx=0.2,dy=0,dz=0,dir="ZXY")
            # self.Cam.boresight(self.yaw_offset, self.pitch_offset, self.roll_offset,0,0,0)
            # self.Cam.intrinsics(640,512,1115,320,256)
            # self.Cam.transform()
            # self.view.selectRow(len(self.currentlist)-1)
            # self.view.setFocus()
            # self.refresh.emit()
        # except:
            # logging.error("pois load data failed",exc_info=True)
        
    # def checkcamorientation(self,x,y,width = 640, height = 512):
        # #x_geo = x
        # #y_geo = y
       # # if self.conf.georef_fliphor_CB.isChecked():
       # #     x_geo = width - x
       # # else:
       # #     x_geo = x
       # # if self.conf.georef_flipver_CB.isChecked():
       # #     y_geo = height - y
       # # else:
       # #     y_geo = y
       # # return x_geo,y_geo
        # return x,y
        
    # 
                        
    # def pos(self,x,y): #set poi at current mouse position click
        # x_geo,y_geo = self.checkcamorientation(x,y)
        # try:
            # if self.ara.header["calibration"].get("error_flags",0) & image.ERRORFLAGS.ALL_META: return
            # uav_lat = self.ara.header["gps"].get("latitude",0)
            # uav_lon = self.ara.header["gps"].get("longitude",0)
            # uav_ele = self.ara.header["gps"].get("rel_altitude",0)
            # uav_yaw = self.ara.header["uav"].get("yaw",0)
            # cam_pitch = self.ara.header["camera"].get("pitch",0)
            # pitch_offset = self.ara.header["calibration"]["boresight"].get("cam_pitch_offset",0)
            # roll_offset  = self.ara.header["calibration"]["boresight"].get("cam_roll_offset",0)
            # yaw_offset   = self.ara.header["calibration"]["boresight"].get("cam_yaw_offset",0)
        # except:
            # logging.error("pois pos(): load header data failed")
            # return
        # self.id = self.id+1
        # try:
            # lat,lon,ele = self.project(x_geo,y_geo,self.Cam)
        # except:
            # lat,lon,ele = 0,0,0

        # try:
            # self.log.emit("ID: %d, File: %s, X: %d, Y: %d, X_geo: %d, Y_geo: %d, lat: %s, lon: %s, ele: %s" %(self.id,self.ara.filename, x,y,x_geo, y_geo,lat,lon,ele)  )
            # self.poilist.append([self.id,self.ara.filename, "xxx", x,y,float(lat),float(lon),float(ele),uav_lat,uav_lon,uav_ele,uav_yaw,cam_pitch,pitch_offset, roll_offset, yaw_offset])
            # self.currentlist = [entry for entry in self.poilist if entry[1] == self.ara.filename] 
            # idx = self.markerModel.index(len(self.currentlist)-1,0)
            # self.refresh.emit()
            # self.view.resizeColumnsToContents()
            # self.view.selectRow(len(self.currentlist)-1)
            # self.view.setFocus()
        # except:    
            # logging.error("pois set pos did not work",exc_info=True)
    
            
    # def loadSettings(self, settings):
        # self.settings = settings
        # self.dialog.loadSettings(settings)
        
    # def writeSettings(self):
        # pass
        
if __name__ == "__main__":
    # import image
    # app = QtGui.QApplication(sys.argv)
    # ara = image.Image.factory("test/5_0210001.ARA")
    # w = Pois(ara)
    # clear = QtGui.QPushButton("clear",w)
    # clear.move(0,200)
    # clear.clicked.connect(w.clear)
    # w.resize(300, 250)
    # w.move(300, 300)
    # w.show()
    # sys.exit(app.exec_())
    pass