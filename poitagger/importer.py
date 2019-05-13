from PyQt5 import QtCore, QtGui, uic
import os
import time
import datetime
import logging
import sys
import PIL
import shutil
from dateutil import parser
#import pytz
#from tzlocal import get_localzone

from . import PATHS     
from . import image   

class CopyThread(QtCore.QThread):   
    log = QtCore.pyqtSignal(str)
    critical = QtCore.pyqtSignal(str)
    info = QtCore.pyqtSignal(str)
    progress = QtCore.pyqtSignal(int)
    
    outdirlist = []    
    eigeneConf = False
    def copy(self,indir,rootdir,flightname,nurFlugBilder,clearsdcard):
        self.indir = indir
        self.rootdir = rootdir
        self.flightname = flightname
        self.nurFlugBilder = nurFlugBilder
        self.clearsdcard = clearsdcard
        self.start()
    
    def is_flying(self,img):
        imag = image.Image.factory(img,True)
        try:
            if imag.header["gps"]["rel_altitude"]>5:
                return True
            else:
                return False
        except:
            logging.warning("there was no rel_altitude exif tag in the image header")
            return False
    
    def get_foldername(self,img):
        try:
            print(img.header["file"]["DateTimeOriginal"],img.header["file"]["name"])
            time = parser.parse(img.header["file"]["DateTimeOriginal"])
        except: 
            time = datetime.datetime.now()
            logging.warning("I didn't find a 'DateTimeOriginal'-Tag in Image Header, so i'll take the current time")
        foldername = time.strftime("%y%m%d_%H%M_")+self.flightname.replace(" ", "_") #.astimezone(get_localzone())
        outpath = os.path.join(self.rootdir,foldername)
        return outpath
        
    def create_folder(self,foldername): #and append (1) or (2) ... if it already exist
        index = ''
        while True:
            try:
                os.makedirs(foldername+index)
                return foldername+index
            except:
                if index:
                    index = '('+str(int(index[1:-1])+1)+')' # Append 1 to number in brackets
                else:
                    index = '(1)'
                pass # Go and try create file again
        
    def run(self):
        self.Flights = {}
        try:
            for root, dirs, files in sorted(os.walk(self.indir)):
                ImagesToCopy = []
                for f in files:
                    if not os.path.splitext(f)[1].lower() in image.SUPPORTED_EXTENSIONS: continue
                    if self.nurFlugBilder and not self.is_flying(os.path.join(root,f)): continue
                    ImagesToCopy.append(os.path.join(root,f))
                if len(files)==0: continue
                img = image.Image.factory(os.path.join(root,f),True)
                name = self.get_foldername(img)
                self.Flights[name]=ImagesToCopy.copy()
            
            for k,v in self.Flights.items():
                k_renamed = self.create_folder(k)
                for img in v:
                    shutil.copy2(img,k_renamed)
                
         #   prog += 1.0
         #   self.progress.emit(int(prog/foldersamount*100))
         #   if len(files)==0: continue
            if self.clearsdcard:
                for root, dirs, files in os.walk(self.indir):
                    for d in dirs:
                        shutil.rmtree(os.path.join(root, d))
                    for f in files:
                        os.remove(os.path.join(root, f))
            self.info.emit("Das Einlesen der SD-Karte war erfolgreich!") 
         
            
        except:
            (type, value, traceback) = sys.exc_info()
            sys.excepthook(type, value, traceback)
            self.critical.emit("SD-Karte einlesen fehlgeschlagen: %s "%value)
              
class SaveAsDialog(QtGui.QDialog):
    
    def __init__(self,parent=None):
        super().__init__(parent)
        self.settings = QtCore.QSettings(PATHS["CONF"], QtCore.QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False) 
        uic.loadUi(os.path.join(PATHS["UI"],'save_as.ui'),self)
        self.sourceTB.clicked.connect(self.onSearchSource)
        self.pathButton.clicked.connect(self.onSearch)
        self.setWindowTitle("Daten einlesen")
        self.setModal(True)
        self.worker = CopyThread()
        self.sourceLE.setText(self.settings.value('IMPORT/folder'))
        self.rootLE.setText(self.settings.value('PATHS/rootdir'))
        self.flightnameLE.setText(self.settings.value('IMPORT/flightname'))
        self.nurFlugBilder.setChecked(self.settings.value('IMPORT/nurFlugBilder',False,type=bool))
        self.SDCard_leeren.setChecked(self.settings.value('IMPORT/SDCard_leeren',False,type=bool))
     
    def connections(self):
        self.worker.critical.connect(lambda txt : QtGui.QMessageBox.critical(self, "SD-Karte einlesen",txt))
        self.worker.info.connect(lambda txt : QtGui.QMessageBox.information(self, "SD-Karte einlesen",txt))
        
    # def st(self, sdcard, workspace, projektName):
        # self.sourceLE.setText(sdcard)
        # self.pathBox.setText(workspace)
        # self.nameBox.setText(projektName)
        
    def onSearchSource(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, "einen anderen Ordner waehlen", self.sourceLE.text())
        if path != "": self.sourceLE.setText(path)
    
    def onSearch(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, "einen anderen Ordner waehlen", self.rootLE.text())
        if path != "": self.rootLE.setText(path)
    
    def accept(self):
        indir = str(self.sourceLE.text())
        self.settings.setValue('IMPORT/folder',indir)
        rootdir = str(self.rootLE.text())
        self.settings.setValue('PATH/rootdir',rootdir)
        flightname = str(self.flightnameLE.text())
        self.settings.setValue('IMPORT/flightname',flightname)
        nurFlugBilder = self.nurFlugBilder.isChecked()
        self.settings.setValue('IMPORT/nurFlugBilder',nurFlugBilder)
        clearsdcard = self.SDCard_leeren.isChecked()
        self.settings.setValue('IMPORT/SDCard_leeren',clearsdcard)
        self.worker.copy(indir, rootdir, flightname,nurFlugBilder,clearsdcard)
        self.hide()
    #def reject(self):
    #    super().reject()
        