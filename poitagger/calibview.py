from PyQt5 import QtCore,QtGui,uic
from PyQt5.QtWidgets import QMainWindow
import pyqtgraph as pg
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import logging

def is_equal(a, b, encoding="utf8"):
    if isinstance(a, bytes):
        a = a.decode(encoding)
    if isinstance(b, bytes):
        b = b.decode(encoding)
    return a == b

types = {"<class 'int'>":"int",
        "<class 'float'>":"float",
        "<class 'str'>":"str",
        "<class 'bool'>":"bool",
        "<class 'bytes'>":"str"}


def paramtree(dic):
    params = []
    for k,v in dic.items():
        if type(v) is not dict:
            params.append({"name": k, 'type': types.get(str(type(v)),"str"), 'renamable':True, 'decimals':9, 'value': v})
        else:
            params.append({"name": k, 'type': "group", 'expanded':True, 'renamable':True, 'children': paramtree(v)})
    return params
    
class Calib(QMainWindow):
    log = QtCore.pyqtSignal(str)
    
    def __init__(self,parent = None):
        super(Calib,self).__init__(parent)
        self.t = ParameterTree()
        
    def load_data(self,Meta): 
        self.Meta = Meta
        self.p = Parameter.create(name='params', type='group', children=paramtree(Meta["general"]))
        self.t.setParameters(self.p, showTop=False)
        
    def append(self,param):
        #print (type(self.Meta))
        self.Meta["bla"] = "trara"
        self.p.insertChild(0, paramtree(param)[0])

if __name__=="__main__":

    class addon(QtCore.QObject):
        
        def log(self,string):
            print(string)
        def change(self,meta,content):
            meta.update(content)
            
        def Print(self,meta):    
            print(meta)
    
    from PyQt5.QtWidgets import QApplication,QAction,QTextBrowser,QToolBar,QPushButton
    import sys
    import flightmeta
    app = QApplication(sys.argv)
    path = "D:/WILDRETTER-DATEN/2017_DLR/2017-04-05_14-56_Hausen"
    fm = flightmeta.FlightMeta(path)
    fm.start()
    win = Calib()
    fm.meta_changed.connect(win.load_data)
    win.setCentralWidget(win.t)
    tb = QToolBar(win)
    trig = QPushButton(win)
    trig.setText("change")
    trig.clicked.connect(lambda: a.change(fm.Meta,{"pois":[{"bla":"blabla"}]}))
    
    fm.Meta.changed.connect(lambda: a.log("jetzt veraendert!"))
    fm.Meta["pois"].changed.connect(lambda: a.log("POIS veraendert!"))
    
    trig2 = QPushButton(win)
    trig2.setText("print")
    trig2.clicked.connect(lambda: a.Print(fm.Meta))
    print (type(fm.Meta["pois"]))
    insert = QPushButton(win)
    insert.setText("insert")
    insert.clicked.connect(lambda: win.append({"namsade":"vaasdlue"}))
    
    insert.clicked.connect(lambda: a.log("jetzt"))
    
    tb.addWidget(trig)
    tb.addWidget(trig2)
    tb.addWidget(insert)
    win.addToolBar(tb)
    win.show()
    a = addon()
    
    fm.meta_changed.connect(lambda: a.log("Da wurde was veraendert"))
    
    # Escape by Key
    win.escAction = QAction('escape', win)
    win.escAction.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Escape))
    win.addAction(win.escAction)
    win.escAction.triggered.connect(win.close)
      
    sys.exit(app.exec_())
