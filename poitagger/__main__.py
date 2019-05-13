""" poi_tagger2 can read ARA-files and makes the georeference for points of interest

Usage:
    poitagger.py [<infolder>] [-r <rootdir>] [-w] [--remote-debugging-port=<port_number>]
    poitagger.py -h | --help
    poitagger.py --version

Arguments:
    <infolder>                              this is the folder for all in and output files 
Options:
    -r <rootdir>                            rootdirectory for the foldertree [default: None]
    -w                                      set windowposition to (x,y)=(0,0)
    --remote-debugging-port=<port_number>   set the Chromium Debugging Port for the QtWebEngine 
"""

from docopt import docopt
import warnings
warnings.filterwarnings("ignore", category=FutureWarning) # PyQtGraph has a FutureWarning: h5py: Conversion from float to np.floating is deprecated

from PyQt5 import QtCore,QtGui,uic, QtWidgets
from PyQt5.QtWidgets import QApplication,QWidget,QMainWindow,QMessageBox,QTextEdit

import numpy as np

import sys
import os
import shutil
import platform

from . import nested
from . import gpx
from . import poimodel2
from . import utils2
from . import flightjson
from . import PATHS
from . import __version__
# Widgets
from . import importer
from . import workflow
from . import poiview
from . import info
from . import calib
from . import geoview
from . import properties
from . import imageview
from . import treeview
from . import gpxexport

#from . import dem

paramreduce = nested.Nested(callback=nested.paramtodict,callback_pre=nested.pre_paramtodict,tupletype=list)
     
