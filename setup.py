from setuptools import setup, find_packages
import sys, os, codecs, re

here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(name='poitagger',
      version=find_version("poitagger", "__init__.py"),
      description="pyqt5 gui application for georeferencing drone based images",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='uav drone thermal flir georeferencing computer vision localization gps exif pyqt5 qt image tagging geo gps',
      author='Martin Israel',
      author_email='martin.israel@dlr.de',
      url='',
      license='GNU GPL 3',
      packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'docopt',
        'setuptools',
        'PyQt5',
        'numpy',
        'lxml',
        'pyqtgraph>=0.11',
        'tifffile',
        'utm',
        'pytz',
        'bs4',
        'python-dateutil',
        'pyyaml',
        'yamlordereddictloader',
        'requests',
        'requests_cache',
        'simplejson',
        'exifread',
        'Pillow'
      ],
      dependency_links = [
        'https://github.com/pyqtgraph/pyqtgraph/archive/develop.zip'
      ],
      package_data={
            '': ['*.js','*.html','*.css','*.ui','ui/*.*','ui/icons/*.*','*.ini'],
      },
      entry_points={
        'gui_scripts':  ["poitagger = poitagger.__main__:main"],
    },
      )

