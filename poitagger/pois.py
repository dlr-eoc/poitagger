from __future__ import print_function
import flirsd
import numpy as np
import os
import logging
import sys
import utm
import collections
import datetime
import camera2
import gpx
import math
import xml.etree.ElementTree as ET
import image

import traceback
import upload

from PyQt5 import QtGui,QtCore,uic

POITYPE = ["Vielleicht","Kitz_1","Kitz_2","Kitz_3","Kitz_4","Kitz_5","Kitz_6","Kitz_7","Kitz_8","Kitz_9","Kitz_10","Sonstiges"]
    
        
class Pois(QtGui.QMainWindow):
    refresh = QtCore.pyqtSignal()
    liste =  QtCore.pyqtSignal(list)
    vislist = QtCore.pyqtSignal(list)
    clear = QtCore.pyqtSignal(bool)
    #loadimg = QtCore.pyqtSignal(str) #geht noch nicht !
    imgname = ""
    log = QtCore.pyqtSignal(str)
    id = 0
    poilist = []
    currentlist = []
    selected = []
    yaw_offset = 0
    pitch_offset = 0
    roll_offset = 0
    indir = ""
    flightid = 2
    
    def __init__(self,conf):
        QtGui.QMainWindow.__init__(self)
        uic.loadUi('ui/pois.ui',self)
        
        self.dialog = upload.UploadDialog("Upload")
        self.conf = conf
        self.view = QtGui.QTableView()
        self.setCentralWidget(self.view)
        header = self.view.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.Stretch)
        
        self.header = ["ID","File","Name","x","y","lat","lon","ele","uav_lat","uav_lon","uav_ele","uav_yaw","cam_pitch"]
        self.markerModel = MyTableModel(self,[],self.header)
        self.view.setModel(self.markerModel) #view is ein tableview aus pois.ui
        self.view.resizeColumnsToContents()
        self.view.resizeRowsToContents()
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.view.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        hv = self.view.horizontalHeader()
        hv.setResizeMode(QtGui.QHeaderView.Interactive)
        vwidth = self.view.verticalHeader().width()
        swidth = self.view.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent)
        fwidth = self.view.frameWidth() * 2
        #self.view.setFixedWidth(vwidth + 400 + swidth + fwidth)
        #for col in enumerate(self.header):
        #    self.view.setColumnWidth(col, self.view.width())
        
        self.refresh.connect(self.refreshtable)
        
        self.view.itemDelegate().closeEditor.connect(self.finishediting)
        self.selectionModel = self.view.selectionModel() 
        
        
        
        self.markerModel.layoutChanged.connect(lambda: QtCore.QTimer.singleShot(0, self.view.scrollToBottom))
        self.Cam = camera2.Camera()
        self.CamR = camera2.Camera()
        self.actionAllePois.triggered.connect(self.refreshtable)
        self.markerModel.fill([],self.header)
        
        self.delAction = QtGui.QAction('delpoi', self)
        self.delAction.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Delete))
        self.addAction(self.delAction)
        
        self.delAction.triggered.connect(self.delete_poi)
        self.actionReproMarker.triggered.connect(self.selectionhandler)
        self.selectionModel.selectionChanged.connect(self.selectionhandler)
        self.actionUpload.triggered.connect(lambda: self.dialog.openPropDialog(self.reload_poilist()))
        
        
        
    def selectionhandler(self):
        # Todo: diese Liste ist falsch, wenn man alle Pois anzeigen laesst (auch die , die nicht auf dem aktuellen Bild sichtbar sind)
        # die Zaehlreihenfolge entspricht der auf diesem Bild sichtbaren Pois 
        #print "selected"
        #print ("selectionhandler",self.poilist)
        
        pois_s = []
        selected = [index.row() for index in self.selectionModel.selectedRows()]
       # print "sel",selected
        #if len(selected)>0:
        #    print "selected",selected, self.imgname
        
        liste =  self.poilist if self.actionAllePois.isChecked() else self.currentlist # liste ist die in der table-view angezeigte liste
        
        for k,i in enumerate(liste):
            new_i = i[:]
            #print(i[1])
            if i[1] == self.imgname:
                if k in selected:
                    new_i.append(1)
                else:
                    new_i.append(0)
                pois_s.append(new_i)
    
       # print "liste:"#, pois_s    
        
