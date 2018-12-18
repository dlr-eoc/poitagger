"""
###############  TODO: ###############

Zum settings: Momentan sind die Einstellungen teilweise ueber die Properties-Klasse implementiert worden.
Das ist unguenstig, weil die Einstellungen nur in einem Widget Umfeld verwendet werden koennen. 
Es gibt aber Einstellungen, die zentral von Komponenten der Software benoetigt werden, die nicht an das Properties Widget direkt herankommen.
Ausserdem wird es sehr unuebersichtlich mit der Zeit.

Es gibt ja ein zentrales Settings-Objekt, das beim schließen des Programms die Eintraege in die Datei conf.ini schreibt.
Fuer alle Settings koennte man dieses Zentrale Objekt einbinden, und jegliche Einstellung von jedem Button einfach da reinschreiben. 
Dann kann auch immer jeder abfragen, welche Einstellung gerade eingestellt ist.
Damit nicht so viel Schreibarbeit entsteht, weil bei jedem Button druecken, muss auch noch die Settings geschrieben werden, 
koennte man vielleicht per Observer, oder Decorator-Pattern das Fuellen und abrufen der Werte vereinfachen.

Oder StateMachine??? QStatemachine



Es muesste die Liste der Pois und anderer Objekte in folgendem Format geschickt werden:
[{painttype:"namedPoiCircle",pos:(631,511),text:"Kiebitz1",from:"Pois"},
{painttype:"blobText",pos:(631,511),text:"6434",from:"ImgProcModel"},
]

und dann muesste es eine empfaenger-Methode geben, die diese Listen annimmt, 
die alten mit dem schluesselwort des selben senders rauswirft und durch die neuen ersetzt.
danach ein clear addedItems und die liste wieder neu zeichnen. Je nach Painttyp, 
gibt es eine eigene Methode, die dann die Dinge entsprechend Zeichnet.
"""

from __future__ import print_function

from PyQt5 import QtCore,QtGui,uic
import pyqtgraph as pg
import pyqtgraph.exporters
import numpy as np
#import cv2

import os
import traceback
import logging

from . import image 
from . import PATHS
#import asctec
from . import utils2

#widgets
#import imageprocessing2
from . import temp
from . import PATHS   
SIZE = 30 # This is just the distance for the Labeling of the Pois

