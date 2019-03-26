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

from . import gpx
from . import image
from . import PATHS
from . import upload
from . import transform

np.set_printoptions(suppress=True)
    
epsilon=1e-6

def par(meta,treepath=[],default=None):
    n = len(treepath)
    try: 
        chain = "meta"
        for i in treepath:
            chain += ".child('"+i+"')"
        chain += ".value()"
        #print (chain)
        return eval(chain)
    except:
        #logging.error("par failed",exc_info=True)
        return default
    
class PoiModel(QtCore.QObject):
    sigPois =  QtCore.pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.Cam = camproject.Camera()
        self.CamR = camproject.Camera()
        self.Ext = camproject.Extrinsics()
        self.ExtR = camproject.Extrinsics()
        self.dem = None
        self.boresight_roll, self.boresight_pitch, self.boresight_yaw,self.boresight_order = 0,0,0,"ZYX"
        self.im_width,self.im_height,self.im_fx,self.im_cx,self.im_cy = 0,0,1000,0,0

    def onImage(self,point):
        pt = point.ravel()
        if  0 < pt[0] < self.im_width:
            if 0 < pt[1] < self.im_height:
                return True
        else:
            return False
            
    def setAttitude(self,mat=None):
        if mat== None:
            self.Cam.attitudeMat(self.Ext.transform())
        else:
            self.Cam.attitudeMat(mat)
    
    def setPose(self,imgheader):
        #logging.warning("SET POSE " + imgheader["file"]["name"])
        self.imgheader = imgheader
        try:
            uavyaw = imgheader["uav"]["yaw"]
            uavX = round(imgheader["gps"].get("UTM_X",0),3)
            uavY = round(imgheader["gps"].get("UTM_Y",0),3)
            uavZ = imgheader["gps"].get("rel_altitude",0)
            uavorder = imgheader["uav"]["euler_order"]
            roll = imgheader["camera"]["roll"]
            
            pitch= imgheader["camera"]["pitch"]
            
            yaw = imgheader["camera"]["yaw"]
            gimbalorder = imgheader["camera"]["euler_order"]
            
            self.Ext.setPose(X=uavX,Y=uavY,Z=uavZ,order=uavorder)
            self.Ext.setGimbal(roll=roll,pitch=pitch,yaw=yaw,order=gimbalorder)
            #self.Ext.setUAVBoresight(dx=0.2)
        except:
            logging.error("pois load data failed",exc_info=True)
        self.setAttitude()
       # print(self.Ext.getParams())
       # print(self.ExtR.getParams()["pose"])
        
    def loadMeta(self,meta):
        self.im_width = par(meta, ["general","images","width"],0) #meta.child("general").child("images").child("width").value() #["general"]["images"]["width"]
        self.im_height = par(meta, ["general","images","height"],0) #meta.child("general").child("images").child("height").value()#["general"]["images"]["height"]
        self.im_cx = par(meta, ["calibration","geometric","cx"],0) #meta.child("calibration").child("geometric").child("cx").value()#["calibration"]["geometric"]["cx"]
        self.im_cy = par(meta, ["calibration","geometric","cy"],0) #meta.child("calibration").child("geometric").child("cy").value()#["calibration"]["geometric"]["cy"]
        self.im_fx = par(meta, ["calibration","geometric","fx"],0) #meta.child("calibration").child("geometric").child("fx").value()#["calibration"]["geometric"]["fx"]
        
        ###########################
        # there was a fixed Value in camera2 !!!!
        ###########################
        
        self.im_cx = 320
        self.im_cy = 256
        self.im_fx = 1115
        
        self.boresight_pitch = par(meta, ["calibration","boresight","cam_pitch"],0) #meta.child("calibration").child("boresight").child("cam_pitch_offset").value()#["calibration"]["boresight"]["cam_pitch_offset"]
        self.boresight_roll = par(meta, ["calibration","boresight","cam_roll"],0) #meta.child("calibration").child("boresight").child("cam_roll_offset").value()#["calibration"]["boresight"]["cam_roll_offset"]
        self.boresight_yaw = par(meta, ["calibration","boresight","cam_yaw"],0) #meta.child("calibration").child("boresight").child("cam_yaw_offset").value()#["calibration"]["boresight"]["cam_yaw_offset"]
        self.boresight_order = par(meta, ["calibration","boresight","cam_euler_order"],"ZYX") #meta.child("calibration").child("boresight").child("cam_yaw_offset").value()#["calibration"]["boresight"]["cam_yaw_offset"]
        self.pois = []
        try:
            for L in meta.child("pois").children():
                for poi in L.child("data").children():
                    for view in poi.children():
                        val = literal_eval(view.value())
                       # print ("VAL",val,view.opts)
                        try:
                            self.pois.append({"name":poi.name(),"x":val[0],"y":val[1],"layer":L.name(),
                                "filename":view.name(), 
                                "lat":float(view.opts.get("latitude",0)),
                                "lon":float(view.opts.get("longitude",0)), 
                                "ele":float(view.opts.get("elevation",0)),
                                "uav_lat":float(view.opts["uav_lat"]), 
                                "uav_lon":float(view.opts["uav_lon"]),
                                "uav_ele":float(view.opts["uav_ele"]), 
                                #"uav_yaw":float(view.opts["uav_yaw"]),
                                "cam_yaw":float(view.opts["cam_yaw"]),
                                "cam_pitch":float(view.opts["cam_pitch"]), 
                                "cam_roll":float(view.opts["cam_roll"]),
                                "cam_euler_order":view.opts["cam_euler_order"],
                                "boresight_pitch":float(view.opts["boresight_pitch"]), 
                                "borsight_roll":float(view.opts["boresight_roll"]),
                                "boresight_yaw":float(view.opts["boresight_yaw"]), 
                                "boresight_euler_order":view.opts["boresight_euler_order"],
                                "found_time":view.opts["found_time"]})
                        except:
                            self.pois.append({"name":poi.name(),
                                "x":val[0],"y":val[1],
                                "layer":L.name(),
                                "filename":view.name()}) 
        except:
            logging.error("load Calib failed",exc_info=True)
            
        self.Ext.setCameraBoresight(droll=self.boresight_roll, dpitch= self.boresight_pitch, dyaw=self.boresight_yaw, order=self.boresight_order)
        self.setIntrinsics(self.im_width,self.im_height,self.im_fx,self.im_cx,self.im_cy)
       # print("loadMeta",self.im_width,self.im_height,self.im_fx,self.im_cx,self.im_cy)
        
    def getPois(self,filename):
        Pois = []
        Reprojected = []
        #print("========",filename,"============")
        for i in self.pois:
            if i["filename"]==filename:
                Pois.append(i)
            else:
                try:
                    attitude = self.prepareReproject(i)    
                    j = self.backreproject(i, attitude)
                 #   print(j)
                    if not j.all() == None:
                        rep = i.copy()
                        rep["x"]= j.ravel()[0]
                        rep["y"]= j.ravel()[1]
                        rep["reprojected"]=True
                        Reprojected.append(rep)
                except:
                    logging.warning("getPois Reproject failed",exc_info=True)
        Pois.extend(Reprojected)
       # print("REPROJECTED:")
       # print (Reprojected)
        self.sigPois.emit(Pois)
        
            
    
    def prepareReproject(self,poi):
    #    print("ExtR:")
        UTM_Y,UTM_X,ZoneNumber,ZoneLetter = utm.from_latlon(poi["uav_lat"],poi["uav_lon"])
        self.ExtR.setPose(0,0,0,round(UTM_X,3),round(UTM_Y,3),poi["uav_ele"]) #yaw=0.54,X=UTM_X,Y=UTM_Y,Z=48.57)
        #self.ExtR.setUAVBoresight(dx=poi["cam_dx"],dy=poi["cam_dy"],dz=poi["cam_dz"])#dx=0.20)
        self.ExtR.setCameraBoresight(dyaw= self.boresight_yaw, 
            dpitch= self.boresight_pitch, 
            droll= self.boresight_roll,
            order= self.boresight_order) #dpitch=-1.5,dyaw=1.0
        self.ExtR.setGimbal(roll=poi["cam_roll"],pitch= poi["cam_pitch"],yaw=poi["cam_yaw"],order=poi["cam_euler_order"])#pitch=-90,roll=-0.23,yaw=0,order="ZXY")
        #self.ExtR.setGimbal(pitch=-90,roll=0,yaw=0,order="ZXY")
        #print ("RBoresight:",self.ExtR.R_cam_boresight)
        #print ("TBoresight:",self.ExtR.T_cam_boresight)
        #print("RGimbal",self.ExtR.R_gimbal)
        #print("uavboresight",self.ExtR.R_uav_boresight)
        #print("uavboresight",self.ExtR.T_uav_boresight)
        #print("uav",self.ExtR.T_uav)#T_uav
        
        # print("cosyUAV2Cam",self.ExtR.cosyUAVToCamera,
        # "rcambire",self.ExtR.R_cam_boresight,
        # "tcambore",self.ExtR.T_cam_boresight,
        # "rgim",self.ExtR.R_gimbal,
        # "r_uav_bore",self.ExtR.R_uav_boresight,
        # "Tuavbore",self.ExtR.T_uav_boresight,
        # "R_uav",self.ExtR.R_uav,
        # "cosyW2UAV",self.ExtR.cosyWorldToUAV.T,
        # "T_uav",self.ExtR.T_uav)
        
        
        return self.ExtR.transform()
    
    def setIntrinsics(self,width,height,fx,cx,cy,ar=1.0,skew=0.0):
        self.Cam.intrinsics(width,height,fx,cx,cy,ar,skew)
        self.CamR.intrinsics(width,height,fx,cx,cy,ar,skew)
    
    def setDEM(self,dem):
        self.dem = dem
        
    def raymarching(self,pos,vec,ele=0):
        if not self.dem:
            poi = self.ray_intersect_plane(pos[0:3],vec[0:3],np.array([0,0,1,ele]),True)
        return poi #3D Vector
    
    def ray_intersect_plane(self,raypos, raydir, plane, front_only=True):
        p = plane[:3] * plane[3]
        n = plane[:3]
        
        rd_n = np.dot(raydir.ravel()[:3], n)
        if abs(rd_n) < epsilon:
            logging.warning("length of raydir is 0")
            return np.array([[None],[None],[None]])
        if front_only == True:
            if rd_n >= epsilon:
                logging.warning("raydir points away")
                return np.array([[None],[None],[None]])
        pd = np.dot(p, n)
        p0_n = np.dot(raypos.ravel(), n)
        t = (pd - p0_n) / rd_n
        return raypos.ravel() + (raydir.ravel()[:3] * t)
    
    def reproject_poi(self,x,y):
        pos = self.reproject(np.array([x,y]))
        lat, lon = utm.to_latlon(pos[1],pos[0],self.imgheader["gps"].get("UTM_ZoneNumber",0),
                        self.imgheader["gps"].get("UTM_ZoneLetter",None))
        found_time = datetime.datetime.now().isoformat()
        return {"name":self.imgheader["file"]["name"],"value":(x,y),"type":"str", "paramtyp":"view", 
            "latitude":lat, "longitude":lon,"elevation":pos[2], 
            "uav_lat":float(self.imgheader["gps"]["latitude"]), 
            "uav_lon":float(self.imgheader["gps"]["longitude"]),
            "uav_ele":float(self.imgheader["gps"]["rel_altitude"]), 
            "cam_yaw":float(self.imgheader["camera"]["yaw"]),
            "cam_pitch":float(self.imgheader["camera"]["pitch"]), 
            "cam_roll":float(self.imgheader["camera"]["roll"]),
            "cam_euler_order":self.imgheader["camera"]["euler_order"],
            "boresight_pitch":self.boresight_pitch, 
            "boresight_roll":self.boresight_roll,
            "boresight_yaw":self.boresight_yaw, 
            "boresight_euler_order":self.boresight_order, 
            "found_time":found_time,
            "readonly":False,"removable":True,"renamable":False,"enabled":False}
        
    def reproject(self,x):
        repro = self.Cam.reproject(x)
        campos = self.Cam.position()
        rd = repro.T - campos.ravel()
        pos = self.raymarching(campos, rd.reshape(4,1))
        return pos
    
   # def frontofcamera(self,pt,camplane):
   #     print ("frontofcam",pt.ravel(),camplane.ravel())
   #     rd_n = np.dot(pt.ravel()[:3], camplane.ravel()[:3])
   #     print ("infrontofcam", rd_n)
   #     if rd_n>0: return True
   #     else: return False
        
    def backreproject(self,x,attitudeMat):
      #  print(x,attitudeMat)
        self.CamR.attitudeMat(attitudeMat)
        pixel = np.array([int(float(x["x"])),int(float(x["y"]))]) #.reshape(1,2)
        repro = self.CamR.reproject(pixel)
        campos = self.CamR.position()
        rd = repro.T - campos.ravel()
        pos = self.raymarching(campos,rd).reshape(1,3)
      #  if not self.frontofcamera(pos,self.Cam.reproject(np.array([[320,256]]))):
      #      print("BACKSIDE!")
      #      return np.array([[None,None]])
        
        x_br = self.Cam.project(pos)
        if self.onImage(x_br.ravel()):
            return x_br
        else:
            return np.array([[None,None]])
        
        
