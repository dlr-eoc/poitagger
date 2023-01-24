from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QWidget,QDialog
import ast
import pyqtgraph as pg
import os
from .. import PATHS 
from .. import CONF

class GpxProperties(QWidget):
    def __init__(self):
        QDialog.__init__(self)
        uic.loadUi(os.path.join(PATHS["PROPERTIES"],'gpx_export.ui'),self)
        self.label.setText("mit dieser Übertragungsart können die Pois z.B. auf ältere Garmin Geräte übertragen <br>werden. <a href='https://www.gpsbabel.org/'>GPSBabel</a> muss separat installiert werden.")   
        self.label.setOpenExternalLinks(True)
        self.connections()
        
    def connections(self):
        self.gpsbabelTB.clicked.connect(self.ChoosePath)
        
    def ChoosePath(self,x):
        self.babelpath = QFileDialog.getOpenFileName(self, "Select GPSBabel binary",self.gpsbabelLE.text())[0]
        self.gpsbabelLE.setText(self.babelpath)
    
    def loadSettings(self):
        self.gpsbabelLE.setText(CONF["GPX"]["gpsbabel"])
        
    
    def writeSettings(self):
        CONF["GPX"]["gpsbabel"] = str(self.gpsbabelLE.text())
        
       
        