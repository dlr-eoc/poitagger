from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
import ast
import os
import pyqtgraph as pg
from .. import PATHS 
from .. import CONF
class GeoviewProperties(QtGui.QWidget):
    
    def __init__(self):
        QtGui.QDialog.__init__(self)
        uic.loadUi(os.path.join(PATHS["PROPERTIES"],'geoview_conf.ui'),self)
        self.label.setText("<a href='https://www.mapbox.com/signup/'>Create a Mapbox Account</a>")
        self.connections()
        
    def connections(self):
        pass
        
    def loadSettings(self):
        self.token.setText(CONF["GEOVIEW"]["mapboxtoken"])
        self.style.setText(CONF["GEOVIEW"]["mapboxstyle"])
     
    def writeSettings(self):
        CONF["GEOVIEW"]["mapboxtoken"] = str(self.token.text())
        CONF["GEOVIEW"]["mapboxstyle"] = str(self.style.text())
        
       
        