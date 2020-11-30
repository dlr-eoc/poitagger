#import yaml
#import yamlordereddictloader
import os
import ast
from lxml import etree
import logging
from PyQt5 import QtCore,QtGui,uic, QtWidgets
from PyQt5.QtWidgets import QApplication,QWidget,QMainWindow, QLineEdit,QToolButton,QAction,QMessageBox,QPushButton,QVBoxLayout,QListWidget,QComboBox
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType 
import datetime
from collections import OrderedDict,MutableMapping,MutableSequence
from ast import literal_eval

from . import image
from . import utils2
from . import flightjson
from . import nested
from . import PATHS
from . import poimodel2
from . import upload

    
logger = logging.getLogger(__name__)

class PoiView(QMainWindow):
    sigJumpTo = QtCore.pyqtSignal(str)
    def __init__(self,settings,model):
        super().__init__()
        uic.loadUi(os.path.join(PATHS["UI"],'pois.ui'),self)
        self.dialog = upload.UploadDialog("Upload",settings)
        self.settings = settings
        self.t = ParameterTree(showHeader=False)
        self.model = model
        self.horizontalLayout.addWidget(self.t)#self.listw)
        self.cb = QComboBox()
        self.cb.currentTextChanged.connect(self.chooseLayer)
        self.actiondelLayer.triggered.connect(self.delLayer)
        #self.actionnewLayer.triggered.connect(self.newLayer)
        self.actionshow.triggered.connect(self.jumpTo)
        self.actionVisible.triggered.connect(self.setVis)
        self.actionUpload.triggered.connect(lambda: self.dialog.openPropDialog(self.model.pois))
        
        self.actionNeuerMarker.setChecked(utils2.toBool(self.settings.value('POIS/neuerMarker')))
        self.actionVisible.setChecked(utils2.toBool(self.settings.value('POIS/visible')))
        
    
    def setVis(self,trigger):
        self.settings.setValue('POIS/visible', str(self.actionVisible.isChecked()))
       # print("reproject",str(self.actionVisible.isChecked()))
        
    def setMeta(self,fm):
        self.model.loadMeta(fm)
        self.toolBar.addWidget(self.cb)
        self.p = fm.child("pois")
        self.loadComboBox()
        self.p.sigTreeStateChanged.connect(self.loadComboBox)
        
    def loadComboBox(self):
        self.cb.clear()
        layer = self.p.children()
        for i in layer:
            self.cb.addItem(i.name())
        self.cb.addItem("neue Ebene")
        if len(layer)>0:
            self.cb.setCurrentText(layer[-1].name())
        else:
            pass
            #print("HIER wird nochmal geladen")
          #  self.newLayer()
            
        
    def delLayer(self):
        self.p.removeChild(self.p.child(str(self.cb.currentText())))
        self.loadComboBox()
        
    def newLayer(self):
        last = len(self.p.children())
        dt = datetime.datetime.now().isoformat()
        description = "blabla"
        ts = {"name":"timestamp","type":"str", "value": dt,"readonly":False,"removable":False,"renamable":False}
        desc = {"name":"description","type":"str", "value": description, "readonly":False,"removable":False,"renamable":True}
        data = {"name":"data","type":"group", "readonly":False,"removable":False,"renamable":False,"children":[]}
        self.p.insertChild(last,{"name":str(last),"type":"group", "readonly":False,"removable":True,"renamable":True,"children":[ts,desc,data]})
        self.loadComboBox()
        return str(last)
        
    def chooseLayer(self,current):
        if str(current) == "neue Ebene":
            current = self.newLayer()
        childnames = [i.name() for i in self.p.children()]
        if not current in childnames: return
        try:
            self.t.clear()
        except:
            pass
            #logger.warning("clear failed")
        self.t.addParameters(self.p.child(str(current)).child("data"), showTop=False)
        
    def addPoi(self,value):
        currentdata = self.p.child(str(self.cb.currentText())).child("data")
        last = len(currentdata.children())
        #childnames = [i.name() for i in self.p.children()]
        defaultname = self.settings.value("POIS/defaultname") 
        currentdata.insertChild(last,{"name":defaultname+str(last),"value":value,"type":"group", "readonly":False,"expanded":False,"removable":True,"renamable":True})
        data = self.t.topLevelItem(0)
        currentItem = data.child(data.childCount()-1)
        self.t.setCurrentItem(currentItem)
        self.t.editItem(currentItem,0)
        
    def getPoisAsGpx(self):
        pois = []
        try:
            for L in self.p.children():
                for poi in L.child("data").children():
                    for view in poi.children():
                        val = literal_eval(view.value())
                       # print ("VAL",val,view.opts)
                        try:
                            pois.append({"name":poi.name(),"x":val[0],"y":val[1],"layer":L.name(),
                                "filename":view.name(), 
                                "lat":float(view.opts.get("latitude",0)),
                                "lon":float(view.opts.get("longitude",0)), 
                                "ele":float(view.opts.get("elevation",0)),
                                "uav_lat":float(view.opts["uav_lat"]), 
                                "uav_lon":float(view.opts["uav_lon"]),
                                "uav_ele":float(view.opts["uav_ele"]), 
                                "cam_yaw":float(view.opts["cam_yaw"]),
                                "cam_pitch":float(view.opts["cam_pitch"]), 
                                "cam_roll":float(view.opts["cam_roll"]),
                                "cam_euler_order":view.opts["cam_euler_order"],
                                "boresight_pitch":float(view.opts["boresight_pitch"]), 
                                "borsight_roll":float(view.opts["boresight_roll"]),
                                "boresight_yaw":float(view.opts["boresight_yaw"]), 
                                "boresight_euler_order":view.opts["boresight_euler_order"],
                                "found_time":view.opts["found_time"]})
                        except:
                            pois.append({"name":poi.name(),
                                "x":val[0],"y":val[1],
                                "layer":L.name(),
                                "filename":view.name()}) 
        except:
            logger.error("getPoisAsGpx failed",exc_info=True)
        return pois    
            
    def jumpTo(self): #jump in the treeview to the image that is currently selected
        logger.warning("image jumpTo")
        cur = self.t.currentItem()
        logger.warning(cur.param.opts)
        if cur== None: return
        if cur.param.opts.get("paramtyp")=="view":
            self.sigJumpTo.emit(cur.param.name())
        
    def addView(self,filename,x,y):
        if not self.actionNeuerMarker.isChecked(): return
        self.addPoi("Point")
        cur = self.t.currentItem()
        if not cur == None and cur.parent() == self.t.topLevelItem(0):  
            try:
                cur.param.addChild(self.model.reproject_poi(x,y))
                #cur.contextMenu.addAction('ShowImage').triggered.connect(self.jumpTo)
                #cur.param.setOpts(latitude=46.45234)
                #print("lat",cur.param.opts["latitude"])
                self.model.getPois(filename)
            except:
                logger.warning("addView",exc_info=True)
                QtGui.QMessageBox.information(self, "POI Ansicht ","Dieser POI wurde auf diesem Bild schon einmal gesetzt!"); 
        else:
            QtGui.QMessageBox.information(self, "POI setzen","Es ist noch kein POI angelegt bzw. ausgewählt!"); 
            
    def delParameter(self):
        c = self.t.currentItem().param
        reply = QMessageBox.question(self, "Parameter loeschen?","Soll der Parameter '{}'  tatsaechlich geloescht werden?".format(c.name()),QMessageBox.Yes,QMessageBox.No) 
        if reply == QMessageBox.Yes:
            c.remove()

    def writeSettings(self):
