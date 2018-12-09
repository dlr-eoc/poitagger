from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
import ast
import pyqtgraph as pg

class GeoviewProperties(QtGui.QWidget):
    
    def __init__(self,settings):
        QtGui.QDialog.__init__(self)
        uic.loadUi('poitagger/properties/geoview_conf.ui',self)
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
        
       
        