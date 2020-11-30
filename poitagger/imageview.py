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
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType 

import numpy as np
#import cv2

import os
import traceback
import logging

from . import image 
from . import PATHS
from . import nested
#import asctec
from . import utils2

#widgets
#import imageprocessing2
from . import temp
#SIZE = 30 # This is just the distance for the Labeling of the Pois
try:
    from . import premium
    is_premium = True
except:
    is_premium = False
    pass


logger = logging.getLogger(__name__)
    
class ORIENTATION(object):
    FLIP_LR = 0x01
    FLIP_UP = 0x02
    FLIP_DIAG = 0x04
    
# class Action2ParameterItem(ParameterItem):
    # def __init__(self, param, depth):
        # ParameterItem.__init__(self, param, depth)
        
        
        # self.layoutWidget = QtGui.QWidget()
        # self.layout = QtGui.QHBoxLayout()
        # self.layout.setContentsMargins(0, 0, 0, 0)
        # self.layout.setSpacing(2)
        # self.layoutWidget.setLayout(self.layout)
        # icon  = QtGui.QIcon(os.path.join(PATHS["ICONS"],'maximize-512.png'))
        # self.button = QtGui.QPushButton()
        # self.button.setIcon(icon)
        # self.displayLabel = QtGui.QLabel()
        # self.displayLabel.setText(param.name())
        # self.layout.addWidget(self.displayLabel)
        # self.layout.addSpacing(100)
        # self.layout.addWidget(self.button)
        # self.layout.addStretch()
        # self.button.clicked.connect(self.buttonClicked)
        # param.sigNameChanged.connect(self.paramRenamed)
        # self.setText(0, '')
        
    # def treeWidgetChanged(self):
        # ParameterItem.treeWidgetChanged(self)
        # tree = self.treeWidget()
        # if tree is None:
            # return
        
        # tree.setFirstItemColumnSpanned(self, True)
        # tree.setItemWidget(self, 0, self.layoutWidget)
        
    # def paramRenamed(self, param, name):
        # self.button.setText(name)
        
    # def buttonClicked(self):
        # self.param.activate()
        
# class Action2Parameter(Parameter):
    # """Used for displaying a button within the tree."""
    # itemClass = Action2ParameterItem
    # sigActivated = QtCore.Signal(object)
    
    # def activate(self):
        # self.sigActivated.emit(self)
        # self.emitStateChanged('activated', None)
        
# registerParameterType('action2', Action2Parameter, override=True)

    

