import yaml
import yamlordereddictloader
import os
import ast
from lxml import etree
import logging
from PyQt5 import QtCore,QtGui,uic, QtWidgets
from PyQt5.QtWidgets import QApplication,QWidget,QMainWindow, QLineEdit,QToolButton,QAction,QMessageBox,QPushButton,QVBoxLayout
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType 
import datetime
from collections import OrderedDict,MutableMapping,MutableSequence

from . import image
from . import utils2
from . import flightmeta
from . import nested
from . import PATHS

    
class PoisWidget(QMainWindow):
    def __init__(self,parent = None):
        super(PoisWidget, self).__init__(parent)
        uic.loadUi(os.path.join(PATHS["UI"],'pois.ui'),self)
        self.setWindowFlags(QtCore.Qt.Widget)
        self.t = ParameterTree(showHeader=False)
        self.horizontalLayout.addWidget(self.t)
        
    def setMeta(self,fmpois):
        self.p = fmpois
        self.t.setParameters(self.p, showTop=False)
        self.actionNeuerMarker.triggered.connect(lambda : self.addPoi("{'name':'xxx','type':'kitz','x':245,'y':123}"))
        #self.actionimport.toggled.connect(self.flight.enableImport)
        #self.actionsave.triggered.connect(self.flight.save)
        #self.actionreload.triggered.connect(self.flight.load)
    
    
    def addPoi(self,value):
        last = len(self.p.children())
        self.p.insertChild(last,{"name":str(last),"value":value,"type":"str", "readonly":False,"removable":True,"renamable":True})

    def delParameter(self):
        c = self.t.currentItem().param
        reply = QMessageBox.question(self, "Parameter loeschen?","Soll der Parameter '{}'  tatsaechlich geloescht werden?".format(c.name()),QMessageBox.Yes,QMessageBox.No) 
        if reply == QMessageBox.Yes:
            c.remove()

        
        
        
if __name__ == "__main__":
    
    import sys
    app = QApplication(sys.argv)
    path = "D:/WILDRETTER-DATEN/2017_DLR/2017-04-05_14-56_Hausen"
    
    
    win = PoisWidget()
    
    fm = flightmeta.Flight()
    fm.load(path)
    win.setMeta(fm.p.child("pois"))    
    
    vbox = QVBoxLayout()
    win.horizontalLayout.addLayout(vbox)
    but = QPushButton()
    but.setText("change")
    vbox.addWidget(but)
    but.clicked.connect(fm.change)
    
    but2 = QPushButton()
    but2.setText("save")
    vbox.addWidget(but2)
    #but2.clicked.connect(win.save)
    
    but3 = QPushButton()
    but3.setText("add Param")
    vbox.addWidget(but3)
    but3.clicked.connect(lambda: win.addPoi("{'name':'blabla','id':'46'}"))
    
    but4 = QPushButton()
    but4.setText("del Param")
    vbox.addWidget(but4)
    but4.clicked.connect(win.delParameter)
    
    
    but5 = QPushButton()
    but5.setText("saveState")
    vbox.addWidget(but5)
    but5.clicked.connect(win.saveState)
    
    #root.editingFinished.connect(lambda: fm.load(str(root.text())))
    win.show()
    
    # Escape by Key
    win.escAction = QAction('escape', win)
    win.escAction.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Escape))
    win.addAction(win.escAction)
    win.escAction.triggered.connect(win.close)
   
   
    sys.exit(app.exec_())

    