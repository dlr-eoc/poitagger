from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
import ast
import pyqtgraph as pg
from . import pois_conf,gps_conf,image_conf

class PropertyDialog(QtGui.QDialog):
   
    def __init__(self,title):
        QtGui.QDialog.__init__(self)
        uic.loadUi('properties/properties.ui',self)
        self.setWindowTitle(title)
        
        
        self.settings = QtCore.QSettings("conf.ini", QtCore.QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False) 
        
        self.poisproperties = pois_conf.PoisProperties(self.settings)
        self.gpsproperties = gps_conf.GpsProperties(self.settings)
        self.imageproperties = image_conf.ImageProperties(self.settings)
        self.tabWidget.addTab(self.poisproperties,"Pois")
        self.tabWidget.addTab(self.gpsproperties,"GPS-Device")
        self.tabWidget.addTab(self.imageproperties,"Image")
        self.ConfWidgetList = [self.poisproperties,self.gpsproperties,self.imageproperties]
        
        self.connections()
        
        self.loadSettings(self.ConfWidgetList)
        
    def connections(self):
        pass
        
    def openPropDialog(self):
        self.setModal(False)
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
        