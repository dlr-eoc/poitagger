import yaml
import yamlordereddictloader
import json
import os
import ast
from ast import literal_eval
from lxml import etree
import logging
from PyQt5 import QtCore,QtGui,uic, QtWidgets,QtTest
from PyQt5.QtWidgets import QApplication,QWidget,QMainWindow, QLineEdit,QToolButton,QAction,QMessageBox,QPushButton,QVBoxLayout,QProgressDialog
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import datetime
from collections import OrderedDict,MutableMapping,MutableSequence,defaultdict

import numpy as np
import time

from . import image
from . import utils2
from . import nested
from . import PATHS

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
        if l==1: return {"name": str(k), 'type': "str", 'readonly':True,'value': v}
        return v
    if l>0 and kwargs["parentlist"][0] == "pois":
        return v
    #if l>2 and kwargs["parentlist"][0] == "pois" and  kwargs["parentlist"][2] == "data" :
    #    if l>4: return v
    #    elif l==4: return {"name": str(k), 'type': "str", 'readonly':True,'value': v}
    #    return {"name": str(k), 'type': "group", 'children': v}
        
    if not isinstance(v,(MutableMapping,MutableSequence,tuple)):
        return {"name": str(k), 'type': types.get(str(type(v)),"str"), 'readonly':False, 'decimals':9, 'value': v }
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
        uic.loadUi(os.path.join(PATHS["UI"],'flightmain.ui'),self)
        self.setWindowFlags(QtCore.Qt.Widget)
        self.t = ParameterTree(showHeader=False)
        self.horizontalLayout.addWidget(self.t)
        self.progressDialog = QProgressDialog("Task in progress...", "Cancel", 0,100,self)
        self.progressDialog.setWindowModality(QtCore.Qt.WindowModal)
        self.progressDialog.reset()
        
    def setMeta(self,fm):
        self.flight = fm
        self.t.setParameters(self.flight.p, showTop=False)
        self.actiondelete.triggered.connect(self.delete)
        self.actionimport.toggled.connect(self.flight.enableImport)
        self.actionsave.triggered.connect(self.flight.save)
        self.actionreload.triggered.connect(self.flight.load)
        self.flight.progress.connect(self.progressBar)
        self.flight.ifm.progress.connect(self.progressBar)
        self.flight.sigError.connect(self.errorMsg)
        self.flight.sigEmpty.connect(self.createMsg)
        
    
    def errorMsg(self,text):
        QtGui.QMessageBox.critical(self, "Speichern von poitagger.json fehlgeschlagen!",text)
        
    def createMsg(self):
        reply = QtGui.QMessageBox.question(self, "Flightmeta-Datei anlegen?","Dieser Ordner enthält noch keine Flightmeta-Datei (.poitagger.json). Zur Georeferenzierung ist dies nötig.",)
        if reply == QtGui.QMessageBox.Yes:
            self.flight.loadAndSave()
        else:
            self.flight.start()
            
    def progressBar(self,val):
        if val == 0:
            self.progressDialog.show()
        self.progressDialog.setValue(val)
        
    def delete(self):
        mypath = os.path.join(self.flight.path,self.flight.filename)
        if os.path.exists(mypath):
            reply = QMessageBox.question(self, "Flightmetadatei loeschen?","Soll die Datei '{}'  tatsaechlich geloescht werden?".format(mypath),QMessageBox.Yes,QMessageBox.No); 
            if reply == QMessageBox.Yes:
                os.remove(mypath)
    
    def save(self):
        tree = self.flight.p.getValues()
        n = nested.Nested(tree,nested.paramtodict,nested.paramtodict,tupletype=list)
        self.flight.set(n.data)
        
    def addParameter(self):
        c = self.t.currentItem().param
        if not c.isType("group"): c = c.parent()
        last = len(c.children())
        c.insertChild(last,{"name":"","value":"","type":"str", "readonly":False,"removable":True,"renamable":True})
    
    def addPoi(self,value):
        c = self.flight.p.child("pois")
        last = len(c.children())
        c.insertChild(last,{"name":str(last),"value":value,"type":"str", "readonly":False,"removable":True,"renamable":True})

    def delParameter(self):
        c = self.t.currentItem().param
        reply = QMessageBox.question(self, "Parameter loeschen?","Soll der Parameter '{}'  tatsaechlich geloescht werden?".format(c.name()),QMessageBox.Yes,QMessageBox.No) 
        if reply == QMessageBox.Yes:
            c.remove()
        
    def saveState(self):
           with open("saveState.json", 'w') as outfile:
                json.dump(self.p.saveState(), outfile) #, Dumper=yamlordereddictloader.Dumper, default_flow_style=False)
                
    def test(self):
        print (self.flight.p.child("children").child("general").child("path").value())
        
