from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
import ast
import os
import pyqtgraph as pg
from . import pois_conf,gps_conf,image_conf,geoview_conf
from .. import PATHS 
class PropertyDialog(QtGui.QDialog):
   
    def __init__(self,title):
        QtGui.QDialog.__init__(self)
        uic.loadUi(os.path.join(PATHS["PROPERTIES"],'properties.ui'),self)
        self.setWindowTitle(title)
        
        
        self.settings = QtCore.QSettings(os.path.join(PATHS["BASE"],"conf.ini"), QtCore.QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False) 
        
        self.poisproperties = pois_conf.PoisProperties(self.settings)
        self.gpsproperties = gps_conf.GpsProperties(self.settings)
        self.imageproperties = image_conf.ImageProperties(self.settings)
        self.geoviewproperties = geoview_conf.GeoviewProperties(self.settings)
        self.tabWidget.addTab(self.poisproperties,"Pois")
        self.tabWidget.addTab(self.gpsproperties,"GPS-Device")
        self.tabWidget.addTab(self.imageproperties,"Image")
        self.tabWidget.addTab(self.geoviewproperties,"Geoview")
        self.ConfWidgetList = [self.poisproperties,self.gpsproperties,self.imageproperties,self.geoviewproperties]
        
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
        [i.loadSettings(self.settings) for i in lst]
        
    def writeSettings(self,lst):
        [i.writeSettings() for i in lst]
        