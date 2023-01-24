from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtWidgets import QFileDialog,QMainWindow,QTableWidgetItem,QDialog
import os
import platform
import shutil
import logging
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType 
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from . import PATHS 
from . import CONF
from . import upload
from . import gpx


logger = logging.getLogger(__name__)

class GpxView(QMainWindow):
    def __init__(self,model):
        super().__init__()
        uic.loadUi(os.path.join(PATHS["UI"],'gpx.ui'),self)
        self.dialog = upload.UploadDialog("Upload")
        self.gpxdialog = GPXExportDialog()
        self.model = model
        self.actionGpxExport.triggered.connect(self.gpxdialog.show)
       # self.actionUpload.triggered.connect(lambda: self.dialog.openPropDialog(self.model))
        self.model.changed.connect(self.refresh)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tableWidget.setHorizontalHeaderLabels(["Name","Lat", "Lon"])
        self.gpxdialog.accepted.connect(self.exportgpx)
    
    def exportserial(self):
      #  print(PATHS["POIS"])
        cmd = CONF["GPX"]["gpsbabel"] + ' -w -r -t -i gpx,suppresswhite=0,logpoint=0,humminbirdextensions=0,garminextensions=0 -f "' + PATHS["POIS"] + '" -o garmin,snwhite=0,get_posn=0,power_off=0,erase_t=0,resettime=0 -F usb:'
       # print(cmd)
        ret = os.system(cmd)
        if ret == 0: 
            QtGui.QMessageBox.information(self, "Gps-Datenuebertragung ","Die GPS-Datenuebertragung war erfolgreich! Die Wegpunkte wurden ueber das Garmin-Serial/USB-Protokoll uebertragen"); 
        else:
            QtGui.QMessageBox.critical(self, "Gps-Datenuebertragung fehlgeschlagen!","Ein altes Garmin Geraet wurde nicht gefunden. Falls es ordnungsgemaess angeschlossen ist, koennte es sein, dass der Treiber noch nicht installiert ist. <a href='https://download.garmin.com/software/USBDrivers_2312.exe'>Garmin Serial Treiber herunterladen</a>. "); 
                
    def exportmassstorage(self):
        outdir = str(CONF["GPX"]["outpath"])
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
            
    def exportemail(self):
      #  print(PATHS["POIS"])
        senderEmail = str(CONF["GPX"]["emailsender"])
        empfangsEmail = str(CONF["GPX"]["emailreceiver"])
        msg = MIMEMultipart()
        msg['From'] = senderEmail
        msg['To'] = empfangsEmail
        msg['Subject'] = "POIs"
        emailText = "Pois sind hier"
        msg.attach(MIMEText(emailText, 'html'))
        server = smtplib.SMTP(str(CONF["GPX"]["smtpserver"]), str(CONF["GPX"]["smtpport"])) # Die Server Daten
        server.starttls()
        server.login(senderEmail, str(CONF["GPX"]["emailpassword"])) # Das Passwort
        text = msg.as_string()
        server.sendmail(senderEmail, empfangsEmail, text)
        server.quit()
      
    def exportgpx(self):
        if os.path.exists(PATHS["POIS"]):
            os.remove(PATHS["POIS"])
        self.gpxgen = gpx.GpxGenerator(PATHS["POIS"])
        try:
            for i in self.model.pois:
                self.gpxgen.add_wpt(str(i["lat"]),str(i["lon"]),str(i["ele"]),i["found_time"],str(i["name"]),"poi")
            self.gpxgen.save(PATHS["POIS"],False)
        except:
            logger.error("GPX_TO_GPS save failed",exc_info=True)
            
        if str(CONF["GPX"]["exportType"]) == "serial":# conf.garminserial_rB.isChecked():
            self.exportserial()
        elif  str(CONF["GPX"]["exportType"]) == "massStorage":# conf.massStorage_rB.isChecked():
            self.exportmassstorage()
        elif  str(CONF["GPX"]["exportType"]) == "email":# conf.massStorage_rB.isChecked():
            self.exportemail()
        elif  str(CONF["GPX"]["exportType"]) == "wildretter":# conf.massStorage_rB.isChecked():
            self.exportemail()
            
        else:
            QtGui.QMessageBox.critical(self, "Info2","kein export device typ gewaehlt "); 
    
    def refresh(self):
        self.tableWidget.setRowCount(len(self.model.pois))
        for k,i in enumerate(self.model.pois):
            self.tableWidget.setItem(k,0,QTableWidgetItem(i["name"]))
            self.tableWidget.setItem(k,1,QTableWidgetItem(str(i["lat"])))
            self.tableWidget.setItem(k,2,QTableWidgetItem(str(i["lon"])))
        self.tableWidget.resizeColumnsToContents()
        
class GPXExportDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        uic.loadUi(os.path.join(PATHS["UI"],'gpxexport.ui'),self)
        self.setWindowTitle("GPX Export")
        
        self.lineEdit.setText(CONF["GPX"]["outpath"])
        self.gpsbabelpath = CONF["GPX"]["gpsbabel"]
        self.exporttype = CONF["GPX"]["exportType"]
        self.emailLE.setText(CONF["GPX"]["email"])
        
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
        CONF["GPX"]["outpath"] = self.lineEdit.text()
        CONF["GPX"]["email"] = self.emailLE.text()
        if self.gpsbabelRB.isChecked():
            CONF["GPX"]["exportType"] = "serial"
        elif self.massstorageRB.isChecked():
            CONF["GPX"]["exportType"] = "massStorage"
        elif self.emailRB.isChecked():
            CONF["GPX"]["exportType"] = "email"
        elif self.wildretterRB.isChecked():
            CONF["GPX"]["exportType"] = "wildretter"
            QtGui.QMessageBox.critical(self, "Diese Auswahl geht noch nicht. Bitte vorerst noch den alten Upload nutzen (Wolken-Icon)"); 
            
        self.done(1)
        
    def reject(self):
        self.done(0)
        