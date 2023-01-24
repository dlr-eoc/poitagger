from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtWidgets import QWidget,QDialog,QColorDialog,QFileDialog
import ast
import pyqtgraph as pg
import os
from .. import PATHS 

class GpxProperties(QWidget):
    def __init__(self,settings):
        QDialog.__init__(self)
        uic.loadUi(os.path.join(PATHS["PROPERTIES"],'gpx_export.ui'),self)
        self.settings = settings
        self.label.setText("mit dieser Übertragungsart können die Pois z.B. auf ältere Garmin Geräte übertragen <br>werden. <a href='https://www.gpsbabel.org/'>GPSBabel</a> muss separat installiert werden.")   
        self.label.setOpenExternalLinks(True)
        self.connections()
        
    def connections(self):
        self.gpsbabelTB.clicked.connect(self.ChoosePath)
        
    def ChoosePath(self,x):
        self.babelpath = QFileDialog.getOpenFileName(self, "Select GPSBabel binary",self.gpsbabelLE.text())[0]
        self.gpsbabelLE.setText(self.babelpath)
    
    def loadSettings(self,s):
        self.settings = s
        self.gpsbabelLE.setText(s.value('GPX/gpsbabel'))
        
    
    def writeSettings(self):
        pass
        self.settings.setValue('GPX/gpsbabel',str(self.gpsbabelLE.text()))
        
       
        