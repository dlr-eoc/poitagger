import pkg_resources
import os
__version__ = "0.2.4"

PATHS = {}

PATHS["CONF"] = "./conf.ini"
if not os.path.exists(PATHS["CONF"]):
    PATHS["CONF"] = pkg_resources.resource_filename('poitagger', 'conf.ini')
PATHS["BASE"] = pkg_resources.resource_filename('poitagger', '')
PATHS["UI"] = pkg_resources.resource_filename('poitagger', 'ui/')
PATHS["PROPERTIES"] = pkg_resources.resource_filename('poitagger', 'properties/')
PATHS["ICONS"] = pkg_resources.resource_filename('poitagger', 'ui/icons/')
PATHS["CALIB"] = pkg_resources.resource_filename('poitagger', 'calibsettings/')

