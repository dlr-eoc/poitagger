import pkg_resources
import os
from shutil import copyfile,copytree
from PyQt5 import QtCore
from datetime import datetime
__version__ = "0.2.16"

PATHS = {}

#PATHS["CONF"] = "./conf.ini"
PATHS["USER"] = os.path.expanduser("~/poitagger/")

if not os.path.exists(PATHS["USER"]):
    os.mkdir(PATHS["USER"])
PATHS["USER_CALIB"] = os.path.join(PATHS["USER"], "calib")

PATHS["BASE"] = pkg_resources.resource_filename('poitagger', '')
    
if not os.path.exists(PATHS["USER_CALIB"]):
    os.mkdir(PATHS["USER_CALIB"])
if not os.path.exists(os.path.join(PATHS["USER_CALIB"],"Flir_Boson_320_6,3mm.json")):
    copyfile(os.path.join(PATHS["BASE"],"calib","Flir_Boson_320_6,3mm.json"),os.path.join(PATHS["USER_CALIB"],"Flir_Boson_320_6,3mm.json"))
if not os.path.exists(os.path.join(PATHS["USER_CALIB"],"Flir_Boson_640_14mm.json")):
    copyfile(os.path.join(PATHS["BASE"],"calib","Flir_Boson_640_14mm.json"),os.path.join(PATHS["USER_CALIB"],"Flir_Boson_640_14mm.json"))
if not os.path.exists(os.path.join(PATHS["USER_CALIB"],"Mavic2_Enterprise_Dual.json")):
    copyfile(os.path.join(PATHS["BASE"],"calib","Mavic2_Enterprise_Dual.json"),os.path.join(PATHS["USER_CALIB"],"Mavic2_Enterprise_Dual.json"))

PATHS["CONF"] = os.path.join(PATHS["USER"], "poitagger.ini")
PATHS["POIS"] = os.path.join(PATHS["USER"], "pois.gpx")

if not os.path.exists(PATHS["CONF"]):
    copyfile(pkg_resources.resource_filename('poitagger', 'conf.ini'), PATHS["CONF"])

settings = QtCore.QSettings(PATHS["CONF"], QtCore.QSettings.IniFormat)

if float(settings.value("INI/version",0)) < 1.1:
    print("INI-File veraltet")
    copyfile(os.path.join(PATHS["BASE"],"calib","Flir_Boson_640_14mm.json"),os.path.join(PATHS["USER_CALIB"],"Flir_Boson_640_14mm.json"))
    copyfile(os.path.join(PATHS["BASE"],"calib","Flir_Vue_640_19mm.json"),os.path.join(PATHS["USER_CALIB"],"Flir_Vue_640_19mm.json"))
    today = datetime.today().strftime('%Y-%m-%d')
    newfilename = os.path.join(os.path.dirname(PATHS["CONF"]),"poitagger_"+today+".ini")
    #print(newfilename)
    if os.path.exists(newfilename):
        os.unlink(newfilename)
    os.rename(PATHS["CONF"],newfilename)
    copyfile(pkg_resources.resource_filename('poitagger', 'conf.ini'), PATHS["CONF"])

print(PATHS["CONF"])
PATHS["UI"] = pkg_resources.resource_filename('poitagger', 'ui/')
PATHS["PROPERTIES"] = pkg_resources.resource_filename('poitagger', 'properties/')
PATHS["ICONS"] = pkg_resources.resource_filename('poitagger', 'ui/icons/')
PATHS["CALIB"] = pkg_resources.resource_filename('poitagger', 'calibsettings/')

