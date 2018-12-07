from PyQt5 import QtCore,QtGui,uic
import pyqtgraph as pg
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import traceback

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
            params.append({"name": k, 'type': types.get(str(type(v)),"str"), 'decimals':9, 'value': v})
        else:
            params.append({"name": k, 'type': "group", 'children': paramtree(v)})
    return params
    
class Info(QtGui.QWidget):
    log = QtCore.pyqtSignal(str)
    position = QtCore.pyqtSignal(float,float) # lat, lon
    
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.t = ParameterTree()
        self.importer = ImportInfo()
        self.t.setParameters(self.importer.p, showTop=False)
        self.importer.finished.connect(self.reloaded)
       
    def load_data(self,ara): 
        self.savedScrollPosition = self.t.verticalScrollBar().value()
        self.importer.load(ara)
        self.importer.start()
       
    def reloaded(self):
        self.t.verticalScrollBar().setValue(self.savedScrollPosition)
        lat = self.importer.p.child("gps").child("latitude").value()
        lon = self.importer.p.child("gps").child("longitude").value()
        self.position.emit(float(lat),float(lon))
        

class ImportInfo(QtCore.QThread):
    finished = QtCore.pyqtSignal()
    def __init__(self):
        QtCore.QObject.__init__(self)
        categories = [{"name":"camera",'type':"group"},
                    {"name":"uav",'type':"group"},
                    {"name":"image",'type':"group"},
                    {"name":"file",'type':"group"},
                    {"name":"gps",'type':"group"}]
        self.p = Parameter.create(name='params', type='group',children=categories)
        
    def load(self,meta):
        self.meta = meta
        self.start()
    
    def run(self):
        self.p.treeChangeBlocker()
        self.p.restoreState({"name":"params", "type":"group", "children":paramtree(self.meta)})
        self.p.unblockTreeChangeSignal()
        self.finished.emit()
        
        
if __name__=="__main__":
    pass
    