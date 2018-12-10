import yaml
import os
import image
from lxml import etree
import logging
import utils2
from PyQt5 import QtCore,QtGui,uic, QtWidgets
from PyQt5.QtWidgets import QApplication,QWidget,QMainWindow, QLineEdit,QToolButton,QAction,QMessageBox,QPushButton,QVBoxLayout
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType 
from datetime import datetime
from collections import OrderedDict,MutableMapping,MutableSequence
import nested

types = {"<class 'int'>":"int",
        "<class 'float'>":"float",
        "<class 'str'>":"str",
        "<class 'bool'>":"bool",
        "<class 'bytes'>":"str"}

def getBranch(container,branchlist):
    if len(branchlist)==0:
        return container
    else: 
        return getBranch(container.get(branchlist.pop(0)),branchlist)

def setBranch(container,branchlist,newvalue):
    last = branchlist.pop()
    getBranch(container,branchlist).__setitem__(last,newvalue)
 
def dictToParam(k,v,**kwargs):
    '''
    this is a callback function for nested. it converts the output of saveState() from a Parameter from the pyQtGraph module.
    This output is an OrderedDict with specific structure like the following:
    
    calling nested with this callbackfunction leads to a parameter state dictionary:
    '''
    l = len(kwargs["parentlist"])
    if l>0 and kwargs["parentlist"][0] == "uavpath":
        if l==1: return {"name": str(k), 'type': "str", 'value': v}
        return v
    if l>2 and kwargs["parentlist"][0] == "pois" and  kwargs["parentlist"][2] == "data" :
        if l>4: return v
        elif l==4: return {"name": str(k), 'type': "str", 'value': v}
        return {"name": str(k), 'type': "group", 'children': v}
        
    if not isinstance(v,(MutableMapping,MutableSequence,tuple)):
        return {"name": str(k), 'type': types.get(str(type(v)),"str"),  'decimals':9, 'value': v }
    else:
        return {"name": str(k), 'type': "group", 'children': v}
    
def pre_paramStateReduce(k,v,**kwargs):
    '''
    this is a callback function for nested. it converts the output of saveState() from a Parameter from the pyQtGraph module.
    This output is an OrderedDict with specific structure like the following:
    
    calling nested with this callbackfunction leads tO a reduced dictionary:
    '''
    if (type(v) == dict): 
        myval = {}
        for key,val in v.items():
            if not key in ['decimals', 'default','enabled','name', 'readonly',
                           'removable','renamable','strictNaming','title', 'visible']:
                if v.get("type")!="group":
                    if key in ["expanded"]: 
                        continue
                else:
                    if key in ["value"]: 
                        continue
                myval[key] = val
        return myval
    return v
        
    
class FlightWidget(QMainWindow):
    def __init__(self,parent = None):
        super(FlightWidget, self).__init__(parent)
        uic.loadUi('poitagger/ui/flightmain.ui',self)
        self.setWindowFlags(QtCore.Qt.Widget)
        self.t = ParameterTree()
        self.horizontalLayout.addWidget(self.t)
        
    def setMeta(self,fm):
        self.flight = fm
        self.t.setParameters(self.flight.p, showTop=False)
        self.actiondelete.triggered.connect(self.delete)
        self.actionimport.toggled.connect(self.flight.enableImport)
        self.actionsave.triggered.connect(self.flight.save)
        self.actionreload.triggered.connect(self.flight.load)
    
    def delete(self):
        mypath = os.path.join(self.flight.path,self.flight.filename)
        if os.path.exists(mypath):
            reply = QMessageBox.question(self, "Flightmetadatei loeschen?","Soll die Datei '{}'  tatsaechlich geloescht werden?".format(mypath),QMessageBox.Yes,QMessageBox.No); 
            if reply == QMessageBox.Yes:
                os.remove(mypath)
    
    def save(self):
        tree = self.p.getValues()
        n = nested.Nested(tree,nested.paramtodict,nested.paramtodict,tupletype=list)
        self.flight.set(n.data)
        
    def addParameter(self):
        c = self.t.currentItem().param
        if not c.isType("group"): c = c.parent()
        last = len(c.children())
        c.insertChild(last,{"name":"","value":"","type":"str", "readonly":False,"removable":True,"renamable":True})

    def delParameter(self):
        c = self.t.currentItem().param
        reply = QMessageBox.question(self, "Parameter loeschen?","Soll der Parameter '{}'  tatsaechlich geloescht werden?".format(c.name()),QMessageBox.Yes,QMessageBox.No) 
        if reply == QMessageBox.Yes:
            c.remove()
        
    def saveState(self):
           with open("saveState.yml", 'w') as outfile:
                yaml.dump(self.p.saveState(), outfile, default_flow_style=False)
                
    