class Img(QtGui.QWidget):
    log = QtCore.pyqtSignal(str)
    loaded = QtCore.pyqtSignal(bool)
    highlighting = QtCore.pyqtSignal(str)
    sigMouseMode = QtCore.pyqtSignal(str) #["poi" , "temp"]
    sigPixel = QtCore.pyqtSignal(int,int) #x,y,digitalNumber
    saveimgdir = None
    imwidth = 640
    imheight = 512
    
    def __init__(self,conf,startimage):
        QtGui.QWidget.__init__(self)
        self.w = pg.GraphicsLayoutWidget()
        
        self.settings = QtCore.QSettings("conf.ini", QtCore.QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False) 
        
        self.vbox = self.w.addViewBox(lockAspect=True,enableMenu=False,invertY=True)
        self.vbox.setRange(QtCore.QRect(0,0,self.imwidth,self.imheight))#,padding=0.0
        
        self.wdebug = pg.GraphicsLayoutWidget()
        self.vboxdebug = self.wdebug.addViewBox(lockAspect=True,enableMenu=False,invertY=True)
        self.vboxdebug.setRange(QtCore.QRect(0,0,self.imwidth,self.imheight))#,padding=0.0
        
        
        self.infoUI = uic.loadUi(os.path.join(PATHS["UI"],"imgInfo.ui"))
        self.viewCtrlUI = uic.loadUi(os.path.join(PATHS["UI"],'viewcontrol.ui'))
        self.imgDebugUI = uic.loadUi(os.path.join(PATHS["UI"],"imgDebug.ui"))
        self.normkitzUI = uic.loadUi(os.path.join(PATHS["UI"],"normkitz.ui"))
        
        self.conf = conf
        #self.settings = settings
        self.histlut = pg.HistogramLUTWidget()
        #self.proc = imageprocessing2.ImageProcessing(self.settings)
        self.temp = temp.Temp()
        self.curimg = startimage
        self.connections()
      #  self.proc.reload.emit()
        
    def connections(self):
        self.vbox.sigStateChanged.connect(self.rewriteInfo)
        self.infoUI.pushButton.clicked.connect(lambda: self.vbox.setRange(QtCore.QRect(0,0,self.imwidth,self.imheight),padding=0.0))#vbox.screenGeometry().width(),vbox.screenGeometry().height()
        
        self.infoUI.zoom.editingFinished.connect(lambda: self.setZoom(self.infoUI.zoom.value()))#lambda: self.vbox.setRange(QtCore.QRect(0,0,640,512)
        
        
        self.w.scene().sigMouseMoved.connect(self.mouseMoved)
        self.w.scene().sigMouseClicked.connect(self.pixelClicked)
      #  self.proc.reload.connect(lambda: self.loadImg(self.curimg))
        
        self.temp.verticalLayout.addWidget(self.normkitzUI)
        self.temp.verticalLayout.addWidget(self.infoUI)
        self.temp.histVL.addWidget(self.histlut)
        self.temp.histVL.addWidget(self.histlut)
        
     #   self.imgDebugUI.pushButton.clicked.connect(self.proc.cutout)
            
    def appendButtonsToToolBar(self,toolBar):
        self.toolBar = toolBar
        
        tempIcon = QtGui.QIcon(QtGui.QPixmap(os.path.join(PATHS["ICONS"],"temp.png")))
        self.tempAction = QtGui.QAction(tempIcon,"temp", self)
        self.tempAction.setToolTip("Measure Temperature")
        self.tempAction.setCheckable(True)
        self.toolBar.addAction(self.tempAction)
        
        poiIcon = QtGui.QIcon(QtGui.QPixmap(os.path.join(PATHS["ICONS"],"poi2.png")))
        self.poiAction = QtGui.QAction(poiIcon,"poi", self)
        self.poiAction.setToolTip("Point of Interest")
        self.poiAction.setCheckable(True)
        self.poiAction.setChecked(True)
        self.toolBar.addAction(self.poiAction)
        
        self.actionGroupTools = QtGui.QActionGroup(self)
        self.actionGroupTools.addAction(self.tempAction)
        self.actionGroupTools.addAction(self.poiAction)
        self.actionGroupTools.triggered.connect(self.changeMouseMode)
    
    def changeMouseMode(self):
        if self.poiAction.isChecked():
            self.sigMouseMode.emit("poi") 
        else:
            self.sigMouseMode.emit("temp")
            
    
        
    def rewriteInfo(self):
        [[x1,x2],[y1,y2]] = self.vbox.viewRange()
        swidth = self.vbox.screenGeometry().width()
        width = x2-x1
        zoom = swidth / width *100
        self.infoUI.zoom.setValue(zoom)
        self.infoUI.x_view.setValue(x1)
        self.infoUI.y_view.setValue(y1)
        self.infoUI.x_range.setValue(width)
        self.infoUI.y_range.setValue(y2-y1)
    
    def setZoom(self,zoom):
        pass
        
    def mouseMoved(self,pos):
        try:
            pt = self.image.mapFromScene(pos)
            self.infoUI.x_mouse.setValue(pt.x())
            self.infoUI.y_mouse.setValue(pt.y())
        except:
            pass
        
    def calc_kitzsize(self):####TODO: Pixelseitenlaenge und Brennweite aus Datei holen!
        r_kitz = 0.2
        #gsd = self.ara.header.baro*17e-6/19e-3 if self.ara.header.baro > 0 else 0.01
        try:
            gsd = self.ara.header["gps"].get("rel_altitude",0)*17e-6/19e-3 if self.ara.header["gps"].get("rel_altitude",0) > 0 else 0.01
            r_pix = int(r_kitz/gsd)
            #print "baro",self.ara.header.baro,gsd,r_pix
            zoom = self.infoUI.zoom.value()/100.0
            
            return r_pix * zoom
        except:
            logging.error("imageview calc_kitzsize load image header failed", exc_info=True)
            return 1
            
    def flip(self,img):
        self.fliplr = True if self.infoUI.CVfliphorCheckBox.isChecked() else False
        self.flipud = True if self.infoUI.CVflipverCheckBox.isChecked() else False
        lrimage = img if not self.fliplr else np.fliplr(img)
        return lrimage.T if not self.flipud else np.flipud(lrimage).T
        
    def loadImg(self,curimg):
        self.curimg = curimg
        self.imgdir, self.imgname = os.path.split(str(curimg))
        self.imgbasename, ext = os.path.splitext(self.imgname)
        if not os.path.isfile(curimg): return
        
        self.ara = image.Image.factory(curimg)
        
        if hasattr(self.ara, 'rawbody'):
            img = self.ara.rawbody 
        else:
            img = self.ara.image 
        
        # try:
            # if str(curimg).lower().endswith((".tiff",".tif")):
                # self.ara = utils2.LoadTiff(curimg)
            # elif str(curimg).lower().endswith((".tiff",".tif")):
                # self.ara = utils2.LoadJpg(curimg)
            # else:
                #pass
                
        # except:
            # print("no image loaded!")
            # return 
        try:
            self.imheight,self.imwidth = img.shape[0],img.shape[1]
        except:
            print("ERROR!, shape:", img.shape)
  #      self.proc.load(self.ara,self.conf)
        
        pixmap = QtGui.QPixmap(100, 100)
        pixmap.fill(QtCore.Qt.white)
  
        painter = QtGui.QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(179,119,0)), 1))
        painter.setBrush(QtGui.QColor(179,119,0));
        r = self.calc_kitzsize()
        
        painter.drawEllipse(50-r,50-r,2*r,2*r)
        
        painter.end()
        preprocessed = self.flip(img)
        #preprocessed = self.flip(self.ara.image.astype(int))
