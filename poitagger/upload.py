from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtWidgets import QApplication
import ast
import requests
import simplejson as json
from urllib.parse import urlencode
#import urllib.parse
from urllib.request import Request, urlopen
import traceback
import os
from . import PATHS

import pyqtgraph as pg

class UploadDialog(QtGui.QDialog):

    def __init__(self,title,settings):
        QtGui.QDialog.__init__(self)
        self.settings = settings
        uic.loadUi(os.path.join(PATHS["UI"],'upload.ui'),self)
        self.setWindowTitle(title)
        self.connections()
        self.loadSettings(settings)
        #self.setCalib()

    def connections(self):
        self.sessionButton.pressed.connect(self.createSession)
        self.flightPathButton.pressed.connect(self.postFlightPath)
        self.poisUploadButton.pressed.connect(self.uploadPois)
        self.visitButton.pressed.connect(self.loadWebsite)
        self.insertButton.pressed.connect(self.insertFromClipboard)
        
    def insertFromClipboard(self):
        #text = QApplication.clipboard().text()
        #print(text)
        self.key.clear()
        self.key.paste()
        
    def loadWebsite(self):
        try:
            url = QtCore.QUrl(self.server.text())
            QtGui.QDesktopServices.openUrl(url)
        except:
            logger.error("loadWebsite failed!")
            
    def openPropDialog(self, poilist):
        self.poilist = poilist
        self.setModal(False)
        self.show()

        
    def uploadPois(self):
      #                 0   1       2       3 4    5    6       7   8           9           10      11      12
      #self.header = ["ID","File","Name","x","y","lat","lon","ele","uav_lat","uav_lon","uav_ele","uav_yaw","cam_pitch"]
      #13                       14              15              16                                              17
      #self.pitch_offset,self.roll_offset,self.yaw_offset, raw.header.gps_date+"T"+raw.header.gps_time, int(raw.header.start_hor_accur*1000) ]


       # self.pois.append({"name":poi.name(),"x":val[0],"y":val[1],"layer":L.name(),
                                # "filename":view.name(),
                                # "lat":float(view.opts.get("latitude",0)),
                                # "lon":float(view.opts.get("longitude",0)),
                                # "ele":float(view.opts.get("elevation",0)),
                                # "uav_lat":float(view.opts["uav_lat"]),
                                # "uav_lon":float(view.opts["uav_lon"]),
                                # "uav_ele":float(view.opts["uav_ele"]),
                                # "cam_yaw":float(view.opts["cam_yaw"]),
                                # "cam_pitch":float(view.opts["cam_pitch"]),
                                # "cam_roll":float(view.opts["cam_roll"]),
                                # "cam_euler_order":view.opts["cam_euler_order"],
                                # "boresight_pitch":float(view.opts["boresight_pitch"]),
                                # "borsight_roll":float(view.opts["boresight_roll"]),
                                # "boresight_yaw":float(view.opts["boresight_yaw"]),
                                # "boresight_euler_order":view.opts["boresight_euler_order"],
                                # "found_time":view.opts["found_time"]})

        Myjson = {"key":self.keystr,"pois":[]}#,"debug":"True"
        for k,i in enumerate(self.poilist):
            Myjson["pois"].append({"POI_PTFK":1, "POI_Reliability":50, "POI_ImageSrc":i["filename"], "POI_Comment":"",
                    "POI_FFK":self.flightid,"POI_PFBFK":1,"POI_Found_Timestamp":i["found_time"].replace("T"," "),
                    "POI_Found_at_Flight_Height":i["uav_ele"],
                    "POI_Point":"ST_GeomFromText('POINT({} {})',4326)".format(i["lon"],i["lat"]),
                    "POI_Label":k,"POI_Name":i["name"],"POI_GPS_Accuracy":0})
        # for i in self.poilist:
            # Myjson["pois"].append({"POI_PTFK":1, "POI_Reliability":50, "POI_ImageSrc":i[1], "POI_Comment":"",
                    # "POI_FFK":self.flightid,"POI_PFBFK":1,"POI_Found_Timestamp":i[16].replace("T"," "),
                    # "POI_Found_at_Flight_Height":i[10],
                    # "POI_Point":"ST_GeomFromText('POINT({} {})',4326)".format(i[6],i[5]),
                    # "POI_Label":i[0],"POI_Name":i[2],"POI_GPS_Accuracy":i[17]})

        # url = "http://wildretter.caf.dlr.de/poitaggerbridge/jsonread.php"
        
        #host = str(self.settings.value('WILDRETTERAPP/url'))
        url = self.hoststr + 'apis/upload_pois'
        headers = {'Content-type': 'application/json'}
        try:
            r = requests.post(url, data=json.dumps(Myjson), headers=headers)
            print (r.content)
            QtGui.QMessageBox.information(self, "Pois-Upload","Die Uebertragung von {} Pois war erfolgreich! Die Punkte koennen jetzt mit Hilfe der Wildretter-App aufgesucht werden. Sessionnr: {}".format(len(Myjson["pois"]),self.sessionid));

        except:
            QtGui.QMessageBox.critical(self, "Pois-Upload fehlgeschlagen!","Der Upload von {} Pois hat leider nicht funktioniert! ".format(len(Myjson)));
            traceback.print_exc()


    def createSession(self):
        
        # url = 'http://wildretter.caf.dlr.de/poitaggerbridge/insertsession.php' # Set destination URL here
        
        url = self.hoststr + 'apis/create_session'
        print ("create_session",url)
        post_fields = {'Key':self.keystr,'SES_GTFK':'1','SES_WFK':'1','SES_FWRFK':'1','SES_Comment':'Kommentar','SES_Point':"ST_GeomFromText('POINT(10.820 47.181)', 4326)",'SES_Area':"NULL",'SES_Name':"Test"}     # Set POST fields here
        # url = 'https://td.programmiera.de/apis/create_session'
        # post_fields = {'Key':'1cea2d29f7f91c000da772c5b00fc8fc94a979df980ce5f572dd01280775986f','SES_GTFK':'1','SES_WFK':'1','SES_FWRFK':'1','SES_Comment':'Kommentar','SES_Point':"ST_GeomFromText('POINT(10.820 47.181)', 4326)",'SES_Area':"NULL",'SES_Name':"Test"}     # Set POST fields here
        content = ""
        try:
            request = Request(url, urlencode(post_fields).encode())
            content = urlopen(request).read()
            print(content)
            self.sessionid = str(int(content))
            self.SessionID.insert(self.sessionid)
            QtGui.QMessageBox.information(self, "Create Session","Die Erzeugung einer Session hat geklappt!. Sessionnr: {}".format(self.sessionid));

        except:
            QtGui.QMessageBox.critical(self, "Create Session fehlgeschlagen!","Die Erzeugung einer neuen Session hat leider nicht funktioniert! \r\n Fehlermeldung: {}".format(len(post_fields), content));
            traceback.print_exc()




    def postFlightPath(self):   #noch nicht fertig!
        # url = 'http://wildretter.caf.dlr.de/poitaggerbridge/insertflightpath.php' # Set destination URL here
        #url = 'https://td.programmiera.de/apis/post_flight_path'
        #host = str(self.settings.value('WILDRETTERAPP/url'))
        url = self.hoststr + 'apis/post_flight_path'
        post_fields = {'Key':self.keystr,'F_Start':'2018-04-30 12:01:45','F_Stop':'2018-04-30 12:24:23','F_Comment':'Kommentar x','F_SESFK':self.SessionID.text(), 'F_Number':'1', 'F_Path':"NULL",'F_Track':"NULL",'F_TimeTrack':"NULL"}     # Set POST fields here
        try:
            request = Request(url, urlencode(post_fields).encode())
            content = urlopen(request).read()
            #print(content)
            flightid = str(int(content))
            self.FlightID.insert(flightid)
            self.flightid = flightid

            QtGui.QMessageBox.information(self, "Upload Flugpfad","Der Upload des Flugpfads hat geklappt!. Flugnr: {}".format(self.flightid));

        except:
            QtGui.QMessageBox.critical(self, "Upload Flugpfad fehlgeschlagen!","Der Upload des Flugpfads hat leider nicht funktioniert! \r\n Fehlermeldung: {}".format(content));
            traceback.print_exc()

    def postPois(self):
        #rot, Version 2012_1	DLR	Asctec, Falcon 8	 	Sensoren: IR-CAM: Tau640 , RGB-CAM: e-Cam50
        # url = 'http://wildretter.caf.dlr.de/poitaggerbridge/insertpois.php' # Set destination URL here
       # url = 'https://td.programmiera.de/apis/post_pois'
        url = self.hoststr + 'apis/post_pois'
        print(url)
        post_fields = {'Key':self.keystr,'POI_PTFK': '1','POI_Reliability':'50','POI_ImageSrc':'','POI_Comment':'No Comment','POI_FFK':self.FlightID.text(),'POI_PFBFK':'1','POI_Found_Timestamp':'2018-04-12 12:30:00','POI_Found_at_Flight_Height': '79.45','POI_Point':"ST_GeometryFromText ( 'POINT (11.282862 48.088271)', 4326 )", 'POI_Label':'1','POI_Name':'k1', 'POI_GPS_Accuracy':'1'}     # Set POST fields here
        request = Request(url, urlencode(post_fields).encode())
        json = urlopen(request).read()#.decode()
        print(json)


    def loadSettings(self,settings):
        self.hoststr = str(self.settings.value('WILDRETTERAPP/url'))
        self.keystr = str(self.settings.value('WILDRETTERAPP/key'))
        if self.hoststr == None:
            self.hoststr = "https://td.programmiera.de/"
        self.server.insert(self.hoststr)
        self.key.insert(self.keystr)
        
    def writeSettings(self):
        print("write Settings UploadDialog")
        self.settings.setValue('WILDRETTERAPP/url', str(self.server.text()))
        self.settings.setValue('WILDRETTERAPP/key', str(self.key.text()))
        
#    def onSearch(self):
        #path = QtGui.QFileDialog.getOpenFileName(self, "eine Kamera Kalibrier-Datei waehlen", self.DeadPixelpathBox.text(), "Calibration File (*.ini)")
        #if path == "":
        #    return
        #else:
        #    self.DeadPixelpathBox.setText(path)
        #    self.calibfile = path
        #    self.camcalib = QtCore.QSettings(path, QtCore.QSettings.IniFormat)
        #    self.setCalib()

