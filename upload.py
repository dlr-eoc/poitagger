from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
import ast
import requests
import simplejson as json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import traceback


import pyqtgraph as pg

class UploadDialog(QtGui.QDialog):
    
    def __init__(self,title):
        QtGui.QDialog.__init__(self)
        uic.loadUi('ui/upload.ui',self)
        self.setWindowTitle(title)
        self.connections()
        #self.setCalib()
        
    def connections(self):
        self.sessionButton.pressed.connect(self.createSession)
        self.flightPathButton.pressed.connect(self.postFlightPath)
        self.poisUploadButton.pressed.connect(self.uploadPois)
        
    def openPropDialog(self, poilist):
        self.poilist = poilist
        self.setModal(False)
        self.show()
    
    
    def uploadPois(self):
        Myjson = {"key":"aowlsdf32350adfwerl4svKER231Edas","pois":[]}#,"debug":"True"
        for i in self.poilist:
            Myjson["pois"].append({"POI_PTFK":1, "POI_Reliability":50, "POI_ImageSrc":i[1], "POI_Comment":"",
                    "POI_FFK":self.flightid,"POI_PFBFK":1,"POI_Found_Timestamp":i[16].replace("T"," "),
                    "POI_Found_at_Flight_Height":i[10],
                    "POI_Point":"ST_GeomFromText('POINT({} {})',4326)".format(i[6],i[5]),
                    "POI_Label":i[0],"POI_Name":i[2],"POI_GPS_Accuracy":i[17]})
            
        url = "http://wildretter.caf.dlr.de/poitaggerbridge/jsonread.php"
        headers = {'Content-type': 'application/json'}
        try:
            r = requests.post(url, data=json.dumps(Myjson), headers=headers)
            print (r.content)
            QtGui.QMessageBox.information(self, "Pois-Upload","Die Uebertragung von {} Pois war erfolgreich! Die Punkte koennen jetzt mit Hilfe der Wildretter-App aufgesucht werden. Sessionnr: {}".format(len(Myjson["pois"]),self.sessionid)); 
        
        except:
            QtGui.QMessageBox.critical(self, "Pois-Upload fehlgeschlagen!","Der Upload von {} Pois hat leider nicht funktioniert! ".format(len(Myjson))); 
            traceback.print_exc()
        
        
    def createSession(self):
        url = 'http://wildretter.caf.dlr.de/poitaggerbridge/insertsession.php' # Set destination URL here
        post_fields = {'Key':'aowlsdf32350adfwerl4svKER231Edas','SES_GTFK':'1','SES_WFK':'1','SES_FWRFK':'1','SES_Comment':'Kommentar','SES_Point':"ST_GeomFromText('POINT(10.820 47.181)', 4326)",'SES_Area':"NULL",'SES_Name':"Test"}     # Set POST fields here
        try:
            request = Request(url, urlencode(post_fields).encode())
            content = urlopen(request).read()
            self.sessionid = str(int(content))
            self.SessionID.insert(self.sessionid)    
            QtGui.QMessageBox.information(self, "Create Session","Die Erzeugung einer Session hat geklappt!. Sessionnr: {}".format(self.sessionid)); 
            
        except:
            QtGui.QMessageBox.critical(self, "Create Session fehlgeschlagen!","Die Erzeugung einer neuen Session hat leider nicht funktioniert! \r\n Fehlermeldung: {}".format(len(Myjson), content)); 
            traceback.print_exc()
        
        
        
        
    def postFlightPath(self):   #noch nicht fertig!
        url = 'http://wildretter.caf.dlr.de/poitaggerbridge/insertflightpath.php' # Set destination URL here
        post_fields = {'Key':'aowlsdf32350adfwerl4svKER231Edas','F_Start':'2018-04-30 12:01:45','F_Stop':'2018-04-30 12:24:23','F_Comment':'Kommentar x','F_SESFK':self.SessionID.text(), 'F_Number':'1', 'F_Path':"NULL",'F_Track':"NULL",'F_TimeTrack':"NULL"}     # Set POST fields here
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
        url = 'http://wildretter.caf.dlr.de/poitaggerbridge/insertpois.php' # Set destination URL here
        post_fields = {'Key':'aowlsdf32350adfwerl4svKER231Edas','POI_PTFK': '1','POI_Reliability':'50','POI_ImageSrc':'','POI_Comment':'No Comment','POI_FFK':self.FlightID.text(),'POI_PFBFK':'1','POI_Found_Timestamp':'2018-04-12 12:30:00','POI_Found_at_Flight_Height': '79.45','POI_Point':"ST_GeometryFromText ( 'POINT (11.282862 48.088271)', 4326 )", 'POI_Label':'1','POI_Name':'k1', 'POI_GPS_Accuracy':'1'}     # Set POST fields here
        request = Request(url, urlencode(post_fields).encode())
        json = urlopen(request).read()#.decode()
        print(json)
             
        
    def loadSettings(self,settings):
        #camserial = str(self.camcalib.value('GENERAL/camserial'))
        #badpxl_v = ast.literal_eval(str(self.camcalib.value('DEAD_PIXEL/bad_pixels_v',"[]")))
        pass
        
    def writeSettings(self):
#        camserial = str(self.camcalib.value('GENERAL/camserial'))
#        badpxl_v = ast.literal_eval(str(self.camcalib.value('DEAD_PIXEL/bad_pixels_v',"[]")))
        pass
        
#    def onSearch(self):
        #path = QtGui.QFileDialog.getOpenFileName(self, "eine Kamera Kalibrier-Datei waehlen", self.DeadPixelpathBox.text(), "Calibration File (*.ini)")
        #if path == "":
        #    return
        #else:
        #    self.DeadPixelpathBox.setText(path)
        #    self.calibfile = path    
        #    self.camcalib = QtCore.QSettings(path, QtCore.QSettings.IniFormat)
        #    self.setCalib()