###################################################################### das gehoert eigentlich wo anders hin       
       #reprojection of pois
        for i in self.poilist:
            if not i[1] == self.imgname:
                if self.actionReproMarker.isChecked():
                    point = self.reproject(i)
                    if point:
                        point[3],point[4] = self.checkcamorientation(point[3],point[4])
                        #print (point[3],point[4],self.CamR.position())
                        pois_s.append(point)
        
        self.liste.emit(pois_s) #diese liste wird in poi_tagger2.py von paint_pois abgefangen und gemalt
        #if self.actionReproMarker.isChecked(): 
        #    self.calc_poi_pos() 
#######################################################################

        
    def finishediting(self,cell):
        selected = [index.row() for index in self.selectionModel.selectedRows()][0]
        self.currentlist[selected][2] = cell.text()
        self.refresh.emit()
        
    def delete_poi(self):
        #print ("delete_poi",self.poilist)
        
        liste =  self.poilist if self.actionAllePois.isChecked() else self.currentlist
        #print(liste)
            
        selected = [index.row() for index in self.selectionModel.selectedRows()]
        
        if selected:
            selected = selected[0]
            self.poilist.remove(liste[selected])
            self.currentlist.remove(liste[selected])
            self.refresh.emit()
            try:
                last = [k for k,i in enumerate(reversed(liste)) if i[1]==self.imgname][0]
                self.view.selectRow(last)
            except:
                print("after delete: nothing in poilist")
            self.view.setFocus()
            
    def reload_poilist(self):
        #falls die Kalibrierung nach dem Setzen der Pois geschieht, wird hiermit die projektion in der poiliste korrigiert.
        myCam = camera2.Camera()
        print ("reload_poi",self.indir)
        
        reloaded_poilist = []
        for entry in self.poilist:
            filename = entry[1]
            x_geo,y_geo = self.checkcamorientation(entry[3],entry[4])
            curfilepath = os.path.join(self.indir,filename)
            #raw = flirsd.ConvertRaw(curfilepath)
            raw = image.Image.factory(curfilepath)
            if self.calib.actionEigeneWerte.isChecked():
                pitch_offset = self.calib.dlr_cam_pitch_offset_2.value()
                roll_offset = self.calib.dlr_cam_roll_offset_2.value()
                yaw_offset = self.calib.dlr_cam_yaw_offset_2.value()
            else:
                pitch_offset = ara.header["calibration"]["boresight"].get("cam_pitch_offset",0)
                roll_offset = ara.header["calibration"]["boresight"].get("cam_roll_offset",0)
                yaw_offset = ara.header["calibration"]["boresight"].get("cam_yaw_offset",0)
            
            myCam.pose(0,0,ara.header["uav"]["yaw"],ara.header["gps"].get("UTM_X",0),ara.header["gps"].get("UTM_Y",0),ara.header["gps"].get("rel_altitude",0))
            myCam.gimbal(roll=ara.header["camera"]["roll"],pitch=ara.header["camera"]["pitch"],yaw=ara.header["camera"]["yaw"],dx=0.2,dy=0,dz=0,dir="ZXY")
            myCam.boresight(self.yaw_offset, self.pitch_offset, self.roll_offset,0,0,0)
            myCam.intrinsics(640,512,1115,320,256)
            myCam.transform()
            lat,lon,ele = self.project(x_geo,y_geo,myCam)
            row = [entry[0],filename,entry[2],x_geo,y_geo,lat,lon,ele,entry[8],entry[9],entry[10],entry[11],entry[12],self.pitch_offset,self.roll_offset,self.yaw_offset, raw.header.gps_date+"T"+raw.header.gps_time, int(raw.header.start_hor_accur*1000) ]
            reloaded_poilist.append(row)
            
            
           # print "new",row
           # print "old",entry
        #print "---------------------"
        #print reloaded_poilist
        return reloaded_poilist
        
    def save(self):
        reloaded_poilist = self.reload_poilist()
        self.poisxml = ET.Element("pois")
        #self.poisxml.clear()
            
        for entry in reloaded_poilist:    
            p = ET.SubElement(self.poisxml,"poi")
            id = ET.SubElement(p,"id")
            filename = ET.SubElement(p,"filename")
            name = ET.SubElement(p,"name")
            px_x = ET.SubElement(p,"pixel_x")
            px_y = ET.SubElement(p,"pixel_y")
            
            lat = ET.SubElement(p,"latitude")
            lon = ET.SubElement(p,"longitude")
            ele = ET.SubElement(p,"elevation")
            
            uav_lat = ET.SubElement(p,"uav_latitude")
            uav_lon = ET.SubElement(p,"uav_longitude")
            uav_ele = ET.SubElement(p,"uav_elevation")
            uav_yaw = ET.SubElement(p,"uav_yaw")
            cam_pitch = ET.SubElement(p,"cam_pitch")
            
            pitch_offset = ET.SubElement(p,"pitch_offset")
            roll_offset = ET.SubElement(p,"roll_offset")
            yaw_offset = ET.SubElement(p,"yaw_offset")
            
            found_time = ET.SubElement(p,"found_time")
            
            id.text = str(entry[0])
            filename.text = str(entry[1])
            name.text = str(entry[2])
            px_x.text = str(entry[3])
            px_y.text = str(entry[4])
            lat.text = str(entry[5])
            lon.text = str(entry[6])
            ele.text = str(entry[7])
            uav_lat.text = str(entry[8])
            uav_lon.text = str(entry[9])
            uav_ele.text = str(entry[10])
            uav_yaw.text = str(entry[11])
            cam_pitch.text = str(entry[12])
            
            pitch_offset.text = str(entry[13])
            roll_offset.text  = str(entry[14])
            yaw_offset.text   = str(entry[15])
            found_time.text = str(entry[16])
        
   
    def load(self,pois,indir): #pois is elementlist from "flightmeta.xml"
        self.poisxml = pois
        self.indir = indir
        self.poilist = []
        if pois == None:
            return
        try:
            for poi in pois:
                #["ID","File","Name","x","y","lat","lon","ele","uav_lat","uav_lon","uav_ele","uav_yaw","cam_pitch"]
                self.poilist.append([poi["id"],poi["filename"],poi["name"],
                    poi["pixel_x"],poi["pixel_y"],poi["latitude"],poi["longitude"],
                    poi["elevation"],poi["uav_latitude"],poi["uav_longitude"],
                    poi["uav_elevation"],poi["uav_yaw"],poi["cam_pitch"]])
        except:
            traceback.print_exc()
        self.markerModel.fill(self.poilist,self.header)
      
    def refreshtable(self):
       # print ("refreshtable",self.poilist)
        
        if self.actionAllePois.isChecked():
        #    print("allePois")
            self.markerModel.fill(self.poilist,self.header)
        else:
       #     print("nur current list")
            self.markerModel.fill(self.currentlist,self.header)
      #  print ("refreshtable2",self.poilist)
            
        self.selectionhandler()    #hier wird die poiliste verarbeitet und danach emited
        self.view.resizeColumnsToContents()
        self.repaint()
        
        
    def reproject(self,poi):
    # Wir machen das hier nur , um in echtzeit aenderungen an yaw_offset, pitch_offset und roll_offset sichtbar zu machen
       # print("REPROJECT: ",poi)
        #print self.ara.header.gps_time
        #poi: [id,filename,name,x,y,lat,lon,ele,uav_lat,uav_lon,uav_ele,uav_yaw,cam_pitch]
        UTM_Y,UTM_X,ZoneNumber,ZoneLetter = utm.from_latlon(poi[8],poi[9])
        self.CamR.pose(0,0,poi[11],UTM_X,UTM_Y,poi[10])
        self.CamR.gimbal(roll=0,pitch=poi[12],yaw=0,dx=0.2,dy=0,dz=0,dir="ZXY")
        self.CamR.boresight(self.yaw_offset, self.pitch_offset, self.roll_offset,0,0,0)
        self.CamR.intrinsics(640,512,1115,320,256)
        self.CamR.transform()
        x_geo,y_geo = self.checkcamorientation(poi[3],poi[4])
        #x_geo = poi[3]
        #y_geo = poi[4]
        try:
            lat,lon,ele = self.project(x_geo,y_geo,self.CamR) #-------------------------------- bis hier hin
        except:
            lat,lon,ele = 0,0,0
            logging.error("reproject did not work", exc_info=True)
        #self.Cam.project()
        
        #print "latlon",lat,lon,ele,type(lat),type(lon),type(ele)
        u = utm.from_latlon(float(lat),float(lon))#,self.ara.header.ZoneNumber)
        
        V = np.array([[u[1]],[u[0]],[float(ele)],[1]])
       # print ("V",V, self.Cam.position(),self.Cam.R_gimbal,self.Cam.R_uav)
        X = self.Cam.project(V)
       # print ("X",X)
        if self.Cam.visible(X):
            q = []
            q[:] = poi[:]
            q[3] = X[0][0]
            q[4] = X[1][0]
            q.append(2)
            return q
            #            pois_vis.append(q)
            
            
    def load_data(self,ara,imgname,calib):
        """
        zu jedem Bild das geladen wird wird diese Methode aufgerufen
        """
        self.imgname = imgname
        self.calib = calib
        self.currentlist = [entry for entry in self.poilist if entry[1] == ara.filename] 
        try:
            
            if calib.actionEigeneWerte.isChecked():
                self.pitch_offset = calib.dlr_cam_pitch_offset_2.value()
                self.roll_offset = calib.dlr_cam_roll_offset_2.value()
                self.yaw_offset = calib.dlr_cam_yaw_offset_2.value()
            else:
                self.pitch_offset = ara.header["calibration"]["boresight"].get("cam_pitch_offset",0)
                self.roll_offset = ara.header["calibration"]["boresight"].get("cam_roll_offset",0)
                self.yaw_offset = ara.header["calibration"]["boresight"].get("cam_yaw_offset",0)
            self.ara = ara
            self.filename = ara.filename
      
            self.Cam.pose(0,0,ara.header["uav"]["yaw"],ara.header["gps"].get("UTM_X",0),ara.header["gps"].get("UTM_Y",0),ara.header["gps"].get("rel_altitude",0))
            self.Cam.gimbal(roll=ara.header["camera"]["roll"],pitch=ara.header["camera"]["pitch"],yaw=ara.header["camera"]["yaw"],dx=0.2,dy=0,dz=0,dir="ZXY")
            self.Cam.boresight(self.yaw_offset, self.pitch_offset, self.roll_offset,0,0,0)
            self.Cam.intrinsics(640,512,1115,320,256)
            self.Cam.transform()
            self.view.selectRow(len(self.currentlist)-1)
            self.view.setFocus()
            self.refresh.emit()
        except:
            logging.error("pois load data failed",exc_info=True)
        
    def checkcamorientation(self,x,y,width = 640, height = 512):
        #x_geo = x
        #y_geo = y
       # if self.conf.georef_fliphor_CB.isChecked():
       #     x_geo = width - x
       # else:
       #     x_geo = x
       # if self.conf.georef_flipver_CB.isChecked():
       #     y_geo = height - y
       # else:
       #     y_geo = y
       # return x_geo,y_geo
        return x,y
        
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
                        
    def pos(self,x,y): #set poi at current mouse position click
        x_geo,y_geo = self.checkcamorientation(x,y)
        try:
            if self.ara.header["calibration"].get("error_flags",0) & image.ERRORFLAGS.ALL_META: return
            uav_lat = self.ara.header["gps"].get("latitude",0)
            uav_lon = self.ara.header["gps"].get("longitude",0)
            uav_ele = self.ara.header["gps"].get("rel_altitude",0)
            uav_yaw = self.ara.header["uav"].get("yaw",0)
            cam_pitch = self.ara.header["camera"].get("pitch",0)
            pitch_offset = self.ara.header["calibration"]["boresight"].get("cam_pitch_offset",0)
            roll_offset  = self.ara.header["calibration"]["boresight"].get("cam_roll_offset",0)
            yaw_offset   = self.ara.header["calibration"]["boresight"].get("cam_yaw_offset",0)
        except:
            logging.error("pois pos(): load header data failed")
            return
        self.id = self.id+1
        try:
            lat,lon,ele = self.project(x_geo,y_geo,self.Cam)
        except:
            lat,lon,ele = 0,0,0

        try:
            self.log.emit("ID: %d, File: %s, X: %d, Y: %d, X_geo: %d, Y_geo: %d, lat: %s, lon: %s, ele: %s" %(self.id,self.ara.filename, x,y,x_geo, y_geo,lat,lon,ele)  )
            self.poilist.append([self.id,self.ara.filename, "xxx", x,y,float(lat),float(lon),float(ele),uav_lat,uav_lon,uav_ele,uav_yaw,cam_pitch,pitch_offset, roll_offset, yaw_offset])
            self.currentlist = [entry for entry in self.poilist if entry[1] == self.ara.filename] 
            idx = self.markerModel.index(len(self.currentlist)-1,0)
            self.refresh.emit()
            self.view.resizeColumnsToContents()
            self.view.selectRow(len(self.currentlist)-1)
            self.view.setFocus()
        except:    
            logging.error("pois set pos did not work",exc_info=True)
    
        
    def save_gpx(self):
        try:
            self.save()
            #self.write_pois_to_xml()
        except:
            pass

            
    def loadSettings(self, settings):
        self.settings = settings
        self.dialog.loadSettings(settings)
        
    def writeSettings(self):
        pass
            
