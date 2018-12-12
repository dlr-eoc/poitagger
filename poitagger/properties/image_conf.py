from __future__ import print_function
from PyQt5 import QtCore, QtGui, uic
import ast
import pyqtgraph as pg
import os
from .. import PATHS 

class ImageProperties(QtGui.QWidget):
    a = 255
    b = 0
    g = 255
    r = 0
    
   
    def __init__(self,settings):
        QtGui.QDialog.__init__(self)
        uic.loadUi(os.path.join(PATHS["PROPERTIES"],'image_conf.ui'),self)
        self.settings = settings
        
        self.tailrejection = 5
        self.homoKernelX = 147
        self.homoKernelY = 147
        self.calibfile = os.path.join(PATHS["CALIB"],"/default.ini")
        self.camcalib = QtCore.QSettings(self.calibfile, QtCore.QSettings.IniFormat)
        
        self.colorChooser = QtGui.QColorDialog()
        self.maskColbtn = pg.ColorButton()
        
        self.DeadPixelpathBox.setText(self.calibfile)
        
        self.maskColbtn = pg.ColorButton()
        self.maskColVL.addWidget(self.maskColbtn)
        self.setCalib()
        
        self.connections()
        
    def connections(self):
        self.DeadPixelpathButton.clicked.connect(self.onSearch)
        self.tailRejectionSpinBox.valueChanged.connect(self.setTailReject)
        self.homoKernelSizeXspinBox.valueChanged.connect(self.setHomoX)
        self.homoKernelSizeYspinBox.valueChanged.connect(self.setHomoY)
        self.maskColbtn.sigColorChanging.connect(self.setMaskCol)
    
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
        
    def setMaskCol(self,btn):
        self.a = int(btn.color().alpha())
        self.r = int(btn.color().red())
        self.g = int(btn.color().green())
        self.b = int(btn.color().blue())
        print(self.r,self.g,self.b,self.a)
    
    def setTailReject(self,value):  self.tailrejection = value
    def setHomoX(self,value):       self.homoKernelX = value
    def setHomoY(self,value):       self.homoKernelY = value
    
    def setCalib(self):
        camserial = str(self.camcalib.value('GENERAL/camserial'))
        badpxl_v = ast.literal_eval(str(self.camcalib.value('DEAD_PIXEL/bad_pixels_v',"[]")))
        badpxl_h = ast.literal_eval(str(self.camcalib.value('DEAD_PIXEL/bad_pixels_h',"[]")))
        badpxlline_v = ast.literal_eval(str(self.camcalib.value('DEAD_PIXEL/bad_lines_v',"[]")))
        badpxlline_h = ast.literal_eval(str(self.camcalib.value('DEAD_PIXEL/bad_lines_h',"[]")))
        set_mid_value = ast.literal_eval(str(self.camcalib.value('DEAD_PIXEL/set_mid_value',"[]")))
        self.deadpixel={"serial":camserial,"bad_pixels_v":badpxl_v,"bad_pixels_h":badpxl_h,"bad_lines_v":badpxlline_v,"bad_lines_h":badpxlline_h,"set_mid_value":set_mid_value}
            
    def onSearch(self):
        path = QtGui.QFileDialog.getOpenFileName(self, "eine Kamera Kalibrier-Datei waehlen", self.DeadPixelpathBox.text(), "Calibration File (*.ini)")
        if path == "":
            return
        else:
            self.DeadPixelpathBox.setText(path)
            self.calibfile = path    
            self.camcalib = QtCore.QSettings(path, QtCore.QSettings.IniFormat)
            self.setCalib()
    
    def loadSettings(self,s):
        self.settings = s
        
    def writeSettings(self):
        pass
       
        