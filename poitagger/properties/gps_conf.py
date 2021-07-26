from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
import ast
import pyqtgraph as pg
import os
from .. import PATHS 
from .. import CONF

class GpsProperties(QtGui.QWidget):
    
    def __init__(self):
        QtGui.QDialog.__init__(self)
        uic.loadUi(os.path.join(PATHS["PROPERTIES"],'gps_conf.ui'),self)
        self.connections()
        
    def connections(self):
        pass
        
    def loadSettings(self):
        self.name_LE.setText(CONF["GPS-DEVICE"]["devicename"])
        self.harddrive_LE.setText(CONF["GPS-DEVICE"]["harddrive"])
        self.folder_LE.setText(CONF["GPS-DEVICE"]["gpxfolder"])
        
        exporttype = CONF["GPS-DEVICE"]["exportType"]
        detectmode = CONF["GPS-DEVICE"]["detectMode"]

        if exporttype == "serial":
            self.garminserial_rB.setChecked(True)
        elif exporttype == "massStorage":
            self.massStorage_rB.setChecked(True)
        
        if detectmode == "name":
            self.detectName_rB.setChecked(True)
        elif detectmode == "fixedfolder":
            self.fixedFolder_rB.setChecked(True)
        
    
    def writeSettings(self):
        if self.garminserial_rB.isChecked():
            exporttype = "serial"
        elif self.massStorage_rB.isChecked():
            exporttype = "massStorage"
        else:
            exporttype = "None"
        
        if self.detectName_rB.isChecked():
            detectmode = "name"
        elif self.fixedFolder_rB.isChecked():
            detectmode = "fixedfolder"
        else:
            detectmode = "None"
        
        CONF["GPS-DEVICE"]["exportType"] = exporttype
        CONF["GPS-DEVICE"]["detectMode"] = detectmode
        CONF["GPS-DEVICE"]["devicename"] = str(self.name_LE.text())
        CONF["GPS-DEVICE"]["harddrive"] = str(self.harddrive_LE.text())
        CONF["GPS-DEVICE"]["gpxfolder"] = str(self.folder_LE.text())
        
       
        