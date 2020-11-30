from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
import ast
import pyqtgraph as pg
import os
from .. import PATHS 
class PoisProperties(QtGui.QWidget):
    poicolor = "#ffff00"
    poicolor2 = "##0055ff"
    poicolor_repro = "#005500"
   
    def __init__(self,settings):
        QtGui.QDialog.__init__(self)
        uic.loadUi(os.path.join(PATHS["PROPERTIES"],'pois_conf.ui'),self)
        self.settings = settings
        
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
        
    def loadSettings(self,s):
        self.settings = s
        self.setColor(self.poicolor,s.value('POIS/color',"#ff0000"))
        self.size.setValue(int(s.value('POIS/size',"30")))
        self.setColor(self.poicolor_repro,s.value('POIS/color_repro',"#0000ff"))
        self.defaultname.setText(s.value('POIS/defaultname',""))
        
    def writeSettings(self):
        self.settings.setValue('POIS/color',str(self.poicolor.color.name()))
        self.settings.setValue('POIS/color_repro',str(self.poicolor_repro.color.name()))
        self.settings.setValue('POIS/size',str(self.size.value()))
        self.settings.setValue('POIS/defaultname',str(self.defaultname.text()))
        
       
        