from __future__ import print_function
from PyQt5 import QtCore,QtGui,uic
import numpy as np
import cv2
import traceback
import utils2
import bisect
import math
import imgproc2
from skimage import io, exposure, img_as_uint, img_as_float
io.use_plugin('freeimage')


class ImageProcessing(QtGui.QWidget):
    
    log = QtCore.pyqtSignal(str)
    nextimg = QtCore.pyqtSignal(int)
    cor_pix_serial = None
    reload = QtCore.pyqtSignal()
    
    def __init__(self,settings):
        QtGui.QWidget.__init__(self)
        self.viewCtrlUI = uic.loadUi('ui/viewcontrol.ui')
        self.detectionUI = uic.loadUi('ui/detection.ui')
        self.ip = imgproc2.ImgProcModel()
        self.settings = settings
        self.connections()
        
    def connections(self):    
        self.viewCtrlUI.CVfliphorCheckBox.stateChanged.connect(self.changed)
        self.viewCtrlUI.CVflipverCheckBox.stateChanged.connect(self.changed)
        self.viewCtrlUI.CVhomogenizeCheckBox.stateChanged.connect(self.changed)
        self.viewCtrlUI.CVwie_analogCheckBox.stateChanged.connect(self.changed)
        
        self.detectionUI.CVdogCheckBox.stateChanged.connect(self.changed)
        self.detectionUI.CVblobsCheckBox.stateChanged.connect(self.changed)
        self.detectionUI.CVonCheckBox.stateChanged.connect(self.changed)
        self.detectionUI.CVautofaktorCheckBox.stateChanged.connect(self.changed)
        self.detectionUI.CVdogLoSpinBox.valueChanged.connect(self.changed)
        self.detectionUI.CVdogUpSpinBox.valueChanged.connect(self.changed)
        self.detectionUI.CVfactorSpinBox.valueChanged.connect(self.changed)
        self.detectionUI.CVautoThresholdCheckBox.stateChanged.connect(self.changed)
        self.detectionUI.CVautodogCheckBox.stateChanged.connect(self.changed)
        
    def flip(self,img):
        self.fliplr = True if self.viewCtrlUI.CVfliphorCheckBox.isChecked() else False
        self.flipud = True if self.viewCtrlUI.CVflipverCheckBox.isChecked() else False
        lrimage = img if not self.fliplr else np.fliplr(img)
        return lrimage.T if not self.flipud else np.flipud(lrimage).T
        
    def setdirlist(self,aralist):
        self.ip.aralist = aralist
    
    def load(self,ara,conf):
        self.ara = ara
        self.ip.load(self.ara)
        self.image = self.ip.image
            
        if self.viewCtrlUI.CVwie_analogCheckBox.isChecked():
            self.image = self.ip.flir_analog(self.ip.rawimage,0.05) #conf.tailrejection = 0.05
            self.viewCtrlUI.CVhomogenizeCheckBox.setEnabled(False)
        else:
            self.viewCtrlUI.CVhomogenizeCheckBox.setEnabled(True)
            if self.viewCtrlUI.CVhomogenizeCheckBox.isChecked():
                self.image = self.ip.homogenize(self.ip.rawimage, 147,147) #conf.homoKernelX,conf.homoKernelY
        shape = self.image.shape
        height = shape[0]
        width = shape[1]
        self.overlay = np.zeros((height,width), np.uint8) 
        
        
        if self.detectionUI.CVonCheckBox.isChecked() or self.detectionUI.CVdogCheckBox.isChecked():
            if self.detectionUI.CVautodogCheckBox.isChecked():
                self.detectionUI.CVdogLoSpinBox.setEnabled(False)
                self.detectionUI.CVdogUpSpinBox.setEnabled(False)
                self.ip.differenceOfGaussians()
                self.detectionUI.CVdogLoSpinBox.setValue(self.ip.dog_lp)
                self.detectionUI.CVdogUpSpinBox.setValue(self.ip.dog_hp)
            else:
                self.detectionUI.CVdogLoSpinBox.setEnabled(True)
                self.detectionUI.CVdogUpSpinBox.setEnabled(True)
                lo = self.detectionUI.CVdogLoSpinBox.value()
                up = self.detectionUI.CVdogUpSpinBox.value()
                self.ip.differenceOfGaussians(lo,up)
            
        if self.detectionUI.CVonCheckBox.isChecked():
            
            if self.detectionUI.CVautoThresholdCheckBox.isChecked():
                self.detectionUI.CVthresholdSpinBox.setEnabled(False)
                self.detectionUI.CVautofaktorCheckBox.setEnabled(True)
                if self.detectionUI.CVautofaktorCheckBox.isChecked():
                    self.detectionUI.CVfactorSpinBox.setEnabled(False)
                    self.ip.extractContours()
                    self.detectionUI.CVfactorSpinBox.setValue(self.ip.fac)
                else:
                    self.detectionUI.CVfactorSpinBox.setEnabled(True)
                    fac = self.detectionUI.CVfactorSpinBox.value()
                    self.ip.extractContours(fac=fac)
                self.detectionUI.CVthresholdSpinBox.setValue(self.ip.thresh)
            else:
                self.detectionUI.CVthresholdSpinBox.setEnabled(True)
                self.detectionUI.CVautofaktorCheckBox.setEnabled(False)
                self.detectionUI.CVfactorSpinBox.setEnabled(False)
                thresh = self.detectionUI.CVthresholdSpinBox.value()
                self.ip.extractContours(thresh=thresh)
            self.detectionUI.CVblobsSpinBox.setValue(len(self.ip.cont))
            
            self.rblobs,areaokblobs = self.ip.feature_extract(self.ip.thresh,40)
            for r in self.rblobs:
                r['image'] = self.ara.filename
                r['height'] = self.ara.header["gps"]["rel_altitude"]
                r["gsd"] = self.ip.gsd
            
            if self.detectionUI.CVblobsCheckBox.isChecked(): 
                cv2.drawContours(self.overlay,self.ip.cont,-1,1,1,1)
                for i in self.rblobs:
                    cv2.putText(self.overlay,str(int(i["col_mean"])), (int(i["x"])+5,int(i["y"])+5), cv2.FONT_HERSHEY_SIMPLEX, .3, 1) 
        
        
    def cutout(self):
        dist = 16
        for i in self.rblobs:
            y,x = int(i["y"]),int(i["x"])
            
            if y-dist > 0 and x-dist>0 and y+dist<512 and x+dist<640:
                im = self.image[y-dist:y+dist,x-dist:x+dist]
                im = exposure.rescale_intensity(im, out_range=(0, 32333))
                im = img_as_uint(im)            
                io.imsave("test/%s_%d_%d.png"%(i["image"][:-4],x,y), im)
        
    def preprocessed(self):
        if self.detectionUI.CVdogCheckBox.isChecked():
            return self.flip(self.ip.dog), self.flip(self.overlay)
        else:
            return self.flip(self.image), self.flip(self.overlay)
    
    def changed(self):
        self.reload.emit()
    

    