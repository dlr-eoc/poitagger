from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtWidgets import QWidget,QDialog
import ast
import pyqtgraph as pg
import os
from .. import PATHS 

class GpsProperties(QWidget):
    
    def __init__(self,settings):
        QDialog.__init__(self)
        uic.loadUi(os.path.join(PATHS["PROPERTIES"],'gps_conf.ui'),self)
        self.settings = settings
        
        self.connections()
        
    def connections(self):
        pass
        
    def loadSettings(self,s):
        self.settings = s
    
        self.name_LE.setText(s.value('GPS-DEVICE/devicename'))
        self.harddrive_LE.setText(s.value('GPS-DEVICE/harddrive'))
        self.folder_LE.setText(s.value('GPS-DEVICE/gpxfolder'))
        
        exporttype = s.value('GPS-DEVICE/exportType')
        detectmode = s.value('GPS-DEVICE/detectMode')

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
        
        self.settings.setValue('GPS-DEVICE/exportType',exporttype)
        self.settings.setValue('GPS-DEVICE/detectMode',detectmode)
        self.settings.setValue('GPS-DEVICE/devicename',str(self.name_LE.text()))
        self.settings.setValue('GPS-DEVICE/harddrive',str(self.harddrive_LE.text()))
        self.settings.setValue('GPS-DEVICE/gpxfolder',str(self.folder_LE.text()))
        
       
        