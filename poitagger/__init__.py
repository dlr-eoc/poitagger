import pkg_resources
import os
from shutil import copyfile

__version__ = "0.2.4"

PATHS = {}

#PATHS["CONF"] = "./conf.ini"
PATHS["CONF"] = os.path.expanduser("~/poitagger.ini")
if not os.path.exists(PATHS["CONF"]):
    copyfile(pkg_resources.resource_filename('poitagger', 'conf.ini'), PATHS["CONF"])
#print(PATHS["CONF"])
PATHS["BASE"] = pkg_resources.resource_filename('poitagger', '')
PATHS["UI"] = pkg_resources.resource_filename('poitagger', 'ui/')
PATHS["PROPERTIES"] = pkg_resources.resource_filename('poitagger', 'properties/')
PATHS["ICONS"] = pkg_resources.resource_filename('poitagger', 'ui/icons/')
PATHS["CALIB"] = pkg_resources.resource_filename('poitagger', 'calibsettings/')

