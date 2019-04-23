from __future__ import print_function

from PyQt5 import QtCore,QtGui,uic
import numpy as np
import utm
import os
import traceback
from . import utils2
import bisect
import math
import csv
import logging
from . import PATHS

class Temp(QtGui.QWidget):
    
    log = QtCore.pyqtSignal(str)
    #minmax = QtCore.pyqtSignal(float,float)
    
    
    def __init__(self):
        QtGui.QWidget.__init__(self)
        uic.loadUi(os.path.join(PATHS["UI"],'temp.ui'),self)
        #self.setLayout(self.layout)
        self.connections()
        
    def connections(self):
        pass
    
################# Temp-UI
    def tempminmax(self,ara):
        #print("Temp minmax")
        try:
            self.ara = ara
            min = np.min(ara.rawbody)
            max = np.max(ara.rawbody)
            pt_min = self.calc_pixtemp(min)
            pt_max = self.calc_pixtemp(max)
            self.pixtemp_dn_min.setValue(min)
            self.pixtemp_dn_max.setValue(max)
            self.pixtemp_temp_min.setValue(pt_min)
            self.pixtemp_temp_max.setValue(pt_max)
         #   self.minmax.emit(pt_min,pt_max)
         #   print("pt_min",pt_min,pt_max)
            return pt_min,pt_max
        except:
            self.log.emit("temperature extraction failed!")
        return 0,0
        
    def calc_pixtemp(self,dn):
        try:
            fileext = os.path.splitext(self.ara.header["file"].get("name",""))[1].lower()
            if not fileext == ".ara" or fileext==".ara" and self.ara.header["file"]["dlr_protokoll"]["erkennung"]==b"DLR":
                B = self.ara.header["calibration"]["radiometric"].get("B",1)
                R = self.ara.header["calibration"]["radiometric"].get("R",1)
                F = self.ara.header["calibration"]["radiometric"].get("F",1)

            pt = B/math.log(R/dn + F) - 273.0  + self.ara.header["camera"].get("coretemp",0) #- 23.0
            
        except:
            pt = 0
            logging.error("calc_pixtemp didn't work. there might be no calibration data in the image header.",exc_info=True)
        return pt
        
    def fill_pixtemp(self,x,y,dn):
        pt = self.calc_pixtemp(dn)
        self.pixtemp_x.setValue(x)
        self.pixtemp_y.setValue(y)
        self.pixtemp_dn.setValue(dn)
        self.pixtemp_temp.setValue(pt)
        
        
            