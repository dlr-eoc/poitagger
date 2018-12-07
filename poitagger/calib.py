from PyQt5 import QtCore,QtGui,uic
from PyQt5.QtWidgets import QApplication,QWidget,QMainWindow,QFileDialog
import os
import logging
import image
class Calib(QtGui.QMainWindow):
    log = QtCore.pyqtSignal(str)
    conf =  QtCore.pyqtSignal(QtCore.QSettings) 
    def __init__(self):
        QtGui.QWidget.__init__(self)
        uic.loadUi('ui/calib2.ui',self)
        
        self.actionGroupTools = QtGui.QActionGroup(self)
        self.actionGroupTools.addAction(self.actionGeometrisch)
        self.actionGroupTools.addAction(self.actionRadiometrisch)
        self.actionGroupTools.addAction(self.actionBoresight)
        
        self.actionGroupTools.triggered.connect(self.focusDockWidget)
        
        self.actionGeometrisch.setChecked(True)
        self.actionAusDatei.triggered.connect(self.ausDatei)
        #self.actionAusDatei.triggered.connect(self.ausDatei)
        self.actionAra_berschreiben_mit_eigenen_Werten.triggered.connect(self.sendSettings)
        calibfile = "default.ini"
        calibpath = os.path.join("calibsettings",calibfile)
        self.settings = QtCore.QSettings(calibpath, QtCore.QSettings.IniFormat)
        self.calibFile.setText(calibfile)
        self.LoadButton.clicked.connect(self.pathChooser)
    
    def pathChooser(self):
            dlgret = QFileDialog.getOpenFileName(self, "Select Calibration File","calibsettings", "Calibration Files (*.ini)")
            calibpath = dlgret[0]
            calibfile = os.path.basename(calibpath)
            self.calibFile.setText(calibfile)
            self.settings = QtCore.QSettings(calibpath, QtCore.QSettings.IniFormat)
            self.ausConfDatei()
            
    def focusDockWidget(self,action):
        if action == self.actionGeometrisch:
            self.label.setText("geometrische Kalibrierung")
            self.stackedWidget.setCurrentIndex(0)
        if action == self.actionRadiometrisch:
            self.label.setText("radiometrische Kalibrierung")
            self.stackedWidget.setCurrentIndex(1)
        if action == self.actionBoresight:
            self.label.setText("Boresight Winkel")
            self.stackedWidget.setCurrentIndex(2)
            
    def load_data(self,ara):    
        try:
            self.dlr_cam_pitch_offset.setValue(ara["calibration"]["boresight"].get("cam_pitch_offset",0))
            self.dlr_cam_roll_offset.setValue(ara["calibration"]["boresight"].get("cam_roll_offset",0))
            self.dlr_cam_yaw_offset.setValue(ara["calibration"]["boresight"].get("cam_yaw_offset",0))
            self.dlr_boresight_ts.setText(str(ara["calibration"]["boresight"].get("timestamp","")))
            self.dlr_boresight_flipped_hor.setChecked(ara["calibration"].get("flags",0) & image.FLAGS.FLIPPED_HOR)#flags_flipped_hor
            self.dlr_boresight_flipped_ver.setChecked(ara["calibration"].get("flags",0) & image.FLAGS.FLIPPED_VER)
                
            self.dlr_radiom_B.setValue(ara["calibration"]["radiometric"].get("B",0))
            self.dlr_radiom_R.setValue(ara["calibration"]["radiometric"].get("R",0))
            self.dlr_radiom_F.setValue(ara["calibration"]["radiometric"].get("F",0))
            self.dlr_radiom_ts.setText(str(ara["calibration"]["radiometric"].get("timestamp","")))
            
            self.dlr_geom_fx.setValue(ara["calibration"]["geometric"].get("fx",0))
            self.dlr_geom_fy.setValue(ara["calibration"]["geometric"].get("fy",0))
            self.dlr_geom_cx.setValue(ara["calibration"]["geometric"].get("cx",ara["image"]["width"]/2))
            self.dlr_geom_cy.setValue(ara["calibration"]["geometric"].get("cy",ara["image"]["height"]/2))
            self.dlr_geom_skew.setValue(ara["calibration"]["geometric"].get("skew",0))
            self.dlr_geom_k1.setValue(ara["calibration"]["geometric"].get("k1",0))
            self.dlr_geom_k2.setValue(ara["calibration"]["geometric"].get("k2",0))
            self.dlr_geom_k3.setValue(ara["calibration"]["geometric"].get("k3",0))
            self.dlr_geom_p1.setValue(ara["calibration"]["geometric"].get("p1",0))
            self.dlr_geom_p2.setValue(ara["calibration"]["geometric"].get("p2",0))
            self.dlr_geom_ts.setText(str(ara["calibration"]["geometric"].get("timestamp","")))
           # print dir(ara)
           # print "Ver",ara.__version__
            self.dlr_geom_pixelshift_x.setValue(ara["camera"].get("pixelshift_x",17e-6))   #does not yet work!
            self.dlr_geom_pixelshift_y.setValue(ara["camera"].get("pixelshift_y",17e-6)) #does not yet work!
        except:
            logging.error("calib load data faild",exc_info=True)
    
    def ausDatei(self):
        s = self.getSettings(True)
        self.dlr_cam_roll_offset_2.setValue(s.value("BORESIGHT_CALIBRATION/rolldiff"))
        self.dlr_cam_pitch_offset_2.setValue(s.value("BORESIGHT_CALIBRATION/pitchdiff"))
        self.dlr_cam_yaw_offset_2.setValue(s.value("BORESIGHT_CALIBRATION/yawdiff"))
        self.dlr_boresight_ts_2.setText(   s.value("BORESIGHT_CALIBRATION/date"))
        self.dlr_boresight_flipped_hor_2.setChecked(   s.value("BORESIGHT_CALIBRATION/flipped_hor"))
        self.dlr_boresight_flipped_ver_2.setChecked(   s.value("BORESIGHT_CALIBRATION/flipped_ver"))
        self.dlr_radiom_B_2.setValue(      s.value("RADIOMETRIC_CALIBRATION/B"))
        self.dlr_radiom_R_2.setValue(      s.value("RADIOMETRIC_CALIBRATION/R"))
        self.dlr_radiom_F_2.setValue(      s.value("RADIOMETRIC_CALIBRATION/F"))
        self.dlr_radiom_ts_2.setText(      s.value("RADIOMETRIC_CALIBRATION/date"))
        self.dlr_geom_fx_2.setValue(       s.value("GEOMETRIC_CALIBRATION/fx" ))
        self.dlr_geom_fy_2.setValue(       s.value("GEOMETRIC_CALIBRATION/fy" ))
        self.dlr_geom_cx_2.setValue(       s.value("GEOMETRIC_CALIBRATION/cx" ))
        self.dlr_geom_cy_2.setValue(       s.value("GEOMETRIC_CALIBRATION/cy" ))
        self.dlr_geom_skew_2.setValue(     s.value("GEOMETRIC_CALIBRATION/skew"))
        self.dlr_geom_k1_2.setValue(       s.value("GEOMETRIC_CALIBRATION/k1"))
        self.dlr_geom_k2_2.setValue(       s.value("GEOMETRIC_CALIBRATION/k2"))
        self.dlr_geom_k3_2.setValue(       s.value("GEOMETRIC_CALIBRATION/k3"))
        self.dlr_geom_p1_2.setValue(       s.value("GEOMETRIC_CALIBRATION/p1"))
        self.dlr_geom_p2_2.setValue(       s.value("GEOMETRIC_CALIBRATION/p2"))
        self.dlr_geom_ts_2.setText(        s.value("GEOMETRIC_CALIBRATION/date"))
        self.dlr_geom_pixelshift_x_2.setValue(       s.value("GEOMETRIC_CALIBRATION/pixelshift_x")) #does not yet work!
        self.dlr_geom_pixelshift_y_2.setValue(       s.value("GEOMETRIC_CALIBRATION/pixelshift_y")) #does not yet work!
            
    def ausConfDatei(self):
        s = self.settings
        self.dlr_cam_roll_offset_2.setValue(float(s.value("BORESIGHT_CALIBRATION/rolldiff")))
        self.dlr_cam_pitch_offset_2.setValue(float(s.value("BORESIGHT_CALIBRATION/pitchdiff")))
        self.dlr_cam_yaw_offset_2.setValue(float(s.value("BORESIGHT_CALIBRATION/yawdiff")))
        self.dlr_boresight_ts_2.setText(   s.value("BORESIGHT_CALIBRATION/date"))
        self.dlr_boresight_flipped_hor_2.setChecked(   bool(s.value("BORESIGHT_CALIBRATION/flipped_hor")))
        self.dlr_boresight_flipped_ver_2.setChecked(   bool(s.value("BORESIGHT_CALIBRATION/flipped_ver")))
        self.dlr_radiom_B_2.setValue(      float(s.value("RADIOMETRIC_CALIBRATION/B"))    )
        self.dlr_radiom_R_2.setValue(      float(s.value("RADIOMETRIC_CALIBRATION/R"))    )
        self.dlr_radiom_F_2.setValue(      float(s.value("RADIOMETRIC_CALIBRATION/F"))    )
        self.dlr_radiom_ts_2.setText(      s.value("RADIOMETRIC_CALIBRATION/date")) 
        self.dlr_geom_fx_2.setValue(       float(s.value("GEOMETRIC_CALIBRATION/fx" ))    )
        self.dlr_geom_fy_2.setValue(       float(s.value("GEOMETRIC_CALIBRATION/fy" ))    )
        self.dlr_geom_cx_2.setValue(       float(s.value("GEOMETRIC_CALIBRATION/cx" ))    )
        self.dlr_geom_cy_2.setValue(       float(s.value("GEOMETRIC_CALIBRATION/cy" ))    )
        self.dlr_geom_skew_2.setValue(     float(s.value("GEOMETRIC_CALIBRATION/skew"))   )
        self.dlr_geom_k1_2.setValue(       float(s.value("GEOMETRIC_CALIBRATION/k1"))     )
        self.dlr_geom_k2_2.setValue(       float(s.value("GEOMETRIC_CALIBRATION/k2"))     )
        self.dlr_geom_k3_2.setValue(       float(s.value("GEOMETRIC_CALIBRATION/k3"))     )
        self.dlr_geom_p1_2.setValue(       float(s.value("GEOMETRIC_CALIBRATION/p1"))     )
        self.dlr_geom_p2_2.setValue(       float(s.value("GEOMETRIC_CALIBRATION/p2"))     )
        self.dlr_geom_ts_2.setText(        s.value("GEOMETRIC_CALIBRATION/date")   )
        self.dlr_geom_pixelshift_x_2.setValue(      int( s.value("GEOMETRIC_CALIBRATION/pixelshift_x"))) #does not yet work!
        self.dlr_geom_pixelshift_y_2.setValue(      int( s.value("GEOMETRIC_CALIBRATION/pixelshift_y"))) #does not yet work!
        
        
        
    def sendSettings(self):
        self.getSettings(False)
        self.conf.emit(self.settings)
        
    def getSettings(self, fromRaw=True):
        if fromRaw:
            self.settings.setValue("BORESIGHT_CALIBRATION/rolldiff", self.dlr_cam_roll_offset.value())
            self.settings.setValue("BORESIGHT_CALIBRATION/pitchdiff",self.dlr_cam_pitch_offset.value())
            self.settings.setValue("BORESIGHT_CALIBRATION/yawdiff",  self.dlr_cam_yaw_offset.value())
            self.settings.setValue("BORESIGHT_CALIBRATION/date",     self.dlr_boresight_ts.text())
            self.settings.setValue("BORESIGHT_CALIBRATION/flipped_hor", self.dlr_boresight_flipped_hor.isChecked())
            self.settings.setValue("BORESIGHT_CALIBRATION/flipped_ver", self.dlr_boresight_flipped_ver.isChecked())
            self.settings.setValue("RADIOMETRIC_CALIBRATION/B",      self.dlr_radiom_B.value())
            self.settings.setValue("RADIOMETRIC_CALIBRATION/R",      self.dlr_radiom_R.value())
            self.settings.setValue("RADIOMETRIC_CALIBRATION/F",      self.dlr_radiom_F.value())
            self.settings.setValue("RADIOMETRIC_CALIBRATION/date",   self.dlr_radiom_ts.text())
            self.settings.setValue("GEOMETRIC_CALIBRATION/fx",       self.dlr_geom_fx.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/fy",       self.dlr_geom_fy.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/cx",       self.dlr_geom_cx.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/cy",       self.dlr_geom_cy.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/skew",     self.dlr_geom_skew.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/k1",       self.dlr_geom_k1.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/k2",       self.dlr_geom_k2.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/k3",       self.dlr_geom_k3.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/p1",       self.dlr_geom_p1.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/p2",       self.dlr_geom_p2.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/pixelshift_x", self.dlr_geom_pixelshift_x.value()) #does not yet work!
            self.settings.setValue("GEOMETRIC_CALIBRATION/pixelshift_y", self.dlr_geom_pixelshift_y.value()) #does not yet work!
            self.settings.setValue("GEOMETRIC_CALIBRATION/date",     self.dlr_geom_ts.text())
            
        else:    
            self.settings.setValue("BORESIGHT_CALIBRATION/rolldiff", self.dlr_cam_roll_offset_2.value())
            self.settings.setValue("BORESIGHT_CALIBRATION/pitchdiff",self.dlr_cam_pitch_offset_2.value())
            self.settings.setValue("BORESIGHT_CALIBRATION/yawdiff",  self.dlr_cam_yaw_offset_2.value())
            self.settings.setValue("BORESIGHT_CALIBRATION/date",     self.dlr_boresight_ts_2.text())
            self.settings.setValue("BORESIGHT_CALIBRATION/flipped_hor", self.dlr_boresight_flipped_hor_2.isChecked())
            self.settings.setValue("BORESIGHT_CALIBRATION/flipped_ver", self.dlr_boresight_flipped_ver_2.isChecked())
            self.settings.setValue("RADIOMETRIC_CALIBRATION/B",      self.dlr_radiom_B_2.value())
            self.settings.setValue("RADIOMETRIC_CALIBRATION/R",      self.dlr_radiom_R_2.value())
            self.settings.setValue("RADIOMETRIC_CALIBRATION/F",      self.dlr_radiom_F_2.value())
            self.settings.setValue("RADIOMETRIC_CALIBRATION/date",   self.dlr_radiom_ts_2.text())
            self.settings.setValue("GEOMETRIC_CALIBRATION/fx",       self.dlr_geom_fx_2.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/fy",       self.dlr_geom_fy_2.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/cx",       self.dlr_geom_cx_2.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/cy",       self.dlr_geom_cy_2.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/skew",     self.dlr_geom_skew_2.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/k1",       self.dlr_geom_k1_2.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/k2",       self.dlr_geom_k2_2.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/k3",       self.dlr_geom_k3_2.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/p1",       self.dlr_geom_p1_2.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/p2",       self.dlr_geom_p2_2.value())
            self.settings.setValue("GEOMETRIC_CALIBRATION/pixelshift_x", self.dlr_geom_pixelshift_x_2.value()) #does not yet work!
            self.settings.setValue("GEOMETRIC_CALIBRATION/pixelshift_y", self.dlr_geom_pixelshift_y_2.value()) #does not yet work!
            self.settings.setValue("GEOMETRIC_CALIBRATION/date",     self.dlr_geom_ts_2.text())
        return self.settings