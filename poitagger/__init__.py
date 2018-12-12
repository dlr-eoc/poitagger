import pkg_resources

__version__ = "0.2.1"

PATHS = {}

PATHS["BASE"] = pkg_resources.resource_filename('poitagger', '')
PATHS["UI"] = pkg_resources.resource_filename('poitagger', 'ui/')
PATHS["PROPERTIES"] = pkg_resources.resource_filename('poitagger', 'properties/')
PATHS["ICONS"] = pkg_resources.resource_filename('poitagger', 'ui/icons/')
PATHS["CALIB"] = pkg_resources.resource_filename('poitagger', 'calibsettings/')