class MyTableModel(QtCore.QAbstractTableModel):
    mylist = []
    def __init__(self, parent, mylist, header, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.header = header
    
    def fill(self, mylist, header):
        self.beginResetModel()
        self.mylist.clear()
        
        self.endResetModel()
        self.mylist = mylist[:]
        self.header = header
        
        self.layoutChanged.emit()
        
    def rowCount(self, parent):
        return len(self.mylist)
    def remove_all(self,parent):
        self.beginResetModel()
        self.mylist.clear()
        self.endResetModel()
        
    def columnCount(self, parent):
        try:
            return len(self.mylist[0])
        except:
            return 0
    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        return self.mylist[index.row()][index.column()]
    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            #print self.header
            try:
                return self.header[col]
            except:
              #  print "HeaderData error"
                return None
        return None
    def sort(self, col, order):
        """sort table by given column number col"""
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.mylist = sorted(self.mylist,
            key=operator.itemgetter(col))
        if order == QtCore.Qt.DescendingOrder:
            self.mylist.reverse()
        self.emit(SIGNAL("layoutChanged()"))
    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    ara = flirsd.ConvertRaw("test/5_0210001.ARA")
    w = Pois(ara)
    clear = QtGui.QPushButton("clear",w)
    clear.move(0,200)
    clear.clicked.connect(w.clear)
    w.resize(300, 250)
    w.move(300, 300)
    w.show()
    sys.exit(app.exec_())
    