#       print("write Settings Poiview")
        self.dialog.writeSettings()
        #self.settings.setValue('WILDRETTERAPP/url', str(self.server.text()))
        self.settings.setValue('POIS/neuerMarker', str(self.actionNeuerMarker.isChecked()))
   
   # def saveState(self):
     #   with open("saveState.yml", 'w') as outfile:
     #       yaml.dump(self.p.saveState(), outfile, Dumper=yamlordereddictloader.Dumper, default_flow_style=False)
        
        
        
if __name__ == "__main__":
    
    import sys
    app = QApplication(sys.argv)
    path = "D:/WILDRETTER-DATEN/2017_DLR/2017-04-05_14-56_Hausen"
    #path = "."
    
    poi = PoiView()
    
    fm = flightjson.Flight()
    fm.load(path)
    #fm.loadfinished.connect(lambda: poi.setMeta(fm.p.child("pois")))
    poi.setMeta(fm.p.child("pois"))    
    poi.t1 = ParameterTree(showHeader=False)
    poi.t1.setParameters(poi.p, showTop=False)
    poi.horizontalLayout.addWidget(poi.t1)
        
    vbox = QVBoxLayout()
    poi.horizontalLayout.addLayout(vbox)
    but = QPushButton()
    but.setText("addView")
    vbox.addWidget(but)
    but.clicked.connect(lambda: poi.addView("04051456_0213.ARA",234,503))
    
    #but2 = QPushButton()
    #but2.setText("save")
    #vbox.addWidget(but2)
    #but2.clicked.connect(poi.save)
    
    but3 = QPushButton()
    but3.setText("add Param")
    vbox.addWidget(but3)
    but3.clicked.connect(lambda: poi.addPoi("{'name':'blabla','id':'46'}"))
    
    but4 = QPushButton()
    but4.setText("del Param")
    vbox.addWidget(but4)
    but4.clicked.connect(poi.delParameter)
    
    
   # but5 = QPushButton()
   # but5.setText("saveState")
   # vbox.addWidget(but5)
   # but5.clicked.connect(poi.saveState)
    
    #root.editingFinished.connect(lambda: fm.load(str(root.text())))
    poi.show()
    
    # Escape by Key
    poi.escAction = QAction('escape', poi)
    poi.escAction.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Escape))
    poi.addAction(poi.escAction)
    poi.escAction.triggered.connect(poi.close)
   
   
    sys.exit(app.exec_())

    