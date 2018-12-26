from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import matplotlib.image as mpimg
import numpy as np
import PIL
# Load image from disk and reorient it for viewing
fname = 'kitten.jpg' # This can be any photo image file
photo =  np.asarray(PIL.Image.open(fname))
#photo=mpimg.imread(fname)
photo = photo.transpose([1,0,2])


# Create app

app = QtGui.QApplication([])



## Create window with ImageView widget

win = QtGui.QMainWindow()
win.resize(1200,800)
imv = pg.ImageView()
win.setCentralWidget(imv)
win.show()
win.setWindowTitle(fname)


## Display the data
imv.setImage(photo)

## Start Qt event loop unless running in interactive mode.

if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()