class Flight(QtCore.QThread):
    import_enabled = False
    pois = QtCore.pyqtSignal(list)
    uavpath = QtCore.pyqtSignal(list)
    calibration = QtCore.pyqtSignal(dict)
    general = QtCore.pyqtSignal(dict)
    changed = QtCore.pyqtSignal()
    path = None
    def __init__(self, filename= "flightmeta.yml"):
        super().__init__()
        self.filename= filename
        self.ifm = ImportFlightMeta()
        categories= [{"name":"general",'type':"group"},
                    {"name":"calibration",'type':"group"},
                    {"name":"pois",'type':"group"},
                    {"name":"images",'type':"group"},
                    {"name":"uavpath",'type':"group"}]
        self.p = Parameter.create(name="flightparam",type="group",children=categories)
        self.ifm.finished.connect(self.setFromImport)
        #self.p.child("general").sigTreeStateChanged.connect(self.general.emit)
        #self.p.child("pois").sigTreeStateChanged.connect(self.pois.emit)
        self.p.child("uavpath").sigValueChanged.connect(self.prepareUavPath)
        self.p.child("pois").sigTreeStateChanged.connect(self.preparePois)
        
    def preparePois(self,poisparam):
        #print("FM, POIS JETZT" )
        poisdict = nested.Nested(poisparam.getValues(),nested.paramtodict,nested.pre_paramtodict,tupletype=list).data
        #print(poisdict)
        pois = []
        try:
            
            for i in poisdict["0"]["data"]:
                entry = dict(i)
                if "id" in entry:
                    pois.append(entry)
        except:
            logging.warning("flightmeta: append poi failed",exc_info=True)
        self.pois.emit(pois)
        #p = poisparam.getValues()
        #print(len(p),p["0"][1]["data"][1])
       # if len(p)>0:
       #     print(p["0"])
    def prepareUavPath(self,uavpathparam):
        pathlist = list(uavpathparam.value())
        self.uavpath.emit(pathlist)
        
    def enableImport(self,toggle):
        self.import_enabled = toggle
    
   
    def setFromImport(self,value):
        self.task = "restoreParameter"
        self.meta = nested.Nested(value,dictToParam).data
        self.start()

    def run(self):
        if self.task == "restoreParameter":
            self.p.restoreState(self.meta)
            
        elif self.task == "loadYaml":
            try:
                with open(os.path.join(self.path,self.filename), 'r') as stream:
                    self.p.restoreState(yaml.load(stream))
            except:
                logging.error("Flightmeta load", exc_info=True)
                
        
    def load(self,path=None,filename=None):
        if path:
            self.path = path
        if filename:
            self.filename = filename
        try:
            myyaml = os.path.join(self.path,self.filename)
            if self.import_enabled:
                self.ifm.load(self.path)
            elif os.path.exists(myyaml):
                self._loadYaml()
        except:
            logging.warning("Loading flightmeta failed")
    
    def _loadYaml(self):
        self.task = "loadYaml"
        self.start()
        
    def save(self):
        if self.path == None: return
        try:
            fpath = os.path.join(self.path,self.filename)
            if os.name == "nt":
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(fpath, 128)
                with open(fpath, 'w') as outfile:
                    yaml.dump(self.p.saveState(), outfile, default_flow_style=False)
                ctypes.windll.kernel32.SetFileAttributesW(fpath, 2)
            else:
                with open(fpath, 'w') as outfile:
                    yaml.dump(self.p.saveState(), outfile, default_flow_style=False)
        except:
            logging.error("Flightmeta save", exc_info=True)
            
    def change(self):
        print("flight.change()")
        print (self.p.child("uavpath").value())
        print(self.p.child("general").child("bounding").getValues())
       # print (self.p.child("uavpath").saveState())
       ##print (self.p.child("general").saveState())
       # self.set("blablabla",["general","path"])
        

        
