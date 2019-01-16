from PyQt5 import QtCore,QtGui,uic, QtWidgets
from PyQt5.QtWidgets import QApplication,QWidget,QTreeView,QVBoxLayout,QPushButton,QMainWindow,QTextBrowser,QFileDialog,QAction,QToolBar
import sys
import os
import logging
from . import treemodel
from . import image
from . import PATHS

class TreeWidget(QMainWindow):
    def __init__(self,parent = None):
        super(TreeWidget, self).__init__(parent)
        uic.loadUi(os.path.join(PATHS["UI"],'treemain.ui'),self)
        self.setWindowFlags(QtCore.Qt.Widget)
        self.view = TreeView()
        self.vb = ViewButtons()
        self.setCentralWidget(self.view)
        self.statusbar.addWidget(self.vb)
        
        
        #self.rightAction = QAction('right', self)
        #self.leftAction = QAction('left', self)
        #self.createKeyCtrl(self.rightAction, QtCore.Qt.Key_Right)
        #self.createKeyCtrl(self.leftAction, QtCore.Qt.Key_Left)
        self.connections()
    
    #def createKeyCtrl(self,actionName, key):
    #    actionName.setShortcut(QtGui.QKeySequence(key))
    #    self.addAction(actionName)  
        
    def connections(self):
        self.vb.steps.connect(self.view.move)
        self.view.imgPathChanged.connect(self.progress)
        self.actiontest.triggered.connect(self.setFilter)
        self.view.imgDirChanged.connect(self.releasePoiFilter)
        
    def releasePoiFilter(self):
        if self.actiontest.isChecked():
            self.actiontest.trigger()
            
    def reloadPoiFiles(self,poilist):
        self.poifiles = [i["filename"] for i in poilist]
        self.setFilter()
        
    def setFilter(self):
        if self.actiontest.isChecked():
            self.view.model.setNameFilters(self.poifiles)
        else:
            self.view.model.setNameFilters(["*"+x for x in image.SUPPORTED_EXTENSIONS])
          
    def progress(self, path): 
        currentIdx = self.view.currentIndex()
        imgamount = self.view.model.rowCount(currentIdx.parent())
        imgpos = currentIdx.row()
        try:
            proz = float(imgpos)/imgamount
        except:
            proz = 0
        self.vb.progressBar.setValue(proz*100)
        
        
    #    self.rightAction.triggered.connect(self.getdown)
    #    self.leftAction.triggered.connect(self.getup)
    
    #def getdown(self):
    #    current = self.view.currentIndex()
    #    self.view.expand(current)
    #    if not self.view.model.hasChildren(current):
    #        self.view.setCurrentIndex(self.view.model.index(0,0,current))
            
        
    #def getup(self):
    #    parent = self.view.currentIndex().parent()
    #    self.view.collapse(parent)
    #    self.view.setCurrentIndex(parent)
        #self.actionUAV_Pfad.triggered.connect(lambda: self.view.setLayerVisible("uavpath",self.actionUAV_Pfad.isChecked()))
        #self.actionDroneVisible.triggered.connect(lambda: self.view.setLayerVisible("uav",self.actionDroneVisible.isChecked()))
        #self.actionPoisVisible.triggered.connect(lambda: self.view.setLayerVisible("pois",self.actionPoisVisible.isChecked()))
       
    def setRoot(self,rd):
        self.rp = RootPath(rd)
        self.view.loadRoot(self.rp.rootdir)
        self.rp.changed.connect(self.view.loadRoot)
        self.toolBar.addWidget(self.rp)
   
class RootPath(QWidget):
    changed = QtCore.pyqtSignal(str)
    log = QtCore.pyqtSignal(str)
    rootdir = ""
    def __init__(self, rootdir = None):#TODO: abfangen wenn pfad falsch
        super(RootPath, self).__init__()
        uic.loadUi(os.path.join(PATHS["UI"],"rootpath.ui"),self)
        if rootdir is not None:
            self.rootdir = rootdir
        self.toolButton.clicked.connect(self.ChooseRootPath)
        self.lineEdit.setText(self.rootdir)
        
    def ChooseRootPath(self,x):
        self.rootdir = str(QFileDialog.getExistingDirectory(self, "Select Directory",self.rootdir))
        self.lineEdit.setText(self.rootdir)
        self.changed.emit(self.rootdir)
        
class ViewButtons(QWidget):
    log = QtCore.pyqtSignal(str)
    steps = QtCore.pyqtSignal(int)
    def __init__(self):
        super(ViewButtons, self).__init__()
        uic.loadUi(os.path.join(PATHS["UI"],"view-buttons.ui"),self)
        self.shortcuts()
        self.connections()
    
    def connections(self):
        self.right_btn.clicked.connect(lambda:self.steps.emit(1))
        self.left_btn.clicked.connect(lambda:self.steps.emit(-1))
        self.right_btn_2.clicked.connect(lambda:self.steps.emit(10))
        self.left_btn_2.clicked.connect(lambda:self.steps.emit(-10))
        
        self.downAction.triggered.connect(lambda:self.steps.emit(1))
        self.upAction.triggered.connect(lambda:self.steps.emit(-1))
        self.pgdownAction.triggered.connect(lambda:self.steps.emit(10))
        self.pgupAction.triggered.connect(lambda:self.steps.emit(-10))
        
    def shortcuts(self):
        self.downAction = QAction('down', self)
        self.upAction = QAction('up', self)
        self.pgdownAction = QAction('pgdown', self)
        self.pgupAction = QAction('pgup', self)
        self.createKeyCtrl(self.downAction, QtCore.Qt.Key_Down)
        self.createKeyCtrl(self.upAction, QtCore.Qt.Key_Up)
        self.createKeyCtrl(self.pgdownAction, QtCore.Qt.Key_PageDown)
        self.createKeyCtrl(self.pgupAction, QtCore.Qt.Key_PageUp)
            
    def createKeyCtrl(self,actionName, key):
        actionName.setShortcut(QtGui.QKeySequence(key))
        self.addAction(actionName)    

        
