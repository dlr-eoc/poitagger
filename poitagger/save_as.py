from PyQt5 import QtCore, QtGui, uic

import os
from . import PATHS

class SaveAsDialog(QtGui.QDialog):
    def __init__(self,parent=None):
        super(SaveAsDialog,self).__init__(parent)
        uic.loadUi(os.path.join(PATHS["UI"],'save_as.ui'),self)
        self.pathButton.clicked.connect(self.onSearch)
        self.setWindowTitle("SD-Karte einlesen")
        self.setModal(True)
    
    def st(self, workspace, projektName):
        self.pathBox.setText(workspace)
        self.nameBox.setText(projektName)
        
    def onSearch(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, "einen anderen Ordner waehlen", self.pathBox.text())
        if path == "":
            return
        else:
            self.pathBox.setText(path)
    
    # def accept(self):
        # print "Hallo"
        # super(SaveAsDialog, self).accept()
        
    # def reject(self):
        # super(SaveAsDialog, self).reject()
        