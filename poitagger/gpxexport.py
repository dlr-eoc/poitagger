from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtWidgets import QFileDialog,QMainWindow,QTableWidgetItem
import os
import platform
import shutil
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType 
from . import PATHS 
from . import upload
from . import gpx

class GpxView(QMainWindow):
    def __init__(self,settings,model):
        super().__init__()
        uic.loadUi(os.path.join(PATHS["UI"],'gpx.ui'),self)
        self.dialog = upload.UploadDialog("Upload")
        self.gpxdialog = GPXExportDialog()
        self.settings = settings
        self.model = model
        self.actionGpxExport.triggered.connect(self.gpxdialog.show)
        self.actionUpload.triggered.connect(lambda: self.dialog.openPropDialog(self.model))
        self.model.changed.connect(self.refresh)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tableWidget.setHorizontalHeaderLabels(["Name","Lat", "Lon"])
        self.gpxdialog.accepted.connect(self.exportgpx)
    
    def exportserial(self):
        cmd = self.settings.value('GPX/gpsbabel') + ' -w -r -t -i gpx,suppresswhite=0,logpoint=0,humminbirdextensions=0,garminextensions=0 -f "' + PATHS["POIS"] + '" -o garmin,snwhite=0,get_posn=0,power_off=0,erase_t=0,resettime=0 -F usb:'
        print(cmd)
        ret = os.system(cmd)
        if ret == 0: 
            QtGui.QMessageBox.information(self, "Gps-Datenuebertragung ","Die GPS-Datenuebertragung war erfolgreich! Die Wegpunkte wurden ueber das Garmin-Serial/USB-Protokoll uebertragen"); 
        else:
            QtGui.QMessageBox.critical(self, "Gps-Datenuebertragung fehlgeschlagen!","ein altes Garmin Geraet wurde nicht gefunden (bei einem neueren GPS-Geraet muss unter Einstellungen/allgemein/GPS-Device MassStorage Device anstatt Garmin Serial/USB ausgewaehlt werden)!"); 
                
    def exportmassstorage(self):
        outdir = str(self.settings.value('GPX/outpath'))
        if os.path.isdir(outdir):
            gpxfilename = "pois.gpx"
            outpath = os.path.join(outdir,gpxfilename)
            os_ver = platform.version().split(".")
            if os_ver[0]=="10":
                os.system('copy "' + PATHS["POIS"].replace("/",os.sep) + '" "' + outpath.replace("/",os.sep) + '" ')
            else:
                shutil.copyfile(PATHS["POIS"], outpath)
            QtGui.QMessageBox.information(self, "Gps-Datenuebertragung ","Die GPS-Datenuebertragung war erfolgreich! Die Wegpunkte wurden hierher kopiert: %s "%outpath); 
        else:
            QtGui.QMessageBox.critical(self, "Gps-Datenuebertragung fehlgeschlagen!","GPS-Geraet nicht gefunden (Das angegebene Verzeichnis %s existiert nicht)!"%outdir); 
            
    def exportgpx(self):
        if os.path.exists(PATHS["POIS"]):
            os.remove(PATHS["POIS"])
        self.gpxgen = gpx.GpxGenerator(PATHS["POIS"])
        try:
            for i in self.model.pois:
                self.gpxgen.add_wpt(str(i["lat"]),str(i["lon"]),str(i["ele"]),i["found_time"],str(i["name"]),"poi")
            self.gpxgen.save(PATHS["POIS"],False)
        except:
            logging.error("GPS_TO_GPS save failed",exc_info=True)
            
        if str(self.settings.value('GPX/exportType')) == "serial":# conf.garminserial_rB.isChecked():
            self.exportserial()
        elif  str(self.settings.value('GPX/exportType')) == "massStorage":# conf.massStorage_rB.isChecked():
            self.exportmassstorage()
        else:
            QtGui.QMessageBox.critical(self, "Info2","kein export device typ gewaehlt "); 
    
    def refresh(self):
        self.tableWidget.setRowCount(len(self.model.pois))
        for k,i in enumerate(self.model.pois):
            self.tableWidget.setItem(k,0,QTableWidgetItem(i["name"]))
            self.tableWidget.setItem(k,1,QTableWidgetItem(str(i["lat"])))
            self.tableWidget.setItem(k,2,QTableWidgetItem(str(i["lon"])))
        self.tableWidget.resizeColumnsToContents()
        
class GPXExportDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        uic.loadUi(os.path.join(PATHS["UI"],'gpxexport.ui'),self)
        self.setWindowTitle("GPX Export")
        
        self.settings = QtCore.QSettings(PATHS["CONF"], QtCore.QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False) 
        self.lineEdit.setText(self.settings.value("GPX/outpath",""))
        self.gpsbabelpath = self.settings.value("GPX/gpsbabel","")
        self.exporttype = self.settings.value('GPX/exportType')
        self.emailLE.setText(self.settings.value('GPX/email'))
        
        if str(self.exporttype) == "serial":
            self.gpsbabelRB.setChecked(True)
        elif str(self.exporttype) == "massStorage":
            self.massstorageRB.setChecked(True)   
        elif str(self.exporttype) == "email":
            self.emailRB.setChecked(True)   
        elif str(self.exporttype) == "wildretter":
            self.wildretterRB.setChecked(True)   
        
        self.connections()
        self.setModal(True)
        
    def connections(self):
        self.toolButton.clicked.connect(self.ChoosePath)
        
    def ChoosePath(self,x):
        self.lineEdit.setText(QFileDialog.getExistingDirectory(self, "Select Directory",self.lineEdit.text()))
        
    def accept(self):
        self.settings.setValue("GPX/outpath",self.lineEdit.text())
        self.settings.setValue('GPX/email',self.emailLE.text())
        if self.gpsbabelRB.isChecked():
            self.settings.setValue('GPX/exportType',"serial")
        elif self.massstorageRB.isChecked():
            self.settings.setValue('GPX/exportType',"massStorage")
        elif self.emailRB.isChecked():
            self.settings.setValue('GPX/exportType',"email")
        elif self.wildretterRB.isChecked():
            self.settings.setValue('GPX/exportType',"wildretter")
        self.done(1)
        
    def reject(self):
        self.done(0)
        