#        self.proc.viewCtrlUI.normkitz.setPixmap(pixmap)
        
  #      preprocessed, overlay = self.proc.preprocessed()
        #self.overlay = np.zeros_like(self.image, np.uint8) 
        
        #self.flip(self.image), self.flip(self.overlay)
        #if self.imgDebugUI.checkBox.isChecked():
        #    preprocessed = np.array(preprocessed * 2 * self.mask, dtype=np.uint16)
        #print ("####################")
        #print("imgshape",preprocessed.shape)
        if len(preprocessed.shape)<3:
            self.image = pg.ImageItem(preprocessed)
            self.temp.tempminmax(self.ara)
            self.histlut.setImageItem(self.image)
            self.vbox.clear()
            self.vbox.addItem(self.image)
        else:
            print ("No Colorimages supported yet")
            #self.vbox.setImage(self.ara.image)
        #self.image = pg.ImageItem(self.ara.image)
        #self.image = pg.image(self.ara.image)
        
        
        
      #  if self.proc.detectionUI.CVonCheckBox.isChecked():

       #     overlay2 = cv2.merge((overlay.T*self.conf.r,overlay.T*self.conf.g,overlay.T*self.conf.b,overlay.T*self.conf.a))
       #     overlay3 = QtGui.QPixmap.fromImage(utils2.toQImage(overlay2))
       #     self.overlay = QtGui.QGraphicsPixmapItem(overlay3)
       #     self.vbox.addItem(self.overlay)
        #print(self.ara["header"])    
        try:
            if self.ara.header["calibration"].get("error_flags",0) & image.ERRORFLAGS.ALL_META:
                hlstr = "QLabel { background-color : #ff0000; }"  #self.imagename.setStyleSheet();
            elif self.ara.header["calibration"].get("error_flags",0) & image.ERRORFLAGS.FAST_PITCH or self.ara.header["calibration"].get("error_flags",0) & image.ERRORFLAGS.FAST_ROLL:
                hlstr = "QLabel { background-color : #ffff00; }" 
            else:
                hlstr = ""
            self.highlighting.emit(hlstr)
        except:
            logging.error("loadImg set color did not work",exc_info=True)
        self.loaded.emit(True)
    
    def onSetMask(self):
    #    self.mask  = self.proc.mat 
        self.vboxdebug.clear()
        self.vboxdebug.addItem(pg.ImageItem(self.mask))
    
    def flippedPoint(self,x_mouse,y_mouse):