class Main(QMainWindow):
    curimgpath = QtCore.pyqtSignal(str)
    log = QtCore.pyqtSignal(str)
    saveimgdir = None
    dockwidgets = []
    
    def __init__(self, imgdir = None, rootdir = None,resetwindow = None):
        QMainWindow.__init__(self)
        self.useflight = True
        self.resetwindow = resetwindow
        self.msg = QMessageBox()
        self.settings = QtCore.QSettings(PATHS["CONF"], QtCore.QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False) 
        rd = rootdir if rootdir is not None else str(self.settings.value('PATHS/rootdir'))
        id = imgdir if imgdir is not None else str(self.settings.value('PATHS/last'))
        self.imgdiff = 1 if imgdir is not None else int(self.settings.value('PATHS/lastimgid',0))
        startfilename = str(self.settings.value('PATHS/lastimgname'))
        
        self.saveDialog = importer.SaveAsDialog(self)
        
        self.conf = properties.PropertyDialog("Einstellungen",self.settings)
        
        
        self.img = imageview.Img(self.conf,os.path.join(id,startfilename),self.settings)
        if self.useflight:
            self.flight = flightjson.Flight(".poitagger.json")
        self.info = info.Info()
       # self.calib = calib.Calib()
       # self.dem = dem.Dem()
        #self.wf = workflow.Araloader()
        
        #self.poiview = pois.Pois(self.conf)
        self.poidata = poimodel2.PoiModel()
        self.poiview = poiview.PoiView(self.poidata)
        self.gpxview = gpxexport.GpxView(self.settings,self.poidata)
        
            
        if self.useflight:
            self.poiview.setMeta(self.flight.p) 
        
        self.geomain = geoview.GeoWidget(self.settings)
        
        self.treemain = treeview.TreeWidget(self)
        self.treemain.setRoot(rd)
        self.treeview = self.treemain.view
        self.treemodel = self.treeview.model
        self.treemodel.metafilename = ".poitagger.json"
        
        self.loadUI()
        self.shortcuts()
        self.connections()
        
        self.treemain.view.setFocus()
        
        self.log.emit("SETTINGS-FILE: "+PATHS["CONF"] + " , cwd: "+os.getcwd() +" , file: "+os.path.realpath(__file__) )
        
    def loadUI(self):
        uic.loadUi(os.path.join(PATHS["UI"],'poitagger.ui'),self)
        self.setCentralWidget(self.img.w)
        
        self.img.appendButtonsToToolBar(self.toolBar)
        
        self.flightmain = flightjson.FlightWidget(self)
        if self.useflight:
            self.flightmain.setMeta(self.flight)
        
        self.Console = QTextEdit(self.ConsoleDockWidget)
        
     #   self.setDockWidget(self.CalibDockWidget,        'GUI/CalibDock',        self.calib)
        #self.setDockWidget(self.DEMDockWidget,          'GUI/DEMDock',          self.dem)
        self.setDockWidget(self.ConsoleDockWidget,      'GUI/ConsoleDock',      self.Console)
        self.setDockWidget(self.PoisDockWidget,         'GUI/PoisDock',         self.poiview)
        self.setDockWidget(self.GeoViewDockWidget,      'GUI/GeoViewDock',      self.geomain)
        self.setDockWidget(self.PixeltempDockWidget,    'GUI/PixeltempDock',    self.img.imgUI)
        self.setDockWidget(self.InfoDockWidget,         'GUI/InfoDock',         self.info.t)
        self.setDockWidget(self.FMInfoDockWidget,       'GUI/FMInfoDock',       self.flightmain) #fminfo
        self.setDockWidget(self.VerzeichnisDockWidget,  'GUI/VerzeichnisDock',  self.treemain)#.tree
        self.setDockWidget(self.GpxDockWidget, 'GUI/GpxDock',self.gpxview)
        
        upperwidgets = [self.GeoViewDockWidget]#,self.CalibDockWidget]#, self.ViewControlDockWidget, self.DEMDockWidget]
        lowerwidgets = [self.ConsoleDockWidget, self.PoisDockWidget, self.GpxDockWidget,self.FMInfoDockWidget]# self.DebugDockWidget,
        self.Console.hide()
        [self.tabifyDockWidget( self.PixeltempDockWidget, w) for w in upperwidgets]
        [self.tabifyDockWidget( self.InfoDockWidget,w) for w in lowerwidgets]
        
        self.loadSettings(self.settings)
        
        self.show()
  
    def setDockWidget(self,dockwidget,settingsprefix,widget=None):
        if not widget == None:
            dockwidget.setWidget(widget) 
                
        self.menuAnsicht.addAction(dockwidget.toggleViewAction())
        self.dockwidgets.append((dockwidget,settingsprefix))
        
    def connections(self):
        self.actionconnects()
        self.logconnects()
        self.info.position.connect(self.geomain.view.moveUav)
        #self.wf.progress.connect(self.AraLoaderProgressBar.setValue)
        self.escAction.triggered.connect(self.close)
        
        self.poiview.sigJumpTo.connect(self.treemain.view.setCurrent)
        self.poidata.sigPois.connect(self.img.paintPois)
       # self.poidata.sig_reprojected.connect(self.img.paintPois)
      #  self.poidata.sigPois.connect(self.treemodel.pois)
        
        self.treemain.view.imgPathChanged.connect(self.onImagePathChanged)
        self.treemain.view.imgDirChanged.connect(self.onDirChanged)
        self.img.loaded.connect(lambda: self.onImageChanged(self.img.ara))
        self.treemain.view.rootDirChanged.connect(lambda rootdir: self.settings.setValue('PATHS/rootdir', rootdir))
        
        if self.useflight:
            self.geomain.actionFitMap.triggered.connect(lambda: self.geomain.view.fitBounds(paramreduce.load(self.flight.p.child("general").child("bounding").getValues())))
            self.flight.uavpath.connect(self.geomain.view.setUavPath)
            self.flight.general.connect(self.img.setOrientation)
            self.flight.loadfinished.connect(lambda: self.poidata.loadMeta(self.flight.p))
            self.flight.poisChanged.connect(lambda: self.poidata.loadMeta(self.flight.p))
            self.img.sigOrientation.connect(self.flight.setOrientation)
            self.flight.pois.connect(self.treemain.reloadPoiFiles)
            self.flight.sigEmpty.connect(self.geomain.view.clear)
            
            self.flight.pois.connect(self.geomain.view.loadpois)
        
        self.img.highlighting.connect(self.treemain.vb.imagename.setStyleSheet)
        self.img.sigPixel.connect(self.poiview.addView)
        self.img.sigMouseMode.connect(self.focusDockWidget)
    
    def actionconnects(self):
        self.actionSD_Karte_einlesen.triggered.connect(self.saveDialog.open) #lambda: self.wf.readSDCard(self.saveDialog,self.settings))
        self.actionJpg_export.triggered.connect(self.img.save_jpg)
        self.actionPng_export.triggered.connect(self.img.save_png)
        #self.actionConvert_folder_to_jpg.triggered.connect(lambda: self.wf.convertFolderJpg(self.treemain.view.current_path()))
        #self.actionCreate_subimages.triggered.connect(lambda: self.wf.createSubimages(self.treemain.view.current_path()))
        self.actionGpx_to_gps.triggered.connect(self.gpx_to_gps)
        self.actionEinstellungen.triggered.connect(self.conf.openPropDialog)
    
    def logconnects(self):
        self.log.connect(self.Console.append)
        #self.wf.log.connect(self.Console.append)
        self.treemain.view.log.connect(self.Console.append)
        self.img.log.connect(self.Console.append)
        self.info.log.connect(self.Console.append)
        self.img.temp.log.connect(self.Console.append)
        
    def onDirChanged(self,path):
        if self.useflight:
            self.flight.load(path)
        self.geomain.setCurrentDir(path)
        
    def onImagePathChanged(self,path):
        self.img.loadImg(path)
        self.setWindowTitle("Poitagger " + str(__version__) + " " + path)
        
    def onImageChanged(self,ara):
        self.info.load_data(ara.header)
        self.poidata.setPose(ara.header)
        self.poidata.getPois(ara.filename)
        self.geomain.setCurrentImg(ara.header)
      
    def gpx_to_gps(self):
        pois = self.poiview.getPoisAsGpx()
        if self.useflight:
            self.flight.save()
        
        poisfilename = "pois.gpx" #os.path.join(self.dir.imgdir,"pois.gpx")
        if os.path.exists(PATHS["POIS"]):
            os.remove(PATHS["POIS"])
        self.gpxgen = gpx.GpxGenerator(PATHS["POIS"])
        try:
            for i in pois:
                self.gpxgen.add_wpt(str(i["lat"]),str(i["lon"]),str(i["ele"]),i["found_time"],str(i["name"]),"poi")
            self.gpxgen.save(PATHS["POIS"],False)
        except:
            logging.error("GPS_TO_GPS save failed",exc_info=True)
            
        self.exportgpx(PATHS["POIS"])#,self.conf)
        
    
    def exportgpx(self,gpxfile):#, conf):
        #self.gpxdialog.show()
        if str(self.settings.value('GPS-DEVICE/exportType')) == "serial":# conf.garminserial_rB.isChecked():
            cmd = 'gpsbabel -w -r -t -i gpx,suppresswhite=0,logpoint=0,humminbirdextensions=0,garminextensions=0 -f "' + gpxfile + '" -o garmin,snwhite=0,get_posn=0,power_off=0,erase_t=0,resettime=0 -F usb:'
            print(cmd)
            ret = os.system(cmd)
            if ret == 0: 
                QtGui.QMessageBox.information(self, "Gps-Datenuebertragung ","Die GPS-Datenuebertragung war erfolgreich! Die Wegpunkte wurden ueber das Garmin-Serial/USB-Protokoll uebertragen"); 
            else:
                QtGui.QMessageBox.critical(self, "Gps-Datenuebertragung fehlgeschlagen!","ein altes Garmin Geraet wurde nicht gefunden (bei einem neueren GPS-Geraet muss unter Einstellungen/allgemein/GPS-Device MassStorage Device anstatt Garmin Serial/USB ausgewaehlt werden)!"); 
                
        elif  str(self.settings.value('GPS-DEVICE/exportType')) == "massStorage":# conf.massStorage_rB.isChecked():
            if str(self.settings.value('GPS-DEVICE/detectMode')) == "name": #conf.detectName_rB.isChecked():
               # drive = utils2.getSDCardPath(str(self.settings.value('GPS-DEVICE/harddrive'))) #str(conf.name_LE.text()))
                drive = None
                if drive==False:
                    QtGui.QMessageBox.critical(self, "Gps-Datenuebertragung fehlgeschlagen!","GPS-Geraet nicht gefunden (Ein Geraet mit dem Namen  %s existiert nicht)!"%str(conf.name_LE.text())); 
                    
                    
            elif str(self.settings.value('GPS-DEVICE/detectMode'))== "fixedfolder": #conf.fixedFolder_rB.isChecked():
                drive = str(self.settings.value('GPS-DEVICE/harddrive')) #str(conf.harddrive_LE.text())
            else:
                QtGui.QMessageBox.critical(self, "Info0","kein Detektionsmodus gewaehlt! (unter Einstellungen/GPS-Device)"); 
            
            if not drive==False and not drive==None:
                print(drive,str(self.settings.value('GPS-DEVICE/gpxfolder')))
                outdir = os.path.join(drive,str(self.settings.value('GPS-DEVICE/gpxfolder')))    #conf.folder_LE.text()
            
                if os.path.isdir(outdir):
                    gpxfilename = "pois.gpx"
                    outpath = os.path.join(outdir,gpxfilename)
                    os_ver = platform.version().split(".")
                    if os_ver[0]=="10":
                        os.system('copy "' + gpxfile.replace("/",os.sep) + '" "' + outpath.replace("/",os.sep) + '" ')
                    else:
                        shutil.copyfile(gpxfile, outpath)
                    QtGui.QMessageBox.information(self, "Gps-Datenuebertragung ","Die GPS-Datenuebertragung war erfolgreich! Die Wegpunkte wurden hierher kopiert: %s "%outpath); 
                    
                
                else:
                    QtGui.QMessageBox.critical(self, "Gps-Datenuebertragung fehlgeschlagen!","GPS-Geraet nicht gefunden (Das angegebene Verzeichnis %s existiert nicht)!"%outdir); 
            else:
                    QtGui.QMessageBox.critical(self, "Gps-Datenuebertragung fehlgeschlagen!","GPS-Geraet nicht gefunden (Das Laufwerk des GPS-Geraetes wurde nicht erkannt)!"); 
                
        else:
            QtGui.QMessageBox.critical(self, "Info2","kein export device typ gewaehlt (unter Einstellungen/GPS-Device)"); 
                    
            
    
    def focusDockWidget(self,mousemode):
        if mousemode == "temp":
            self.PixeltempDockWidget.raise_()
        if mousemode == "poi":
           self.PoisDockWidget.raise_()
           
        
    def loadSettings(self, s):
        [self.setTopDockWidget(w, s.value(v+"Focus")=="true") for w,v in self.dockwidgets]
        [w.setVisible(s.value(v+"Visible")=="true") for w,v in self.dockwidgets]
        size = QtCore.QSize(s.value('GUI/size'))
        pos = QtCore.QPoint(s.value('GUI/pos'))
        # screen = app.primaryScreen()  
        # if self.resetwindow:
            # self.resize(800,600)
            # self.move(0,0)
        # else:
            # curscreen = screenAt(pos)
            # if not curscreen:
                # pos = QtCore.QPoint(0,0)
                # curscreen = screenAt(pos)
            # size = size.boundedTo(curscreen.virtualSize())
            # self.resize(size)
            # self.move(pos)
        
        
        self.img.infoUI.CVfliphorCheckBox.setChecked(s.value('VIEW/fliphor')=="true")
        self.img.infoUI.CVflipverCheckBox.setChecked(s.value('VIEW/flipver')=="true")
        
    #    self.poiview.loadSettings(self.settings)
        
    def writeSettings(self,s):
        s.setValue('PATHS/rootdir', self.treemain.view.rootdir)
        s.setValue('PATHS/last', self.treemain.view.imgdir)
        if len(self.treemain.view.aralist)>0:
            s.setValue('PATHS/lastimgid', self.treemain.view.aralist[0]["id"])
            s.setValue('PATHS/lastimgname', self.treemain.view.aralist[0]["filename"])
        s.setValue('GUI/size', self.size())
        s.setValue('GUI/pos', self.pos())
        
        [s.setValue(v+"Visible",w.isVisible()) for w,v in self.dockwidgets]
        [s.setValue(v+"Focus",self.isTopDockWidget(w)) for w,v in self.dockwidgets]
        
        s.setValue('VIEW/fliphor',self.img.infoUI.CVfliphorCheckBox.isChecked())
        s.setValue('VIEW/flipver',self.img.infoUI.CVflipverCheckBox.isChecked())
     #   s.setValue("SDCARD/device",self.saveDialog.sourceLE.text())
    #    self.poiview.writeSettings()
        
        
    def shortcuts(self):
        self.escAction = QtGui.QAction('escape', self)
        self.clearAction = QtGui.QAction('clear', self)
        self.createKeyCtrl(self.escAction, QtCore.Qt.Key_Escape)
        self.createKeyCtrl(self.clearAction, QtCore.Qt.Key_C)
        
    def createKeyCtrl(self,actionName, key):
        actionName.setShortcut(QtGui.QKeySequence(key))
        self.addAction(actionName)
        
     
    def isTopDockWidget(self,widget):
        if widget.visibleRegion().isEmpty():
            return False
        else:
            return True
    
    def setTopDockWidget(self,widget,boolvar):
        if boolvar:
            widget.raise_()
   
    def closeEvent(self, e=None):
        self.settings.sync()
        self.writeSettings(self.settings)
        if self.useflight:
            self.flight.save()
        if e: e.accept()


