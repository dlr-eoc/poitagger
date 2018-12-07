from PyQt5 import QtCore,QtGui,uic
import pyqtgraph as pg

import numpy as np
import utm
import gdal
import os
import cv2
import traceback
import utils2
import bisect
import math
import csv
import asctec


class View(QtGui.QWidget):
    log = QtCore.pyqtSignal(QtCore.QString)
    curimgpath = QtCore.pyqtSignal(QtCore.QString)
    #nextimg = QtCore.pyqtSignal(int)
    #cor_pix_serial = None
    
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.imv = pg.ImageView()
        
        self.connections()
        
    def connections(self):
        pass
    def loadImg(self,curimg):
        print("load image ", self.CV.ara.header.filename)
        
    #    self.rect = QtGui.QGraphicsRectItem(0,0, self.sizew,self.sizeh)
        self.CV.prepare(curimg,self.imgdir)
        self.qim = self.CV.bildverarbeitung() #self.img, self.ara, self.imagefilename, self.imgdir, flip)
        self.imv.setImage(self.CV.ara.rawbody.T)
        
     #   self.imv.view.addItem(self.rect)
        
        self.scene.clear()
        self.image = QtGui.QGraphicsPixmapItem(QtGui.QPixmap.fromImage(utils2.toQImage(self.qim)),None,self.scene)
        
        self.image.mousePressEvent = self.pixelSelect
        
        self.ara = self.CV.ara
        self.fill_values(self.ara)
        
        try:
            if self.ara.header.errflags_allmeta:
                self.imagename.setStyleSheet("QLabel { background-color : #ff0000; }" );
            elif self.ara.header.errflags_pitch or self.ara.header.errflags_roll:
                self.imagename.setStyleSheet("QLabel { background-color : #ffff00; }" );
            else:
                self.imagename.setStyleSheet("" );
        except:
            traceback.print_exc()
            print "loadImg set color ging nicht!"
    
    def paintPois(self,liste): 
        if self.ara.header.errflags_allmeta: return
        for item in self.scene.items():
            if not item == self.image:
                self.scene.removeItem(item)
        for i in liste:
            if i[1]==self.imgname:
                pcol = QtGui.QPen(self.conf.poicolor.color) if i[13] else QtGui.QPen(self.conf.poicolor2.color)
                col =  self.conf.poicolor.color if i[13] else self.conf.poicolor2.color
                self.scene.addEllipse(i[3]-SIZE/2.0,i[4]-SIZE/2.0,SIZE,SIZE,pcol)
                mytext = self.scene.addText(i[2])
                mytext.setPos(i[3]-SIZE/2.0,i[4]-3*SIZE/2.0)
                mytext.setDefaultTextColor(col)
            else:
                pcol = QtGui.QPen(self.conf.poicolor_repro.color) 
                col =  self.conf.poicolor_repro.color 
                self.scene.addEllipse(i[3]-SIZE/2.0,i[4]-SIZE/2.0,SIZE,SIZE,pcol)
                mytext = self.scene.addText(i[2])
                mytext.setPos(i[3]-SIZE/2.0,i[4]-3*SIZE/2.0)
                mytext.setDefaultTextColor(col)
            
                pass
            
        self.scene.update()
    
    def pixelSelect( self, event ):
        x,y = event.pos().x(),event.pos().y()
        #position = QtCore.QPoint( event.pos().x(),  event.pos().y())
        if self.actionTemp_messen.isChecked():
            dn = self.ara.rawbody[y,640 - x]
            pt = self.Temp.calc_pixtemp(dn)
            self.Temp.fill_pixtemp(x,y,dn,pt)
        elif self.actionPoi.isChecked():
            size = SIZE
            self.scene.addEllipse(x-size/2.0,y-size/2.0,size,size,QtGui.QPen(self.conf.poicolor.color))
            self.pois.pos(x,y)
    
    
        
    def save_jpg(self):
        if not self.saveimgdir:
            self.saveimgdir = self.imgdir
        vorschlag = os.path.join(self.saveimgdir,os.path.splitext(self.aralist[0]["filename"])[0]+".jpg")
        filename = QtGui.QFileDialog.getSaveFileName(self,"Save file",vorschlag,"Image (*.jpg)", );
        self.saveimgdir, last = os.path.split(vorschlag)
        cv2.imwrite(str(filename),self.CV.img,[int(cv2.IMWRITE_JPEG_QUALITY), 90])
    def save_png(self):
        if not self.saveimgdir:
            self.saveimgdir = self.imgdir
        vorschlag = os.path.join(self.saveimgdir,os.path.splitext(self.aralist[0]["filename"])[0]+".png")
        filename = QtGui.QFileDialog.getSaveFileName(self,"Save file",vorschlag,"Image (*.png)", );
        self.saveimgdir, last = os.path.split(vorschlag)
        cv2.imwrite(str(filename),self.img)
    
    

      # VIEWBOX
      #  self.sizew +=3
      #  self.sizeh +=3
      #  try:
      #      a = self.imv.view.addedItems[-1]
      #      self.imv.view.removeItem(a)
      #  except:
      #      traceback.print_exc()
      #      print "Kein Item in ViewBox"
          