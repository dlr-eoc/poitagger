# poitagger
A georeferencing application for drone based images 

Maintainer
----------
  * Martin Israel <martin.israel@dlr.de>
  
Requirements
------------


  * python >= 3.4  (tested with python 3.6 and 3.7)
  * NumPy
  * PyQt5
  * pyqtgraph

and some smaller scripts available with pip         


Installation
------------
Get the requirements:
    `$ pip install -r requirements.txt`
   
To install system-wide from source distribution:
   `$ python setup.py install`

For Windows you can create a standalone version with python-embedded-launcher
   `$ pip install python-embedded-launcher`
   `$ python setup.py bdist_launcher`

Start
-----

this application is now installed as a module. That's why you have to start it with '-m'
    `$ python -m poitagger`
    
    
Documentation
-------------

* Documentation is still very thin. But it will grow
* If you acquired this code via GitHub, then you can build the documentation using sphinx.
      From the documentation directory, run:
          `$ make html`
   

   

