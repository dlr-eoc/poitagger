from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtWidgets import QDialog
import ast
import os
import pyqtgraph as pg
from . import pois_conf,gps_conf,image_conf,geoview_conf,gpx_conf
from .. import PATHS 
from .. import CONF 

class PropertyDialog(QDialog):
   
    def __init__(self,title):
        QDialog.__init__(self)
        uic.loadUi(os.path.join(PATHS["PROPERTIES"],'properties.ui'),self)
        self.setWindowTitle(title)
        
        self.pois = pois_conf.PoisProperties()
        self.gps = gps_conf.GpsProperties()
        self.gpx = gpx_conf.GpxProperties()
        self.image = image_conf.ImageProperties()
        self.geoview = geoview_conf.GeoviewProperties()
        self.tabWidget.addTab(self.pois,"Pois")
        self.tabWidget.addTab(self.gps,"GPS-Device")
        self.tabWidget.addTab(self.gpx,"GPX")
        self.tabWidget.addTab(self.image,"Image")
        self.tabWidget.addTab(self.geoview,"Map")
        self.ConfWidgetList = [self.pois,self.gps,self.gpx,self.image,self.geoview]
        
        self.connections()
        
        self.loadSettings(self.ConfWidgetList)
        self.setModal(True)
        
        
    def connections(self):
        pass
        
    def openPropDialog(self):
       # self.setModal(False)
        self.show()
    
    def accept(self):
        self.writeSettings(self.ConfWidgetList)
        self.hide()
    
    def reject(self):
        self.hide()
        
    def loadSettings(self,lst):
        [i.loadSettings() for i in lst]
        
    def writeSettings(self,lst):
        [i.writeSettings() for i in lst]
        