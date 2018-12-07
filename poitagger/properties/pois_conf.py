from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
import ast
import pyqtgraph as pg

class PoisProperties(QtGui.QWidget):
    poicolor = "#ffff00"
    poicolor2 = "##0055ff"
    poicolor_repro = "#005500"
   
    def __init__(self,settings):
        QtGui.QDialog.__init__(self)
        uic.loadUi('properties/pois_conf.ui',self)
        self.settings = settings
        
        self.colorChooser = QtGui.QColorDialog()
        #self.maskColbtn = pg.ColorButton()
        
        self.connections()
        
    def connections(self):
        self.changeColor.pressed.connect(lambda: self.selectColor(self.poicolor))
        self.changeColor2.pressed.connect(lambda: self.selectColor(self.poicolor2))
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
        
    def loadSettings(self,s):
        self.settings = s
        self.setColor(self.poicolor,s.value('POIS/color'))
        self.setColor(self.poicolor2,s.value('POIS/color2'))
        self.setColor(self.poicolor_repro,s.value('POIS/color_repro'))
    
    def writeSettings(self):
        self.settings.setValue('POIS/color',str(self.poicolor.color.name()))
        self.settings.setValue('POIS/color2',str(self.poicolor2.color.name()))
        self.settings.setValue('POIS/color_repro',str(self.poicolor_repro.color.name()))
        
       
        