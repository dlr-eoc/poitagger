"""
QWebKit wurde ersetzt durch QWebEngine.
Funktioniert ganz anders, deshalb geht das alles hier  nicht!
"""

from PyQt5 import QtCore,QtGui,uic, QtWebEngineWidgets, QtPrintSupport
from PyQt5.QtWidgets import QMainWindow,QApplication,QPushButton

from lxml import etree
import ast
import traceback
import os
import functools
import copy
import numpy as np
import logging
from . import PATHS

WIDTH = 0.00003
HEIGHT = 0.00003


logger = logging.getLogger(__name__)

class GeoWidget(QMainWindow): 
    def __init__(self,settings):
        super().__init__()
        uic.loadUi(os.path.join(PATHS["UI"],'geomain.ui'),self)
        self.setWindowFlags(QtCore.Qt.Widget)
        self.settings = settings
        self.view = Browser(settings)
        self.view.setSizeHint(200,300)
        self.setCentralWidget(self.view)
        self.imgdir = ""
        self.imgheader = {}
        #self.view.lat = 0.0
        #self.view.lon = 0.0
        self.connections()
        
    def connections(self):
        self.actionUAV_Pfad.triggered.connect(lambda: self.view.setLayerVisible("uavpath",self.actionUAV_Pfad.isChecked()))
        self.actionDroneVisible.triggered.connect(lambda: self.view.setLayerVisible("uav",self.actionDroneVisible.isChecked()))
        self.actionPoisVisible.triggered.connect(lambda: self.view.setLayerVisible("pois",self.actionPoisVisible.isChecked()))
        self.actionUAV_position.toggled.connect(self.view.followUavPosition)
        self.actionGoogleMaps.triggered.connect(self.loadGoogleMaps)
        self.actionDrucken.triggered.connect(self.handlePrint)
        self.actionDruckansicht.triggered.connect(self.handlePreview)
        
    def loadGoogleMaps(self):
        try:
            url = QtCore.QUrl("https://www.google.de/maps/place//@%s,%s,20m/data=!3m1!1e3!4m2!3m1!1s0x0:0x0" % (self.imgheader["gps"]["latitude"],self.imgheader["gps"]["longitude"]))
            QtGui.QDesktopServices.openUrl(url)
        except:
            logger.error("loadGoogleMaps failed!")
            
    def handlePrint(self):
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.handlePaintRequest(dialog.printer())
        
    def handlePreview(self):
        dialog = QtPrintSupport.QPrintPreviewDialog()
        dialog.paintRequested.connect(self.handlePaintRequest)
        dialog.exec_()
    
    def setCurrentDir(self,imgdir):
        self.imgdir = imgdir
        
    def setCurrentImg(self,imgheader):
        self.imgheader = imgheader
    
    def handlePaintRequest(self, printer):
        painter = QtGui.QPainter()
        painter.begin(printer)
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        
        self.view.render(painter,painter.deviceTransform().map(QtCore.QPoint(0,45)))   #painter.deviceTransform().map(QtCore.QPoint(0,45))
        
        font = QtGui.QFont("times", 12)
        painter.setFont(font)
        fm = QtGui.QFontMetrics(font)
        text = "Flug: " + self.imgdir
        pixelsWidth = fm.width(text)
        pixelsHeight = fm.height()
        painter.drawText(20, 20, pixelsWidth, pixelsHeight, QtCore.Qt.AlignLeft, text)
        
        painter.end()
        
        
        #self.actionUAV_position.
        
    #def handlePan(self,toggle):
    #    self.view.panMap(self.view.lat,self.view.lon)
        
class Page(QtWebEngineWidgets.QWebEnginePage):
    ''' Settings for the browser.'''
    def userAgentForUrl(self, url):
        ''' Returns a User Agent that will be seen by the website. '''
        return "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
 
