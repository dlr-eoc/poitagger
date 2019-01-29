from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication,QFileSystemModel, QTreeView, QFileIconProvider

import sys, os
#import icons_rc
from . import image
from . import PATHS
rootdir = "D:/WILDRETTER-DATEN"

class TreeModel(QFileSystemModel):
    def __init__(self, parent = None):
        super(TreeModel, self).__init__(parent)
        self.loadpixmaps()
        self.metafilename = "flightmeta.yml"
        self.poifiles = []
        
    def loadpixmaps(self):
        self.foldericon = QFileIconProvider().icon(QFileIconProvider.Folder).pixmap(16,16)
        #self.foldernotok = QtGui.QPixmap(os.path.join(PATHS["ICONS"],"file-poi.png"))
        self.fileicon = QtGui.QPixmap(os.path.join(PATHS["ICONS"],"file-empty.png"))
        self.filepoi = QtGui.QPixmap(os.path.join(PATHS["ICONS"],"file-poi.png"))
        self.folderok = QtGui.QPixmap(os.path.join(PATHS["ICONS"],"folder_ok.png"))
        self.foldernotok = QtGui.QPixmap(os.path.join(PATHS["ICONS"],"folder!.png"))
        #self.fileicon = self.foldernotok
        #self.filepoi = self.foldernotok
        #self.folderok = self.foldernotok
    def columnCount(self, parent):
        return 1
        
    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if section == 0:
                return self.rootPath()
        
    def pois(self,poilist):
        self.poifiles = poilist
        self.layoutChanged.emit()
        
    def data(self, index, role):
        dataoutput = super(TreeModel, self).data(index, role)
       # fname = self.fileName(index)
       # fpath = self.filePath(index)
        fileInfo = QtCore.QFileInfo(self.filePath(index))
        base, ext = os.path.splitext(self.filePath(index))
        if (role == QtCore.Qt.DecorationRole and index.column() == 0):
            if fileInfo.isDir():
                if os.path.exists(os.path.join(self.filePath(index),self.metafilename)):
                    return self.folderok 
                else:
                    return self.foldericon     
            else:
                if self.fileName(index) in self.poifiles:
                    return self.filepoi
        #        if ext.lower() in [".ara",".raw",".ar2"]:
        #            return self.fileicon
        #        elif ext.lower() in [".tif",".tiff"]:
        #            return self.fileicon
        #        elif ext.lower() in [".jpg",".jpeg"]:
        #            return self.filepoi
                else:
                    return self.fileicon
                        
        elif(role == QtCore.Qt.DisplayRole and index.column() == 0):      
            return os.path.split(self.filePath(index))[1]
        else:
            return dataoutput
            
    
        
        
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    app.setStyle("plastique")
    
    model = TreeModel() 
    model.setRootPath( rootdir )
    treeView = QTreeView()
    treeView.show()
    treeView.setModel(model)
    treeView.setRootIndex(model.index(rootdir ))
    
    sys.exit(app.exec_())