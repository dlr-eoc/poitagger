from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
import ast
import pyqtgraph as pg
import os
from .. import PATHS 
from .. import CONF
class PoisProperties(QtGui.QWidget):
    poicolor = "#ffff00"
    poicolor2 = "##0055ff"
    poicolor_repro = "#005500"
   
    def __init__(self):
        QtGui.QDialog.__init__(self)
        uic.loadUi(os.path.join(PATHS["PROPERTIES"],'pois_conf.ui'),self)
        
        self.colorChooser = QtGui.QColorDialog()
        #self.maskColbtn = pg.ColorButton()
        
        self.connections()
        
    def connections(self):
        self.changeColor.pressed.connect(lambda: self.selectColor(self.poicolor))
        self.changeColor3.pressed.connect(lambda: self.selectColor(self.poicolor_repro))
        self.colorChooser.colorSelected.connect(self.receiveColor)
        
         
    def setColor(self,label,color):
        if type(color) in [str]:
            color = QtGui.QColor(color)
        label.setStyleSheet("QLabel { background-color : %s; }" % color.name());
        label.color = color
        
    def selectColor(self,label):
        self.selectedColorLabel = label
        self.colorChooser.open()
    
    def receiveColor(self,col):
        self.setColor(self.selectedColorLabel,col)
        
    def loadSettings(self):
        self.setColor(self.poicolor,CONF["POIS"]["color"])
        self.size.setValue(int(CONF["POIS"]["size"]))
        self.setColor(self.poicolor_repro,CONF["POIS"]["color_repro"])
        self.defaultname.setText(CONF["POIS"]["defaultname"])
        
    def writeSettings(self):
        CONF["POIS"]["color"] = str(self.poicolor.color.name())
        CONF["POIS"]["color_repro"] = str(self.poicolor_repro.color.name())
        CONF["POIS"]["size"] = str(self.size.value())
        CONF["POIS"]["defaultname"] = str(self.defaultname.text())
        
       
        