class Flight(QtCore.QObject): #QThread
    import_enabled = False
    pois = QtCore.pyqtSignal(list)
    poisChanged = QtCore.pyqtSignal()
    uavpath = QtCore.pyqtSignal(list)
    calibration = QtCore.pyqtSignal(dict)
    general = QtCore.pyqtSignal(Parameter)
    changed = QtCore.pyqtSignal()
    loadfinished = QtCore.pyqtSignal()
    sigError = QtCore.pyqtSignal(str)
    sigEmpty = QtCore.pyqtSignal()
    sigClear = QtCore.pyqtSignal()
    
    progress = QtCore.pyqtSignal(int)
    path = None
    
    def __init__(self, filename= ".poitagger.json"):
        super().__init__()
        self.filename= filename
        self.ifm = ImportFlightMeta()
        categories= [{"name":"general",'type':"group",'children':[{'name':'images','type':'group','children':[{'name':'width','type':'int'},{'name':'height','type':'int'}]}]},
                    {"name":"calibration",'type':"group"},
                    {"name":"pois",'type':"group"},
                    {"name":"images",'type':"group"},
                    {"name":"uavpath",'type':"group"}]
        self.p = Parameter.create(name="flightparam",type="group",children=categories)
        self.ifm.finished.connect(self.setFromImport)
        
        self.p.child("general").sigTreeStateChanged.connect(self.prepareGeneral)
        self.p.child("uavpath").sigValueChanged.connect(self.prepareUavPath)
        self.p.child("pois").sigTreeStateChanged.connect(self.__loadPoisList)
        self.p.child("pois").sigTreeStateChanged.connect(lambda: self.poisChanged.emit())
        self.save_after_loading = False 
        self.loadfinished.connect(self.savehandler)
        
    def prepareGeneral(self,generalparam):
        if generalparam.children()== [] : return
        self.general.emit(generalparam)
        
    # def preparePois(self,poisparam):
        # #print("FM, POIS JETZT" )
        # if len(poisparam.getValues())==0: return
        # poisdict = nested.Nested(poisparam.getValues(),nested.paramtodict,nested.pre_paramtodict,tupletype=list).data
        # #print(poisdict)
      # #  with open("test.txt","w") as f:
      # #      f.write(str(poisdict["0"]["data"]))
        # pois = []
        # try:
            # for i in poisdict["0"]["data"]:
                # print ("POI",i)
                # entry = eval(i)
                # #entry = dict(i)
                # if "id" in entry:
                    # pois.append(entry)
        # except:
            # logging.warning("flightmeta: append poi failed",exc_info=True)
        # self.pois.emit(pois)
        # #p = poisparam.getValues()
        # #print(len(p),p["0"][1]["data"][1])
       # # if len(p)>0:
       # #     print(p["0"])
    
    def __loadPoisList(self):
        layer = self.p.child("pois").children()
        pois = []
        try:
            for L in layer:
                poisdata = L.child("data").children()
                for poi in poisdata:
                    for view in poi.children():
                        val = literal_eval(view.value())
                        pois.append({"name":poi.name(),"x":val[0],"y":val[1],"layer":L.name(),"filename":view.name(),
                            "lat":float(view.opts["latitude"]),"lon":float(view.opts["longitude"]),"ele":float(view.opts["elevation"]),
                            "uav_lat":float(view.opts["uav_lat"]),"uav_lon":float(view.opts["uav_lon"]),"uav_ele":float(view.opts["uav_ele"]),
                            "cam_yaw":float(view.opts["cam_yaw"]),"cam_pitch":float(view.opts["cam_pitch"]),"cam_roll":float(view.opts["cam_roll"]),
                            "cam_euler_order":view.opts["cam_euler_order"],
                            "boresight_pitch":float(view.opts["boresight_pitch"]),"boresight_roll":float(view.opts["boresight_roll"]),
                            "boresight_yaw":float(view.opts["boresight_yaw"]),
                            "borsight_euler_order":view.opts["boresight_euler_order"],
                            "found_time":view.opts["found_time"]})
        except:
            logging.warning("loadPoisList failed",exc_info=True)
       # print(pois)
        self.pois.emit(pois)
        
    def prepareUavPath(self,uavpathparam):
        if uavpathparam.value()== None : return
        pathlist = list(uavpathparam.value())
        self.uavpath.emit(pathlist)
    
    def setOrientation(self,val):
        self.p.child("general").child("images").child("orientation").setValue(val)
        
    def enableImport(self,toggle):
        self.import_enabled = toggle
    
    def setFromImport(self,value):
        self.task = "restoreParameter"
        #print(value)
        self.meta = value
        #print(self.meta)
        # self.meta["children"]["general"]["children"]["orientation"] = {'name': 'orientation', 'type': 'group', 'children': [
            # {'name': 'flip lr', 'type': 'bool'},
            # {'name': 'flip up', 'type': 'bool'},
            # {'name': 'flip diag', 'type': 'bool'}
        # ]}
        self.start()

    
    def start(self): #run
        self.progress.emit(0)
        if self.task == "restoreParameter":
            self.p.child("general").restoreState(self.meta["children"]["general"])
            self.p.child("pois").restoreState(self.meta["children"]["pois"])
            self.progress.emit(40)
            self.p.child("uavpath").restoreState(self.meta["children"]["uavpath"])
            self.progress.emit(60)
            self.p.child("calibration").restoreState(self.meta["children"]["calibration"])
            self.progress.emit(80)
            self.p.child("images").restoreState(self.meta["children"]["images"])
        else:
            #print("TASK",self.task)
            self.p.child("general").clearChildren()
            self.p.child("pois").clearChildren()
            #self.p.child("images").clearChildren()
            self.p.child("uavpath").clearChildren()
            self.p.child("calibration").clearChildren()
        self.progress.emit(100)
        self.loadfinished.emit()
        #if self.task=="loadEmpty":
           # print("loadEmpty")
           # self.sigClear.emit()
        
    def loadAndSave(self):
        #print("loadANdSave")
        self.enableImport(True)
        self.save_after_loading=True
        self.load()
        self.enableImport(False)
    
    def savehandler(self):
        #print("nowSave",self.save_after_loading)
        if self.save_after_loading:
            self.save()
            self.save_after_loading = False
            
    def load(self,path=None,filename=None):
        self.progress.emit(0)
            
        if path:
            self.path = path
        if filename:
            self.filename = filename
        try:
            myjson = os.path.join(self.path,self.filename)
            if self.import_enabled:
                self.ifm.load(self.path)
            elif os.path.exists(myjson):
                #self._loadJson()
                self.ifm.load(myjson,True)
            else:
    #            print("Empty")
                self._loadEmpty()
        except:
     #       print("Empty")
            self._loadEmpty()
