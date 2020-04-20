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
    

logger = logging.getLogger(__name__)

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
