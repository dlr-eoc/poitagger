import pkg_resources
import os
from shutil import copyfile

__version__ = "0.2.8"

PATHS = {}

#PATHS["CONF"] = "./conf.ini"
PATHS["USER"] = os.path.expanduser("~/poitagger/")

if not os.path.exists(PATHS["USER"]):
    os.mkdir(PATHS["USER"])
PATHS["USER_CALIB"] = os.path.join(PATHS["USER"], "calib")
    
if not os.path.exists(PATHS["USER_CALIB"]):
    os.mkdir(PATHS["USER_CALIB"])

PATHS["CONF"] = os.path.join(PATHS["USER"], "poitagger.ini")
PATHS["POIS"] = os.path.join(PATHS["USER"], "pois.gpx")

if not os.path.exists(PATHS["CONF"]):
    copyfile(pkg_resources.resource_filename('poitagger', 'conf.ini'), PATHS["CONF"])
print(PATHS["CONF"])
PATHS["BASE"] = pkg_resources.resource_filename('poitagger', '')
PATHS["UI"] = pkg_resources.resource_filename('poitagger', 'ui/')
PATHS["PROPERTIES"] = pkg_resources.resource_filename('poitagger', 'properties/')
PATHS["ICONS"] = pkg_resources.resource_filename('poitagger', 'ui/icons/')
PATHS["CALIB"] = pkg_resources.resource_filename('poitagger', 'calibsettings/')

