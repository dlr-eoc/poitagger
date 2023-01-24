from __future__ import print_function
import numpy as np
import os
import logging
import sys
import utm
import collections
import datetime
import math
import xml.etree.ElementTree as ET
import traceback
from ast import literal_eval
from PyQt5 import QtGui,QtCore,uic

import camproject

from . import PATHS
from . import upload
from . import transform
        
        
class PoiModel(QtCore.QObject):
    sigPois =  QtCore.pyqtSignal(list)
    #sig_reprojected =  QtCore.pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.Cam = camproject.Camera()
        self.CamR = camproject.Camera()
            
    def setMeta(self,param):
        self.p = param.child("pois")
        self.all_p = param
        self.T = transform.Transform()
        
    def load(self,imgheader):
        self.imgheader = imgheader
        print ("###########################################")
        print (imgheader)
        try:
            self.T.pose(0,0,imgheader["uav"]["yaw"],imgheader["gps"].get("UTM_X",0),imgheader["gps"].get("UTM_Y",0),imgheader["gps"].get("rel_altitude",0),True)
            self.T.gimbal(roll=imgheader["camera"]["roll"],pitch=imgheader["camera"]["pitch"],yaw=imgheader["camera"]["yaw"],dx=0.2,dy=0,dz=0,dir="ZXY")
            self.T.boresight(self.yaw_offset, self.pitch_offset, self.roll_offset,0,0,0)
            self.T.transform()
            self.Cam.intrinsics(self.im_width,self.im_height,self.im_fx,self.im_cx,self.im_cy)
            self.Cam.attitudeMat(self.T.attitudeMat())
            
        except:
            logging.error("pois load data failed",exc_info=True)
        
    def __loadPoisList(self):
        layer = self.p.children()
        self.pois = []
        try:
            for L in layer:
                pois = L.child("data").children()
                for poi in pois:
                    for view in poi.children():
                        val = literal_eval(view.value())
                        self.pois.append({"name":poi.name(),"x":val[0],"y":val[1],"layer":L.name(),"filename":view.name(),
                            "lat":float(view.opts["latitude"]),"lon":float(view.opts["longitude"]),"ele":float(view.opts["elevation"]),
                            "uav_lat":float(view.opts["uav_lat"]),"uav_lon":float(view.opts["uav_lon"]),"uav_ele":float(view.opts["uav_ele"]),
                            "cam_yaw":float(view.opts["cam_yaw"]),"cam_pitch":float(view.opts["cam_pitch"]),"cam_roll":float(view.opts["cam_roll"]),
                            "cam_dx":float(view.opts["cam_dx"]),"cam_dy":float(view.opts["cam_dy"]),"cam_dz":float(view.opts["cam_dz"]),"euler_dir":view.opts["euler_dir"],
                            "pitch_offset":float(view.opts["pitch_offset"]),"roll_offset":float(view.opts["roll_offset"]),"yaw_offset":float(view.opts["yaw_offset"]),
                            "found_time":view.opts["found_time"]})
        except:
            logging.warning("loadPoisList failed",exc_info=True)
        
    def loadCalibData(self):
        print ("+++++++++++++++++++ loadCalibDAta")
        try:
            self.im_width = self.all_p.child("general").child("images").child("width").value()
            self.im_height = self.all_p.child("general").child("images").child("height").value()
            self.im_cx = self.all_p.child("calibration").child("geometric").child("cx").value()
            self.im_cy = self.all_p.child("calibration").child("geometric").child("cy").value()
            self.im_fx = self.all_p.child("calibration").child("geometric").child("fx").value()
            #print ("IMWIDTH",self.imwidth,self.imheight,self.im_cx,self.im_cy,self.im_fx)
            
            self.pitch_offset = self.all_p.child("calibration").child("boresight").child("cam_pitch_offset").value()
            self.roll_offset = self.all_p.child("calibration").child("boresight").child("cam_roll_offset").value()
            self.yaw_offset = self.all_p.child("calibration").child("boresight").child("cam_yaw_offset").value()
        except:
            logging.warning("loadCalibFailed",exc_info=True)
            
    def getPois(self,filename):
        #self.pois = [{"name":"Kitz1","x":234,"y":510,"layer":0,"filename":"021345.ARA"}]
        self.__loadPoisList()
        #print(self.pois)
        Direct = []
        Reprojected = []
        for i in self.pois:
            if i["filename"]==filename:
                Direct.append(i)
                #print ("DIRECT POI",i)
            else:
                print ("vorher",i)
                j = self.project(i)
                print ("nachher",j)
                Reprojected.append(j)
                
                
        self.sigPois.emit(self.pois)
    
    def ray_intersect_plane(self,raypos, raydir, plane, front_only=True):
        p = plane[:3] * plane[3]
        n = plane[:3]
        rd_n = np.dot(raydir.ravel(), n)
        if rd_n == 0.0:
            return np.array([[None],[None],[None]])
        if front_only == True:
            if rd_n >= 0.0:
                return np.array([[None],[None],[None]])
        pd = np.dot(p, n)
        p0_n = np.dot(raypos.ravel(), n)
        t = (pd - p0_n) / rd_n
        return raypos + (raydir * t)

       
    def reproject(self,x,y,cam):#muesste eigentlich reproject heissen, weil vom pixel auf 3d-Punkt zurueckprojiziert wird.
            #erzeugt latitude, longitude und elevation  
        try:
            #rp = self.Cam.reproject(np.array([[x],[y]]))
            #poi = self.reprojectZPlane(x,y,0) #Todo: hier wird angenommen, dass das DEM eine Ebene bei Z = 0 ist.
            ele = 0
            poi_cam = np.array([float(x),float(y),1,1])
           # print ("TYPE X",type(x))
            rp = cam.reproject(poi_cam)
            campos = cam.position()
            print ("RP",rp,"POS",campos)
            raydir = rp[0:3] - campos
            poi = self.ray_intersect_plane(campos,raydir,np.array([0,0,1,ele]))
            
            if poi.any() == None:
                print("any(POI) = None",poi)
           #     return (0,0,0)
            print("POI",poi)
            ll = utm.to_latlon(poi[1],poi[0],self.imgheader["gps"]["UTM_ZoneNumber"],self.imgheader["gps"]["UTM_ZoneLetter"])
            return str("%2.6f"%ll[0]),str("%2.6f"%ll[1]),str(poi[2][0])
        except:
            logging.error("project did not work", exc_info=True)    

        
    def project(self,poi):
    # Wir machen das hier nur , um in echtzeit aenderungen an yaw_offset, pitch_offset und roll_offset sichtbar zu machen
        UTM_Y,UTM_X,ZoneNumber,ZoneLetter = utm.from_latlon(poi["uav_lat"],poi["uav_lon"])
        self.T.pose(0,0,poi["cam_yaw"],UTM_X,UTM_Y,poi["uav_ele"],leftcosy=True) # cam_yaw is wrong here. It has to be uav_yaw
        self.T.gimbal(roll=poi["cam_roll"],pitch=poi["cam_pitch"],yaw=poi["cam_yaw"],dx=poi["cam_dx"],dy=poi["cam_dy"],dz=poi["cam_dz"],dir=poi["euler_dir"])
        self.T.boresight(self.yaw_offset, self.pitch_offset, self.roll_offset,0,0,0)
        self.T.transform()
        print ("*****************")
        
        print (self.T.attitudeMat())#[0:3,[3]].ravel())
        self.CamR.attitudeMat(self.T.attitudeMat())
        
        self.CamR.intrinsics(self.im_width,self.im_height,self.im_fx,self.im_cx,self.im_cy)
        #x_geo,y_geo = self.checkcamorientation(poi[3],poi[4])
        #print (self.T.T_uav)
        try:
            lat,lon,ele = self.reproject(poi["x"],poi["y"],self.CamR) #-------------------------------- bis hier hin
        except:
            lat,lon,ele = 0,0,0
            logging.error("reproject did not work", exc_info=True)
        u = utm.from_latlon(float(lat),float(lon))#,self.ara.header.ZoneNumber)
        V = np.array([[u[1]],[u[0]],[float(ele)],[1]])
        X = self.Cam.project(V)
        if self.Cam.visible(X):
            q = poi.copy()
            q["x"] = X[0][0]
            q["y"] = X[1][0]
            q["reprojected"] = True
            return q
            
                    
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