class Browser(QtWebEngineWidgets.QWebEngineView):
    _sizehint = None
    lat = 0
    lon = 0
    followUav = True
    jsloaded = False
    
    def __init__(self,settings):
    
        self.view = QtWebEngineWidgets.QWebEngineView.__init__(self)
        self.settings = settings
        self.setWindowTitle('Loading...')
        self.titleChanged.connect(self.adjustTitle)
        self.page = Page()
        self.setPage(self.page)
        path = "file:///"+PATHS["BASE"]+"/map_gl.html"
        path = path.replace("\\","/")
        self.load(path)
        self.loadFinished.connect(self._loadFinished)
        
    def setSizeHint(self, width, height):
        self._sizehint = QtCore.QSize(width, height)

    def sizeHint(self):
        #print('sizeHint:', self._sizehint)
        if self._sizehint is not None:
            return self._sizehint
        return super(Browser, self).sizeHint()

    def load(self,url):  
        self.setUrl(QtCore.QUrl(url)) 
   
    def _loadFinished(self):
        #pk.eyJ1IjoiZWFzeSIsImEiOiJjaXBqajhrcDYwMDVqdnJudHBpd3RlbHdhIn0.1l-xj2wHpfXg-Pi1oNKrCg
        mapboxtoken = self.settings.value("GEOVIEW/mapboxtoken")
        mapboxstyle = self.settings.value("GEOVIEW/mapboxstyle")
        self.page.runJavaScript("mapboxgl.accessToken ='{}'".format(mapboxtoken))
        line = "var map = new mapboxgl.Map({ container: 'map', style: "+"'{}', ".format(mapboxstyle)+"center: [11.0165, 48.1405],zoom: 18});"
        #print (line)
        self.page.runJavaScript(line)
        

        out = ""
        with open(os.path.join(PATHS["BASE"],"bla.js"),"r") as f:
            self.page.runJavaScript(f.read())
        self.jsloaded = True
        
        
    def adjustTitle(self):
        self.setWindowTitle(self.title())
 
    def disableJS(self):
        jsset = QtWebEngineWidgets.QWebEngineSettings.globalSettings()
        jsset.setAttribute(QtWebEngineWidgets.QWebEngineSettings.JavascriptEnabled, False)
 
    def setMarker(self,lat,lng):
        #print("geoview: setMarker")
        
        self.page.runJavaScript('var marker = new mapboxgl.Marker().setLngLat([{}, {}]).addTo(map);'.format(lng,lat))
        
    def clear(self):
        geojson = {"type": "Feature", "geometry": {"type": "LineString","coordinates": []}}
        #print ("CLEAR")
        self.page.runJavaScript('map.getSource("uavpath").setData({});'.format(geojson))
        #print("geoview: clear")
        #self.page.runJavaScript('map.removeLayer("uavpath");map.removeSource("uavpath");') #console.log(map.getSource("uav"))
        #self.page.runJavaScript('map.removeLayer("pois");map.removeSource("pois");') #console.log(map.getSource("uav"))
        #self.page.runJavaScript('marker.remove();')
        
    def loadpois(self,pois):
        if not self.jsloaded: return 
        #print("geoview: loadPois",pois)
        arr = []
        if pois==[] or pois == None:
            self.page.runJavaScript('map.getSource("pois").setData({{"type": "FeatureCollection","features": {} }})'.format(arr))
            return
        try:
            featureorig = {"type": "Feature","geometry": {"type": "Point","coordinates": []}, "properties": { "title": "", "icon": "zoo"}}
            for i in pois:
                lat, lon = i["lat"], i["lon"]
                name = i["name"]
                feature = copy.deepcopy(featureorig)
                feature["geometry"]["coordinates"] = [lon, lat]
                feature["properties"]["title"] = name
                arr.append(feature)
            self.page.runJavaScript('map.getSource("pois").setData({{"type": "FeatureCollection","features": {} }})'.format(arr))
        except:
            logger.error("geoview: loadpois failed", exc_info=True)
    
    def moveUav(self,lat,lon):
        if not self.jsloaded: return 
        self.lat, self.lon = lat, lon
        if self.followUav:
            self.panMap(lat,lon)
        geojson = {"type": "Feature",
                "geometry": {"type": "Point","coordinates": [lon, lat]},
                "properties": {"title": "UAV","icon": "drone"}}
        #print ("MOVEUAV")
        
        self.page.runJavaScript('map.getSource("uav").setData({});'.format(geojson))
        
    
    def fitBounds(self,bound):
        if not self.jsloaded: return 
        self.page.runJavaScript('map.fitBounds({});'.format(bound)) # bound = [[lng1,lat1],[lng2,lat2]]
    
    def followUavPosition(self,followUav):
        if followUav:
            self.panMap(self.lat,self.lon)
        self.followUav = followUav
        
    def panMap(self, lat, lng):
        if not self.jsloaded: return 
        self.page.runJavaScript('map.panTo([{},{}]);'.format(lng,lat)) #map.panTo(L.latLng({}, {}));
    
    
    def setUavPath(self,uavpath):
        if not self.jsloaded: return 
        P = np.array(uavpath)
        if len(P)==0: 
            return
        try:
            bound = [[P.T[0].min(),P.T[1].min()],[P.T[0].max(),P.T[1].max()]]
            self.fitBounds(bound)
        except:
            logger.warning("calculate boundary from uavpath failed")
            
        geojson = {"type": "Feature", "geometry": {"type": "LineString","coordinates": uavpath}}
        #print ("UAVPATH")
        self.page.runJavaScript('map.getSource("uavpath").setData({});'.format(geojson))
        
    
    def load_filedata(self,ara):     
        try:
            self.moveUav(ara["gps"].get("latitude",0),ara["gps"].get("longitude",0))
            self.panMap(ara["gps"].get("latitude",0),ara["gps"].get("longitude",0))
        except:
            logger.error("geoview load filedata failed")
            
    def setLayerVisible(self,layer,checked):
        if not self.jsloaded: return 
        #print("geoview: setLayervisible")
        self.page.runJavaScript('map.setLayoutProperty("{}", "visibility", "{}");'.format(layer,("visible" if checked==True  else "none")))
        
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = Browser()
    w.resize(400,200)
    load = QPushButton("setPOI",w)
    load.move(0,200)
    load.clicked.connect(lambda: w.setMarker( 48.1405,11.0165))
    
    load2 = QPushButton("pan",w)
    load2.move(100,200)
    load2.clicked.connect(lambda: w.panMap(48.1405,11.0165))
    
    rect = QPushButton("poligon",w)
    rect.move(200,200)
    rect.clicked.connect(lambda: w.setUavPath('test/uavpositions.gpx'))
    
    clear = QPushButton("clear",w)
    clear.move(300,200)
    clear.clicked.connect(w.clear)
    
    change = QPushButton("change",w)
    change.move(400,200)
    change.clicked.connect(lambda: w.setAllPois([{"name":"Kitz1","lat":48.140545,"lon":11.01625},{"name":"Kitz2","lat":48.14045,"lon":11.01625}]))
    
    change = QPushButton("move",w)
    change.move(500,200)
    change.clicked.connect(lambda: w.moveUav(48.123,11.123))
    
    w.resize(600, 250)
    w.move(300, 300)
    w.show()
    sys.exit(app.exec_())