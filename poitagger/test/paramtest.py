from PyQt5 import QtCore,QtGui,uic #, QtWidgets,QtTest
from PyQt5.QtWidgets import QApplication,QWidget,QMainWindow 
#, QLineEdit,QToolButton,QAction,QMessageBox,QPushButton,QVBoxLayout,QProgressDialog
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import json
from poitagger import flightjson
import sys
import nested
from collections import OrderedDict,MutableMapping,MutableSequence,defaultdict


types = {"<class 'int'>":"int",
        "<class 'float'>":"float",
        "<class 'str'>":"str",
        "<class 'bool'>":"bool",
        "<class 'bytes'>":"str"}

def dictToParam(k,v,**kwargs):
    '''
    this is a callback function for nested. it converts the output of saveState() from a Parameter from the pyQtGraph module.
    This output is an OrderedDict with specific structure like the following:
    
    calling nested with this callbackfunction leads to a parameter state dictionary:
    '''
    l = len(kwargs["parentlist"])
    if l>0 and kwargs["parentlist"][0] == "uavpath":
        if l==1: return {"name": str(k), 'type': "str", 'readonly':True,'value': v}
        return v
    if l>0 and kwargs["parentlist"][0] == "pois":
        return v
    #if l>2 and kwargs["parentlist"][0] == "pois" and  kwargs["parentlist"][2] == "data" :
    #    if l>4: return v
    #    elif l==4: return {"name": str(k), 'type': "str", 'readonly':True,'value': v}
    #    return {"name": str(k), 'type': "group", 'children': v}
        
    if not isinstance(v,(MutableMapping,MutableSequence,tuple)):
        return {"name": str(k), 'type': types.get(str(type(v)),"str"), 'readonly':True, 'decimals':9, 'value': v }
    else:
        return {"name": str(k), 'type': "group", 'children': v}
    
    
if __name__== "__main__":

    import sys
    #app = QApplication(sys.argv)
    
    #pm = PoiModel()
    with open("D:/WILDRETTER-DATEN/2017_DLR/2017-04-05_14-56_Hausen/.poitagger.json","r") as stream:
        meta = json.load(stream)
    #print(meta["children"]["general"])

    Meta = nested.Nested(meta,dictToParam).data    
    #print(Meta)
    categories= [{"name":"general",'type':"group"},
                        {"name":"calibration",'type':"group"},
                        {"name":"pois",'type':"group"},
                        {"name":"images",'type':"group"},
                        {"name":"uavpath",'type':"group"}]
    p = Parameter.create(name="flightparam",type="group",children=categories)
    #p = Parameter.create(name="flightparam",type="group",children=[])
    p.restoreState(Meta)
    #print(dir(p))#.child("general")
    for i in p.children():
        print (i.name(),i.value())
    #sys.exit(app.exec_())