class ImportFlightMeta(QtCore.QThread):
    finished = QtCore.pyqtSignal(dict)
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.Meta = {"general":None,"pois":[],"uavpath":[],"calibration":None}
        
    def load(self,path=None):
        self.path = path
        self.start()
        
    def _loadImagesHeader(self):
        self.ImgHdr = []
        self.ImgList = []
        path = self.path
        if path == "": return self.ImgHdr
        try:
            for file in sorted(os.listdir(path)):
                if os.path.splitext(file)[1].lower() not in image.SUPPORTED_EXTENSIONS: continue
                img = image.Image.factory(os.path.join(path,file),onlyheader=True)    
                self.ImgHdr.append(img.header)
            return self.ImgHdr
        except:
            logging.error("FM _loadImgHeader failed", exc_info = True)
            return self.ImgHdr
            
    def _createUavPath(self):
        self.uavpath = []
        try:
            for i in self.ImgHdr:
                self.uavpath.append([float(i["gps"].get("longitude")), float(i["gps"].get("latitude"))])
        except:
            logging.error("FM _createUavPath failed",exc_info=True)
        
    def _getBounding(self,ImgHdr):
        Lat, Lon = [],[]
        for i in ImgHdr:
            lat = i["gps"].get("latitude",None)
            lon = i["gps"].get("longitude",None)
            if lat is not None: Lat.append(lat) 
            if lon is not None: Lon.append(lon) 
        if 0 in [len(Lat),len(Lon)]: return [[None,None],[None,None]]
        return [[min(Lon),min(Lat)],[max(Lon),max(Lat)]]
    
    def _importPois(self, poisxmlfile = "pois.xml"):
        xslt_root = etree.XML('''\
    <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:template match="/pois">
    <xsl:for-each select="p1oi">
    - name: <xsl:value-of select="name/text()"/>
      id: <xsl:value-of select="id/text()"/>
      filename: <xsl:value-of select="filename/text()"/>
      latitude: <xsl:value-of select="latitude/text()"/>
      longitude: <xsl:value-of select="longitude/text()"/>
      pixel_x:  <xsl:value-of select="pixel_x/text()"/>
      pixel_y:  <xsl:value-of select="pixel_y/text()"/>
      elevation:  <xsl:value-of select="elevation/text()"/>
      uav_longitude:  <xsl:value-of select="uav_longitude/text()"/>
      uav_latitude:  <xsl:value-of select="uav_latitude/text()"/>
      uav_elevation:  <xsl:value-of select="uav_elevation/text()"/>
      uav_yaw:  <xsl:value-of select="uav_yaw/text()"/>
      cam_pitch:  <xsl:value-of select="cam_pitch/text()"/>
      pitch_offset:  <xsl:value-of select="pitch_offset/text()"/>
      roll_offset:  <xsl:value-of select="roll_offset/text()"/>
      yaw_offset:  <xsl:value-of select="yaw_offset/text()"/>
      found_time:  <xsl:value-of select="found_time/text()"/>
    </xsl:for-each>
    </xsl:template>
    </xsl:stylesheet>''')
        transform = etree.XSLT(xslt_root)
        doc = etree.parse(poisxmlfile)
        result_tree = transform(doc)
        pois = yaml.load(str(result_tree)[23:])
        if pois == None: pois = []
        ts = datetime.fromtimestamp(os.path.getmtime(self.path)).isoformat()
        return [{"timestamp": ts,"description":"initial dataset","data":pois}]
    
    def run(self):
        self.pois = []
        self.calibration = {}
        self.ImgHdr = self._loadImagesHeader()
        self._createUavPath()
        self.general = {"bounding":self._getBounding(self.ImgHdr),"path":self.path}
        m = {"general": self.general, "pois":self.pois, "calibration": self.calibration, "uavpath": self.uavpath}
        self.Meta.update(m)
        poispath = os.path.join(self.path, "pois.xml")
        if os.path.exists(poispath):
            self.pois = self._importPois(poispath)
        self.Meta["pois"] = self.pois
        self.finished.emit(self.Meta)
        
        
        
if __name__ == "__main__":
    
    import sys
    app = QApplication(sys.argv)
    path = "D:/WILDRETTER-DATEN/2017_DLR/2017-04-05_14-56_Hausen"
    
    
    win = FlightWidget()
    root = QLineEdit()
    root.insert(path)
    ldbut = QPushButton()
    ldbut.setText("Load")
    win.toolBar.addWidget(root)
    win.toolBar.addWidget(ldbut)
    fm = Flight()
    fm.load(path)
    win.setMeta(fm)    
    
    vbox = QVBoxLayout()
    win.horizontalLayout.addLayout(vbox)
    but = QPushButton()
    but.setText("change")
    vbox.addWidget(but)
    but.clicked.connect(fm.change)
    
    but2 = QPushButton()
    but2.setText("save")
    vbox.addWidget(but2)
    but2.clicked.connect(win.save)
    
    but3 = QPushButton()
    but3.setText("add Param")
    vbox.addWidget(but3)
    but3.clicked.connect(win.addParameter)
    
    but4 = QPushButton()
    but4.setText("del Param")
    vbox.addWidget(but4)
    but4.clicked.connect(win.delParameter)
    
    
    but5 = QPushButton()
    but5.setText("saveState")
    vbox.addWidget(but5)
    but5.clicked.connect(win.saveState)
    
    #root.editingFinished.connect(lambda: fm.load(str(root.text())))
    ldbut.clicked.connect(lambda: fm.load(str(root.text())))
    win.show()
    
    # Escape by Key
    win.escAction = QAction('escape', win)
    win.escAction.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Escape))
    win.addAction(win.escAction)
    win.escAction.triggered.connect(win.close)
   
   
    sys.exit(app.exec_())

    