class TreeView(QTreeView):
    log = QtCore.pyqtSignal(str)
    currentPath = QtCore.pyqtSignal(str)
    rootDirChanged = QtCore.pyqtSignal(str)
    imgPathChanged = QtCore.pyqtSignal(str)  #imgpath is the full absolute path of the current image
    imgDirChanged = QtCore.pyqtSignal(str)   #imgdir is the current folder where the images are in
    rootdir = ""
    imgdir = ""
    aralist = []
    imgname = ""
    def __init__(self,parent = None):
        super(TreeView, self).__init__(parent)
        self.model = treemodel.TreeModel() 
        self.model.setReadOnly(False)
        self.model.setNameFilters(["*"+x for x in image.SUPPORTED_EXTENSIONS])
        self.model.setNameFilterDisables(False)
        self.model.directoryLoaded.connect(self.rootPathLoaded)
     #   self.sortByColumn(1,QtCore.Qt.AscendingOrder)
     #   self.setSortingEnabled(True)
        
     
    def loadRoot(self,root):
        self.rootdir = root
        self.model.setRootPath(root)
        self.setModel(self.model)
        self.hideColumn(1)
        self.hideColumn(2)
        self.hideColumn(3)
        rootindex = self.model.index(root)
        self.setRootIndex(rootindex)
        self.rootDirChanged.emit(root)
            
    def rootPathLoaded(self,rootpath):
        rootindex = self.model.index(rootpath)
        if self.model.hasChildren(rootindex):
            firstchild = self.model.index(0,0,rootindex)
            self.setCurrentIndex(firstchild)
    
    def setCurrent(self,name):
        curpath = self.current_path()        
        curdir = curpath if os.path.isdir(curpath) else os.path.dirname(curpath)    
        index = self.model.index(os.path.join(curdir,name))
        self.setCurrentIndex(index)
        
    def move(self,steps):
        i = self.currentIndex()
        newindex = self.model.sibling(i.row()+steps,0,i)
        if not newindex.row() == -1:
            self.setCurrentIndex(newindex)
        else:
            if steps>0:
                last = self.model.rowCount(self.model.parent(i))
                newindex = self.model.sibling(last-1,0,i)
            if steps<0:
                newindex = self.model.sibling(0,0,i)
            self.setCurrentIndex(newindex)
        
    def current_path(self):
        return str(self.model.fileInfo(self.currentIndex()).absoluteFilePath())
        
    def currentChanged(self, current, last):
        #print ("TV, CURRENT CHANGED")
        self.scrollTo(current)
        upper = self.indexAbove(current)
        if upper.isValid():
            if self.visualRect(upper).y() < 0:
                self.scrollTo(upper)
        
        curpath = self.current_path()        
        lastpath = str(self.model.fileInfo(last).absoluteFilePath())
        self.currentPath.emit(curpath)
        if os.path.isfile(curpath): 
            self.imgname = os.path.basename(curpath)
            self.imgPathChanged.emit(curpath)
        lastdir = lastpath if os.path.isdir(lastpath) else os.path.dirname(lastpath)    
        curdir = curpath if os.path.isdir(curpath) else os.path.dirname(curpath)    
        if os.path.isdir(lastdir): 
            if not os.path.samefile(lastdir,curdir):
                self.imgdir = curdir
                self.imgDirChanged.emit(curdir)
        
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    if os.name == "nt":
       import ctypes
       myappid = 'dlr.wildretter.poitagger.1' 
       ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app_icon = QtGui.QIcon()
    app_icon.addFile(os.path.join(PATHS["ICONS"],'poitagger/16x16_.png'), QtCore.QSize(16,16))
    app_icon.addFile(os.path.join(PATHS["ICONS"],'poitagger/24x24_.png'), QtCore.QSize(24,24))
    app_icon.addFile(os.path.join(PATHS["ICONS"],'poitagger/32x32_.png'), QtCore.QSize(32,32))
    app_icon.addFile(os.path.join(PATHS["ICONS"],'poitagger/48x48_.png'), QtCore.QSize(48,48))
    app_icon.addFile(os.path.join(PATHS["ICONS"],'poitagger/256x256_.png'), QtCore.QSize(256,256))

    rootdir = "D:/WILDRETTER-DATEN"
    treemain = TreeWidget()
    treemain.setRoot(rootdir)

    # Escape by Key
    treemain.escAction = QAction('escape', treemain)
    treemain.escAction.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Escape))
    treemain.addAction(treemain.escAction)
    treemain.escAction.triggered.connect(treemain.close)
    treemain.setWindowIcon(app_icon)
    
    treemain.show()
    sys.exit(app.exec_())