#        x = x_mouse if not self.proc.fliplr else self.imwidth - x_mouse -1
#        y = y_mouse if not self.proc.flipud else self.imheight - y_mouse -1
        return x,y
        
    def paintPois(self,liste): 
        if self.ara.header["calibration"].get("error_flags",0) & image.ERRORFLAGS.ALL_META: return
        for item in self.vbox.addedItems[:]:# nur die Overlays loeschen #self.scene.items():
            if type(item) in [QtGui.QGraphicsTextItem, QtGui.QGraphicsEllipseItem,]: # pg.graphicsItems.ImageItem.ImageItem: 
                self.vbox.removeItem(item)
        for i in liste:
            x,y = i[3],i[4]
            y2 = i[4]+SIZE/2.0 #if not self.proc.flipud else self.imheight - i[4]+SIZE/2.0 -1
            eli = QtGui.QGraphicsEllipseItem(x-SIZE/2.0,y-SIZE/2.0,SIZE,SIZE)
            mytext = QtGui.QGraphicsTextItem(str(i[2])) 
            mytext.setPos(x-SIZE/2.0,y2)
            if i[1]==self.imgname:
                pcol = QtGui.QPen(QtGui.QColor("#ff0000")) if i[13] else QtGui.QPen(QtGui.QColor("#55ff00"))
                col =  QtGui.QColor("#ff0000") if i[13] else QtGui.QColor("#55ff00") #self.conf.poicolor.color if i[13] else self.conf.poicolor2.color
                eli.setPen(pcol)
                mytext.setDefaultTextColor(col)
            else:
                pcol = QtGui.QPen(QtGui.QColor("#0000ff"))#self.conf.poicolor_repro.color) 
                col =  QtGui.QColor("#0000ff")#self.conf.poicolor_repro.color 
                eli.setPen(pcol)
                mytext.setDefaultTextColor(col)
            self.vbox.addItem(eli)
            self.vbox.addItem(mytext)
    
    
        
    def pixelClicked( self, event ):
        try:
            pt = self.image.mapFromScene(event.scenePos())
            x,y = int(pt.x()),int(pt.y())
            if not  0 <= x < self.imwidth: return 
            if not  0 <= y < self.imheight: return 
            dn = self.ara.rawbody[y, x]
            if self.poiAction.isChecked():
                eli = QtGui.QGraphicsEllipseItem(int(pt.x())-SIZE/2.0,int(pt.y())-SIZE/2.0,SIZE,SIZE)
                eli.setPen(QtGui.QPen(QtGui.QColor("#ff0000")))
                self.vbox.addItem(eli)
                self.sigPixel.emit(x,y)
            elif self.tempAction.isChecked():
                self.temp.fill_pixtemp(x,y,dn)
        except:
            logging.error("imageview pixelClicked failed", exc_info=True)
            
    def save_jpg(self):
        if not self.saveimgdir:
            self.saveimgdir = self.imgdir
        vorschlag = os.path.join(self.saveimgdir,self.imgbasename+".jpg")
        filename = QtGui.QFileDialog.getSaveFileName(self,"Save file",vorschlag,"Image (*.jpg)", );
        self.saveimgdir, last = os.path.split(str(filename[0]))
        self.exporter = pg.exporters.ImageExporter(self.image)
        self.exporter.params.param('width').setValue(int(self.imwidth), blockSignal=self.exporter.widthChanged)
        self.exporter.params.param('height').setValue(int(self.imheight), blockSignal=self.exporter.heightChanged)      
        #self.exporter.parameters()["width"]= int(self.imwidth)
        myQImage = self.exporter.export(toBytes=True)
        myQImage.save(filename[0], "JPG",90)
 
    def save_png(self):
        if not self.saveimgdir:
            self.saveimgdir = self.imgdir
        vorschlag = os.path.join(self.saveimgdir,self.imgbasename+".png")
        filename = QtGui.QFileDialog.getSaveFileName(self,"Save file",vorschlag,"Image (*.png)", );
        self.saveimgdir, last = os.path.split(str(filename[0]))
        
        self.exporter = pg.exporters.ImageExporter(self.image)
        self.exporter.params.param('width').setValue(int(self.imwidth), blockSignal=self.exporter.widthChanged)
        self.exporter.params.param('height').setValue(int(self.imheight), blockSignal=self.exporter.heightChanged)      
        self.exporter.export(str(filename[0])) 
       
          