class Img(QtGui.QWidget):
    log = QtCore.pyqtSignal(str)
    loaded = QtCore.pyqtSignal(bool)
    highlighting = QtCore.pyqtSignal(str)
    sigMouseMode = QtCore.pyqtSignal(str) #["poi" , "temp"]
    sigPixel = QtCore.pyqtSignal(str,int,int) #x,y,digitalNumber
    sigOrientation = QtCore.pyqtSignal(int)
    saveimgdir = None
    imwidth = 640
    imheight = 512
    
    def __init__(self,conf,startimage,settings):
        QtGui.QWidget.__init__(self)
        self.w = pg.GraphicsLayoutWidget()
        self.settings = settings
        
        self.vbox = self.w.addViewBox(lockAspect=True,enableMenu=False,invertY=True)
        self.vbox.setRange(QtCore.QRect(0,0,self.imwidth,self.imheight))#,padding=0.0
        
        self.wdebug = pg.GraphicsLayoutWidget()
        self.vboxdebug = self.wdebug.addViewBox(lockAspect=True,enableMenu=False,invertY=True)
        self.vboxdebug.setRange(QtCore.QRect(0,0,self.imwidth,self.imheight))#,padding=0.0
        
        
        self.imgUI = uic.loadUi(os.path.join(PATHS["UI"],"image.ui"))
        self.infoUI = uic.loadUi(os.path.join(PATHS["UI"],"imgInfo.ui"))
        self.viewCtrlUI = uic.loadUi(os.path.join(PATHS["UI"],'viewcontrol.ui'))
        self.imgDebugUI = uic.loadUi(os.path.join(PATHS["UI"],"imgDebug.ui"))
        self.normkitzUI = uic.loadUi(os.path.join(PATHS["UI"],"normkitz.ui"))
        
        self.t = ParameterTree(showHeader=False)
        self.imgUI.horizontalLayout.addWidget(self.t)
        
        params = [
            {'name': 'Mouse', 'type': 'group', 'children': [
                {'name': 'x', 'type': 'int', 'value': 0, 'readonly':True},
                {'name': 'y', 'type': 'int', 'value': 0, 'readonly':True},
                {'name': 'Wert (dn)', 'type': 'int', 'value': 0, 'readonly':True},
                {'name': 'Temp', 'type': 'float', 'value': 0 , 'visible':False, 'suffix': '°C', 'readonly':True}]},
            {'name': 'Image', 'type': 'group', 'children': [
                {'name': 'dn min', 'type': 'int', 'value': 0, 'readonly':True},
                {'name': 'dn max', 'type': 'int', 'value': 0, 'readonly':True},
                {'name': 'temp min', 'type': 'float', 'value': 0, 'suffix': '°C', 'readonly':True},
                {'name': 'temp max', 'type': 'float', 'value': 0, 'suffix': '°C', 'readonly':True}
            ]},
            {'name': 'Zoom', 'type': 'int', 'value': 100, 'suffix': '%'},
            {'name': 'fullscreen', 'type': 'action'},
            {'name': 'orientation', 'type': 'group', 'children': [
                {'name': 'flip lr', 'type': 'bool'},
                {'name': 'flip up', 'type': 'bool'},
                {'name': 'flip diag', 'type': 'bool'}
            ]},
            ]
    
            
        if is_premium:
            params.append({'name': 'Premium', 'type': 'group', 'children': [
                {'name': 'homogenize', 'type': 'bool'},
                {'name': 'analog', 'type': 'bool'}]})
            
        self.p = Parameter.create(name='params', type='group',children=params)
        self.t.setParameters(self.p, showTop=False)
        #if is_premium:
           # self.p.child('Premium').child("homogenize").sigActivated.connect(self.set_homogenize)
        
        self.p.child("fullscreen").sigActivated.connect(lambda: self.vbox.setRange(QtCore.QRect(0,0,self.imwidth,self.imheight),padding=0.0))
        self.conf = conf
        #self.settings = settings
        self.histlut = pg.HistogramLUTWidget()
        self.imgUI.horizontalLayout.addWidget(self.histlut)
        
        #self.histlut.setMinimumHeight(95)
        #self.proc = imageprocessing2.ImageProcessing(self.settings)
        self.temp = temp.Temp()
        self.curimg = startimage
        self.connections()
      #  self.proc.reload.emit()
      
   # def set_homogenize(self,check):
    #    self.homo = check
        
    def connections(self):
        self.vbox.sigStateChanged.connect(self.rewriteInfo)
        self.infoUI.pushButton.clicked.connect(lambda: self.vbox.setRange(QtCore.QRect(0,0,self.imwidth,self.imheight),padding=0.0))#vbox.screenGeometry().width(),vbox.screenGeometry().height()
        
        self.infoUI.zoom.editingFinished.connect(lambda: self.setZoom(self.infoUI.zoom.value()))#lambda: self.vbox.setRange(QtCore.QRect(0,0,640,512)
        
        self.p.child('orientation').sigTreeStateChanged.connect(lambda: self.loadImg(self.curimg))
        self.p.child('orientation').sigTreeStateChanged.connect(self.emitOrientation)
        
        self.p.child('orientation').child('flip lr').sigTreeStateChanged.connect(lambda: self.loadImg(self.curimg))
        self.p.child('orientation').child('flip up').sigValueChanged.connect(lambda: self.loadImg(self.curimg))
        self.p.child('orientation').child('flip diag').sigValueChanged.connect(lambda: self.loadImg(self.curimg))
        if is_premium:
            self.p.child('Premium').child('homogenize').sigValueChanged.connect(lambda: self.loadImg(self.curimg))
            self.p.child('Premium').child('analog').sigValueChanged.connect(lambda: self.loadImg(self.curimg))
        
        self.w.scene().sigMouseMoved.connect(self.mouseMoved)
        self.w.scene().sigMouseClicked.connect(self.pixelClicked)
        
      #  self.proc.reload.connect(lambda: self.loadImg(self.curimg))
        
        #self.temp.verticalLayout.addWidget(self.normkitzUI)
     #   self.temp.verticalLayout.addWidget(self.infoUI)
       # self.temp.histVL.addWidget(self.histlut)
      #  self.imgUI.horizontalLayout.addWidget(self.histlut)
        
     #   self.imgDebugUI.pushButton.clicked.connect(self.proc.cutout)
     
    def emitOrientation(self,param):
        a = int(param.child('flip lr').value())*ORIENTATION.FLIP_LR
        b = int(param.child('flip up').value())*ORIENTATION.FLIP_UP
        c = int(param.child('flip diag').value())*ORIENTATION.FLIP_DIAG
        self.sigOrientation.emit(a+b+c)
        
    def setOrientation(self,flightgeneral):
        #orient = flightgeneral.child("orientation")
        #print ("ORIENTATION",orient)
        try:
            imgor = flightgeneral.child("images").child("orientation").value()
            imgorparam = self.p.child('orientation')    
            with imgorparam.treeChangeBlocker():
                imgorparam.child('flip lr').setValue(imgor & ORIENTATION.FLIP_LR)
                imgorparam.child('flip up').setValue(imgor & ORIENTATION.FLIP_UP)
                imgorparam.child('flip diag').setValue(imgor & ORIENTATION.FLIP_DIAG)
        except:
            pass
            
        
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
        self.p.child('Zoom').setValue(zoom)
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
            x,y = int(pt.x()),int(pt.y())
            self.p.child('Mouse').child('x').setValue(x)
            self.p.child('Mouse').child('y').setValue(y)
            if not  0 <= x < self.imwidth: 
                self.p.child('Mouse').child('Wert (dn)').setValue(0)
                return
            if not  0 <= y < self.imheight: 
                self.p.child('Mouse').child('Wert (dn)').setValue(0)
                return
            dn = self.ara.rawbody[y, x]
            self.p.child('Mouse').child('Wert (dn)').setValue(dn)
            
            #self.infoUI.x_mouse.setValue(pt.x())
            #self.infoUI.y_mouse.setValue(pt.y())
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
            logger.error("imageview calc_kitzsize load image header failed", exc_info=True)
            return 1
            
    def flip(self,img):
        self.fliplr = True if self.p.child('orientation').child('flip lr').value() else False
        self.flipud = True if self.p.child('orientation').child('flip up').value() else False
        self.flipdiag = True if self.p.child('orientation').child('flip diag').value() else False
        lrimage = img if not self.fliplr else np.fliplr(img)
        out = lrimage if not self.flipud else np.flipud(lrimage)
        if self.flipdiag:
            return out
        else:
            if len(out.shape)==3: #rgb color image
                return out.transpose([1,0,2])
            else:
                return out.T
            
    def loadImg(self,curimg):
        #print("Load img")
        self.curimg = curimg
        self.imgdir, self.imgname = os.path.split(str(curimg))
        self.imgbasename, ext = os.path.splitext(self.imgname)
        if not os.path.isfile(curimg): return
        
        self.ara = image.Image.factory(curimg)
        #self.log.emit(str(self.ara.exif))
        if hasattr(self.ara, 'rawbody'):
            img = self.ara.rawbody 
        else:
            img = self.ara.image 
        
        try:
            self.imheight,self.imwidth = img.shape[0],img.shape[1]
        except:
            print("ERROR!, shape:", img.shape)
        
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
        #print("IMAGESHAPE:",preprocessed.shape,img.shape)
        if is_premium and self.p.child('Premium').child('analog').value() :
            preprocessed = (premium.analog(preprocessed))
        elif is_premium and self.p.child('Premium').child('homogenize').value() :
            preprocessed = (premium.homogenize(preprocessed))
        
        self.image = pg.ImageItem(preprocessed)
        
        min = np.min(img)
        max = np.max(img)
        self.p.child('Image').child("dn min").setValue(min)
        self.p.child('Image').child("dn max").setValue(max)
        
        pt_min,pt_max = self.temp.tempminmax(self.ara)
        self.p.child('Image').child("temp min").setValue(pt_min)
        self.p.child('Image').child("temp max").setValue(pt_max)
        
        self.histlut.setImageItem(self.image)
        self.vbox.clear()
        self.vbox.addItem(self.image)
        
        
        try:
            if self.ara.header["calibration"].get("error_flags",0) & image.ERRORFLAGS.ALL_META:
                hlstr = "QLabel { background-color : #ff0000; }"  #self.imagename.setStyleSheet();
            elif self.ara.header["calibration"].get("error_flags",0) & image.ERRORFLAGS.FAST_PITCH or self.ara.header["calibration"].get("error_flags",0) & image.ERRORFLAGS.FAST_ROLL:
                hlstr = "QLabel { background-color : #ffff00; }" 
            else:
                hlstr = ""
            self.highlighting.emit(hlstr)
        except:
            logger.error("loadImg set color did not work",exc_info=True)
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
        self.size = int(self.settings.value("POIS/size"))
        if self.ara.header["calibration"].get("error_flags",0) & image.ERRORFLAGS.ALL_META: return
        for item in self.vbox.addedItems[:]:# nur die Overlays loeschen #self.scene.items():
            if type(item) in [QtGui.QGraphicsTextItem, QtGui.QGraphicsEllipseItem,]: # pg.graphicsItems.ImageItem.ImageItem: 
                self.vbox.removeItem(item)
        for i in liste:
            x,y = float(i["x"]),float(i["y"])
            #print (type(x),type(y))
            y2 = y+self.size/2.0 #if not self.proc.flipud else self.imheight - i[4]+self.size/2.0 -1
            eli = QtGui.QGraphicsEllipseItem(x-self.size/2.0,y-self.size/2.0,self.size,self.size)
            mytext = QtGui.QGraphicsTextItem(str(i["name"])) 
            mytext.setPos(x-self.size/2.0,y2)
            if str(self.settings.value("POIS/visible")).lower() != "true": return
            if i["filename"]==self.imgname:
                pcol = QtGui.QPen(QtGui.QColor(self.conf.pois.poicolor.color))#"#ff0000"
                col =  QtGui.QColor(self.conf.pois.poicolor.color) #"#ff0000"
                eli.setPen(pcol)
                mytext.setDefaultTextColor(col)
            else:
                pcol = QtGui.QPen(QtGui.QColor(self.conf.pois.poicolor_repro.color))#"#0000ff") 
                col =  QtGui.QColor(self.conf.pois.poicolor_repro.color)# "#0000ff"
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
            try:
                dn = self.ara.rawbody[y, x]
            except:
                dn = self.ara.image[y, x]
                logger.warning("no rawdata!")
            if self.poiAction.isChecked():
    #            eli = QtGui.QGraphicsEllipseItem(int(pt.x())-self.size/2.0,int(pt.y())-self.size/2.0,self.size,self.size)
    #            eli.setPen(QtGui.QPen(QtGui.QColor("#ff0000")))
    #            self.vbox.addItem(eli)
                self.sigPixel.emit(self.imgname,x,y)
            elif self.tempAction.isChecked():
                print(self.temp.calc_pixtemp(dn))
                #self.temp.fill_pixtemp(x,y,dn)
        except:
            logger.error("imageview pixelClicked failed", exc_info=True)
            
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
       
          