if __name__ == "__main__":
    test = 4
    np.set_printoptions(suppress=True)
    import utm
    
    poi = PoiModel()
    poi.setIntrinsics(640,512,1115,320,256)#640,512,1500,320,256)
        
    if test ==1:
        print("\nExample1")
        poi.Ext.setPose(yaw=0,pitch=0,X=20,Y=1,Z=100)
        poi.Ext.setGimbal(pitch=-80)
        poi.setAttitude()
        Xc = np.array([[320],[256]]).ravel()
    elif test==2:
        print("\nExample2")
        UTM_Y,UTM_X,ZoneNumber,ZoneLetter = utm.from_latlon(48.1405597,11.016507)
        poi.Ext.setPose(X=round(UTM_X,3),Y=round(UTM_Y,3),Z=48.57)
        poi.Ext.setGimbal(pitch=-90)
        poi.setAttitude()
        Xc = np.array([[513],[267]]).ravel()
    elif test==3:
#        backreproject(x) {'name': 'xxx_3', 'x': '513.0', 'y': '267.0', 'layer': '0', 'filename': '04051446_0076.ARA', 'lat': 48.
#140543, 'lon': 11.016634, 'ele': 0.0, 'uav_lat': 48.1405597, 'uav_lon': 11.016507, 'uav_ele': 48.57, 'cam_yaw': 0.54, 'c
#am_pitch': -90.0, 'cam_roll': 0.0, 'cam_dx': 0.2, 'cam_dy': 0.0, 'cam_dz': 0.0, 'euler_dir': 'ZXY', 'pitch_offset': 1.5,
# 'roll_offset': 0.0, 'yaw_offset': 1.0, 'found_time': '2017-04-05T14:43:52'}
#[[      -0.01884844        0.99982235        0.          -549358.97277609]
# [       0.99982235        0.01884844       -0.         -5345193.61324658]
# [       0.                0.                1.              -48.57      ]
# [       0.                0.                0.                1.        ]]
        print("\nExample3")
        UTM_Y,UTM_X,ZoneNumber,ZoneLetter = utm.from_latlon(48.1405597,11.016507)
        poi.Ext.setPose(yaw=0.54,X=round(UTM_X,3),Y=round(UTM_Y,3),Z=48.57)
        poi.Ext.setGimbal(pitch=-90)
        poi.setAttitude()
        Xc = np.array([[513],[267]]).ravel()

    if test <4:
        Xrepro = poi.reproject(Xc)
        print("S",poi.Cam.S)
        print("Xc",Xc)
        print("rel",Xrepro-poi.Cam.position()[0:3].ravel())
        print("Xrepro", Xrepro)

    if test==4:
        print("\nExample4, genauso ist es in camera2 implementiert!") #'filename': '04051446_0076.ARA'
        UTM_Y,UTM_X,ZoneNumber,ZoneLetter = utm.from_latlon(48.1405597,11.016507)
        pUTM_Y,pUTM_X,pZoneNumber,pZoneLetter = utm.from_latlon(48.140543,11.016634)
        #poi.Ext.setPose(roll=-0.23,yaw=-0.54,X=UTM_X,Y=UTM_Y,Z=48.57)
        #poi.Ext.setCameraBoresight(dpitch=-1.5,dyaw=1.0, dx=0.20)
        #poi.Ext.setGimbal(pitch=-90)
        poi.Ext.setPose(yaw=0.54,X=round(UTM_X,3),Y=round(UTM_Y,3),Z=48.57)
        poi.Ext.setUAVBoresight(dx=0.20)
        poi.Ext.setCameraBoresight(dpitch=-1.5,dyaw=1.0)
        poi.Ext.setGimbal(pitch=-90,roll=-0.23,yaw=0,order="ZXY")
        poi.setAttitude()
        Xc = np.array([[513],[267]]).ravel()
        print("Xc",Xc)
        Xrepro = poi.reproject(Xc)
        print("Xrepro", Xrepro)
    
        print("UTM",UTM_Y,UTM_X,ZoneNumber)
        print("pUTM",round(pUTM_X,3),round(pUTM_Y,3),pZoneNumber)
        print("rel from UTM y:",pUTM_Y-UTM_Y,"x:",pUTM_X-UTM_X)
        print("S",poi.Cam.S)
        print("rel",Xrepro-poi.Cam.position()[0:3].ravel())
        xrp = Xrepro.reshape(1,3)
        #mat4d = np.vstack((mat3d,[0,0,0]))
        px = poi.Cam.project(np.hstack((xrp,[[1]])))
        print("px",px)
        pl = poi.Cam.project(np.array([[pUTM_X],[pUTM_Y],[0],[1]]))
        print("frompoilist",pl)
    # import os
    # import sys
    # import logging
    # import numpy as np
    # from PyQt5 import QtCore,QtGui,uic, QtWidgets,QtTest
    # from PyQt5.QtWidgets import QApplication,QWidget,QMainWindow, QLineEdit,QToolButton,QAction,QMessageBox,QPushButton,QVBoxLayout,QProgressDialog
    # import pyqtgraph as pg
    # from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
    # from . import image
    # from . import flightjson
        
    # app = QApplication(sys.argv)
    # path = "D:/WILDRETTER-DATEN/2017_DLR/2017-04-05_14-56_Hausen"
    
    # poi = PoiModel()
    
    # win = flightjson.FlightWidget()
    # root = QLineEdit()
    # root.insert(path)
    # ldbut = QPushButton()
    # ldbut.setText("Load")
    # win.toolBar.addWidget(root)
    # win.toolBar.addWidget(ldbut)
    # fm = flightjson.Flight()
    # fm.load(path)
    # win.setMeta(fm)    
    
    # fm.loadfinished.connect(lambda: poi.loadMeta(fm.p))
    # img = image.Image.factory(os.path.join(path,"04051456_0229.ARA"))
    
    # #poi.setPose(img.header)
    # print("POSE,yaw:",img.header["uav"]["yaw"])
    # print("UTM:",img.header["gps"].get("UTM_X",0),img.header["gps"].get("UTM_Y",0),img.header["gps"].get("rel_altitude",0))
    # print("Gimbal:",img.header["camera"]["roll"],img.header["camera"]["pitch"],img.header["camera"]["yaw"])
    
    # def prepare():
        # #c = poi.Cam.project(np.array([0,0,0,1]))
        # c = np.array([320,256])#[264.0,396.0])
        # #poi.setPose(img.header)
        # poi.Ext.setPose(yaw=0,X=50000,Y=6400,Z=50)
        # poi.Ext.setGimbal(roll=0,pitch=-90)
        # poi.setAttitude()
        # #print("POSalt",poi.Cam.S[0:3,[3]].ravel())
        # #print("POSneu",poi.Cam.position())
        
        # #print (c)
        # rp = poi.reproject(c)
        # print("RP",rp)
        
    # vbox = QVBoxLayout()
    # win.horizontalLayout.addLayout(vbox)
    # but = QPushButton()
    # but.setText("project")
    # vbox.addWidget(but)
    # but.clicked.connect(prepare)
    # win.show()
    
    # win.escAction = QAction('escape', win)
    # win.escAction.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Escape))
    # win.addAction(win.escAction)
    # win.escAction.triggered.connect(win.close)
    # sys.exit(app.exec_())
    
   