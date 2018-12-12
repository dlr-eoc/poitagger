from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
import ast
import os
import pyqtgraph as pg
from .. import PATHS 
class GeoviewProperties(QtGui.QWidget):
    
    def __init__(self,settings):
        QtGui.QDialog.__init__(self)
        uic.loadUi(os.path.join(PATHS["PROPERTIES"],'geoview_conf.ui'),self)
        self.settings = settings
        self.label.setText("<a href='https://www.mapbox.com/signup/'>Create a Mapbox Account</a>")
        self.connections()
        
    def connections(self):
        pass
        
    def loadSettings(self,s):
        self.settings = s
        self.token.setText(s.value('GEOVIEW/mapboxtoken'))
        self.style.setText(s.value('GEOVIEW/mapboxstyle'))
     
    def writeSettings(self):
        self.settings.setValue('GEOVIEW/mapboxtoken',str(self.token.text()))
        self.settings.setValue('GEOVIEW/mapboxstyle',str(self.style.text()))
        
       
        