#            logging.warning("Loading flightmeta failed")
        
    def _loadEmpty(self):
        hasimages = False
        for file in os.listdir(self.path):
            if os.path.splitext(file)[1].lower() in image.SUPPORTED_EXTENSIONS: 
                hasimages=True
        self.task = "loadEmpty"
        if hasimages:
            self.sigEmpty.emit()
            return
        self.start()
        
    def _loadJson(self):
        self.task = "loadJson"
        self.start()
        
    def save(self):
        if self.path == None: return
        if self.task == "loadEmpty": return
        try:
            ppath = str(self.p.child("general").child("path").value())
            text = "Der Pfad aus .poitagger.json stimmt nicht mit dem Speicherort überein.\n .poitagger.json: {0}, Speicherort: {1}".format(ppath,self.path)
            if not ppath==self.path:
                logging.warning(text)
                self.sigError.emit(text)
            else:
                self.save_ok()
        except:
            logging.error("Flightmeta save", exc_info=True)
    
    def save_ok(self):
            fpath = os.path.join(self.path,self.filename)
            if os.name == "nt":
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(fpath, 128)
                with open(fpath, 'w') as outfile:
                    json.dump(self.p.saveState(), outfile)#, Dumper=yamlordereddictloader.Dumper, default_flow_style=False)
                ctypes.windll.kernel32.SetFileAttributesW(fpath, 2)
            else:
                with open(fpath, 'w') as outfile:
                    json.dump(self.p.saveState(), outfile)#, Dumper=yamlordereddictloader.Dumper, default_flow_style=False)
            
    #def change(self):
    #    print("flight.change()")
    #    print (self.p.child("uavpath").value())
    #    print(self.p.child("general").child("bounding").getValues())
       # print (self.p.child("uavpath").saveState())
       ##print (self.p.child("general").saveState())
       # self.set("blablabla",["general","path"])
        

        
