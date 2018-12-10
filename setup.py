from cx_Freeze import setup, Executable
from setuptools import setup, find_packages
import sys, os

version = '0.2'


base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    'build_exe': {
        'includes': 'atexit'
    }
}

executables = [
    Executable('poitagger', base=base)
]


setup(name='poitagger',
      version=version,
      description="pyqt5 gui application for georeferencing drone based images",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='uav drone thermal flir georeferencing computer vision localization gps exif pyqt5 qt image tagging geo gps',
      author='Martin Israel',
      author_email='martin.israel@dlr.de',
      url='',
      license='GNU GPL 3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      options=options,
      executables=executables,
      entry_points={
        'console_scripts': [
            'app1 = poitagger:main',
        ],
    },
      )