def screenAt(*pos):
    #print (type(pos),type(*pos),pos,*pos)
    screens = app.screens()
    for s in screens:
        srect = s.availableGeometry()
        if srect.contains(pos[0] + QtCore.QPoint(10,10)):
            return s
    return app.primaryScreen()
    

def main():
    global app
    arg = docopt(__doc__, version=__version__)
    app = QtGui.QApplication(sys.argv)
    
    if os.name == "nt":
       import ctypes
       myappid = 'dlr.wildretter.poitagger.1' 
       ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app_icon = QtGui.QIcon()
    app_icon.addFile(os.path.join(PATHS["ICONS"],'poitagger/16x16_.png'), QtCore.QSize(16,16))
    app_icon.addFile(os.path.join(PATHS["ICONS"],'poitagger/24x24_.png'), QtCore.QSize(24,24))
    app_icon.addFile(os.path.join(PATHS["ICONS"],'poitagger/32x32_.png'), QtCore.QSize(32,32))
    app_icon.addFile(os.path.join(PATHS["ICONS"],'poitagger/48x48_.png'), QtCore.QSize(48,48))
    app_icon.addFile(os.path.join(PATHS["ICONS"],'poitagger/256x256_.png'), QtCore.QSize(256,256))
    
    imgdir = None
    rootdir = None
    if arg["<infolder>"] is not None:
        if os.path.isfile(arg["<infolder>"]):
            imgdir, file = os.path.split(arg["<infolder>"])
        if os.path.isdir(arg["<infolder>"]):
            imgdir = arg["<infolder>"]
    if arg["-r"] is not None:
        if os.path.isdir(arg["-r"]):
            rootdir = arg["-r"]
    window=Main(imgdir,rootdir,arg["-w"])
    
    
    window.setWindowIcon(app_icon)
    window.setWindowTitle("Poitagger " + str(__version__))
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()