class ImportFlightMeta(QtCore.QThread):
    finished = QtCore.pyqtSignal(dict)
    progress = QtCore.pyqtSignal(int)
    loadJson = False
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.Meta = {"general":None,"pois":[],"uavpath":[],"images":[], "calibration": {"geometric":{},"radiometric":{},"boresight":{}}}
        
    def load(self,path=None,loadJson=False):
        self.path = path
        self.loadJson=loadJson
        self.start()
      
    def _loadImagesHeader(self):
        self.ImgHdr = []
        self.ImgList = []
        path = self.path
        if path == "": return self.ImgHdr
        Dir = sorted(os.listdir(path))
        num = float(len(Dir))
       # print(num)
        try:
            for k,file in enumerate(Dir):
                #print(int((k/num)*60))
                if k%10==0:
                    self.progress.emit(int((k/num)*60))
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
                if i["gps"].get("longitude") != None:
                    self.uavpath.append([float(i["gps"].get("longitude")), float(i["gps"].get("latitude"))])
        except:
            logging.error("FM _createUavPath failed",exc_info=True)
        
    def _generalParams(self):
        Width = []
        Height = []
        Bitdepth = []
        width = 0
        height = 0
        bitdepth = 0
        orientation = 0
        try:
            for i in self.ImgHdr:
                if i["rawimage"].get("width") != None:
                    Width.append(i["rawimage"].get("width"))
                    Height.append(i["rawimage"].get("height"))
                    Bitdepth.append(i["rawimage"].get("bitdepth"))
                elif i["image"].get("width") != None:
                    Width.append(i["image"].get("width"))
                    Height.append(i["image"].get("height"))
                    Bitdepth.append(i["image"].get("bitdepth"))
            
            if Width.count(Width[0])==len(Width): width = Width[0]
            else: width = np.bincount(Width).argmax() #achtung rundet ab!
            if Height.count(Height[0])==len(Height): height = Height[0]
            else: height = np.bincount(Height).argmax() #achtung rundet ab!
            if Bitdepth.count(Bitdepth[0])==len(Bitdepth): bitdepth = Bitdepth[0]
            else: bitdepth = np.bincount(Bitdepth).argmax() #achtung rundet ab!
        except:
            logging.error("FM _generalParams failed",exc_info=True)
        return {"bounding":self._getBounding(self.ImgHdr),"path":self.path,"images": {"width":width,"height":height,"bitdepth":bitdepth,"orientation":orientation}}
        
    def _getBounding(self,ImgHdr):
        Lat, Lon = [],[]
        for i in ImgHdr:
            lat = i["gps"].get("latitude",None)
            lon = i["gps"].get("longitude",None)
            if lat is not None: Lat.append(lat) 
            if lon is not None: Lon.append(lon) 
        if 0 in [len(Lat),len(Lon)]: return [[None,None],[None,None]]
        return [[min(Lon),min(Lat)],[max(Lon),max(Lat)]]
        
    def _loadCalibration(self):
        Geom = defaultdict(list)
        Radi = defaultdict(list)
        Bore = defaultdict(list)
        for i in self.ImgHdr:
            for k,v in i["calibration"]["geometric"].items(): Geom[k].append(v)
            for k,v in i["calibration"]["radiometric"].items(): Radi[k].append(v)
            for k,v in i["calibration"]["boresight"].items(): 
                #print("boresight:",k,v)
                Bore[k].append(v)
        geom,radi,bore = {},{},{}
        
        for k,v in Geom.items(): 
            if v.count(v[0])==len(v): geom[k] = v[0]
            else: 
                print("GEOM",k,v[0],np.bincount(v).argmax())
                geom[k] = np.bincount(v).argmax() #achtung rundet ab!
        for k,v in Radi.items(): 
            if v.count(v[0])==len(v): radi[k] = v[0]
            else: radi[k] = np.bincount(v).argmax() #achtung rundet ab!
        for k,v in Bore.items(): 
            if v.count(v[0])==len(v): bore[k] = v[0]
            else: bore[k] = np.bincount(v).argmax() #achtung rundet ab!
        print (len(bore),bore)
            
        self.calibration = {"geometric":geom,"radiometric":radi,"boresight":bore}
        
            
    def _importPois(self, poisxmlfile = "pois.xml"):
        xslt_root = etree.XML('''\
    <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:template match="/pois">
    [<xsl:for-each select="p1oi">{ "name": "<xsl:value-of select="name/text()"/>",
      "filename": "<xsl:value-of select="filename/text()"/>",
      "latitude": "<xsl:value-of select="latitude/text()"/>",
      "longitude": "<xsl:value-of select="longitude/text()"/>",
      "pixel_x":  "<xsl:value-of select="pixel_x/text()"/>",
      "pixel_y":  "<xsl:value-of select="pixel_y/text()"/>",
      "elevation":  "<xsl:value-of select="elevation/text()"/>",
      "uav_longitude":  "<xsl:value-of select="uav_longitude/text()"/>",
      "uav_latitude":  "<xsl:value-of select="uav_latitude/text()"/>",
      "uav_elevation":  "<xsl:value-of select="uav_elevation/text()"/>",
      "uav_yaw":  "<xsl:value-of select="uav_yaw/text()"/>",
      "cam_pitch":  "<xsl:value-of select="cam_pitch/text()"/>",
      "pitch_offset":  "<xsl:value-of select="pitch_offset/text()"/>",
      "roll_offset":  "<xsl:value-of select="roll_offset/text()"/>",
      "yaw_offset":  "<xsl:value-of select="yaw_offset/text()"/>",
      "found_time":  "<xsl:value-of select="found_time/text()"/>"},</xsl:for-each>]</xsl:template>
    </xsl:stylesheet>''')
        transform = etree.XSLT(xslt_root)
        doc = etree.parse(poisxmlfile)
        result_tree = transform(doc)
        try:
            pois = json.loads(str(result_tree)[23:-3]+"]")
        except:
            logging.error("convert pois.xml to json failed")
            pois = []
        if pois == None: pois = []
        ts = datetime.datetime.fromtimestamp(os.path.getmtime(self.path)).isoformat()
        P = []
        for k,i in enumerate(pois):
            # if not i["found_time"] is None: 
                # try:
                    # ft = i["found_time"].isoformat()
                # except:
                    # ft = datetime.datetime.fromtimestamp(i["found_time"]).isoformat()
            # else:
                # ft = ""
            P.append({"name":"_".join([str(i["name"]),str(k)]), "type":"group", 
                        "expanded":False, "renamable":True, "removable":True, "children": [{ 
                        "name":i["filename"],"value":(i["pixel_x"],i["pixel_y"]), 
                        "readonly":True, "paramtyp":"view", "removeable":True, "type":"str","renameable":False, 
                        "latitude":i["latitude"],"longitude":i["longitude"],"elevation":i["elevation"],
                        "uav_lat":i["uav_latitude"],"uav_lon":i["uav_longitude"],"uav_ele":i["uav_elevation"],
                        "cam_yaw":i["uav_yaw"],"cam_pitch":-float(i["cam_pitch"]),"cam_roll":0,
                        #"cam_dx":0.2,"cam_dy":0,"cam_dz":0,
                        "cam_euler_order":"ZXY",
                        "boresight_pitch":-float(i["pitch_offset"]),"boresight_roll":i["roll_offset"],"boresight_yaw":i["yaw_offset"],
                        "boresight_euler_order":"ZYX",
                        "found_time":i["found_time"] }]})
        out = {"name":"pois","type":"group", "expanded":True, "children":[{"name":"0","type":"group","children": [{"name":"timestamp","type":"str","readonly":True,
                "value":ts},{"name":"description","type":"str","readonly":False,"value":"initial dataset"},
                        {"name":"data","type":"group","readonly":True,"expanded":True, "children":P}]}]}
        return out
    
    def run(self):
        if self.loadJson:
            try:
                with open(self.path, 'r') as stream:
                    self.Meta = json.load(stream)#,Loader=yamlordereddictloader.Loader))
            except:
                logging.error("Flightmeta load", exc_info=True)
        else:
            self.pois = {"name":"pois","type":"group", "expanded":True, "children":[]}
            self. images = []
            self.calibration = {}
            self.ImgHdr = self._loadImagesHeader()
            self.progress.emit(60)
            self._loadCalibration()
            self.progress.emit(70)
            self._createUavPath()
            self.progress.emit(80)
            self.general = self._generalParams()
            self.progress.emit(90)
            m = {"general": self.general, "pois":self.pois, "calibration": self.calibration, "images": self.images, "uavpath": self.uavpath}
            self.Meta.update(m)
            poispath = os.path.join(self.path, "pois.xml")
            if os.path.exists(poispath):
                self.pois = self._importPois(poispath)
            self.Meta["pois"] = self.pois
            self.progress.emit(100)
            self.Meta = nested.Nested(self.Meta,dictToParam).data    
            
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
    
    but2 = QPushButton()
    but2.setText("save")
    vbox.addWidget(but2)
    but2.clicked.connect(win.save)
    
    but3 = QPushButton()
    but3.setText("add Param")
    vbox.addWidget(but3)
    but3.clicked.connect(lambda: win.addPoi("{'name':'blabla','id':'46'}"))
    
    but4 = QPushButton()
    but4.setText("del Param")
    vbox.addWidget(but4)
    but4.clicked.connect(win.delParameter)
    
    
    but5 = QPushButton()
    but5.setText("saveState")
    vbox.addWidget(but5)
    but5.clicked.connect(win.saveState)
    
    but6 = QPushButton()
    but6.setText("test")
    vbox.addWidget(but6)
    but6.clicked.connect(win.test)
    
    ldbut.clicked.connect(lambda: fm.load(str(root.text())))
    win.show()
    
    # Escape by Key
    win.escAction = QAction('escape', win)
    win.escAction.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Escape))
    win.addAction(win.escAction)
    win.escAction.triggered.connect(win.close)
   
   
    sys.exit(app.exec_())

    