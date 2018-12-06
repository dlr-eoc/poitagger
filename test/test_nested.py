import pytest
import nested
from observable import *
from collections import OrderedDict

def test_simple():
    test= {"int":1,"dict":{"tuple":(1,2,3),"list":[5,2],"listof":[{1:3,"3":"1"},("qw",3,1.34)]}}
    n = nested.Nested(test,dicttype=ObservableDict,listtype=ObservableList,tupletype=list)
    print ("nested",n.data)
    right = ObservableDict({'int': 1, 'dict': ObservableDict({'tuple': [1, 2, 3], 'list': ObservableList([5, 2]), 'listof': ObservableList([ObservableDict({1: 3, '3': '1'}), ['qw', 3, 1.34]])})}) 
    print ("right",right)
    assert n.data == right

def test_tuple():
    test= {"int":1,"dict":{"tuple":(1,2,3),"list":[5,2],"listof":[{1:3,"3":"1"},("qw",3,1.34)]}}
    n = nested.Nested(test,dicttype=ObservableDict,listtype=ObservableList)
    print ("nested",n)
    right = ObservableDict({'int': 1, 'dict': ObservableDict({'tuple': (1, 2, 3), 'list': ObservableList([5, 2]), 'listof': ObservableList([ObservableDict({1: 3, '3': '1'}), ('qw', 3, 1.34)])})}) 
    print ("right",right)
    assert n.data == right
    assert type(n.data) == ObservableDict
    assert type(n.data["dict"]) == ObservableDict
    assert type(n.data["dict"]["list"]) == ObservableList
    assert type(n.data["dict"]["listof"]) == ObservableList
    assert type(n.data["dict"]["listof"][0]) == ObservableDict
    assert type(n.data["dict"]["listof"][1]) == tuple
    
def test_tuple2():
    test= {"int":1,"dict":{"tuple":(1,2,3),"list":[5,2],"listof":[{1:3,"3":"1"},("qw",3,1.34)]}}
    n = nested.Nested(test,dicttype=ObservableDict,listtype=ObservableList)
    print ("nested",n)
    right = {"int":1,"dict":{"tuple":(1,2,3),"list":[5,2],"listof":[{1:3,"3":"1"},("qw",3,1.34)]}}
    print ("right",right)
    assert n.data == right
    
def test_paramtodict():
    A = OrderedDict([('general', (None, OrderedDict([('bounding', (None, OrderedDict([ ('0', (None, OrderedDict([ ('0', (100, OrderedDict())), 
      ('1', (200, OrderedDict()))]))),]))), ('path',  ('blablabla', OrderedDict()))]))),])
    assert nested.Nested(A,nested.paramtodict,nested.pre_paramtodict,tupletype=list).data == {'general':{'bounding':[[100,200]],'path':'blablabla'}}
   
 
def test_paramtodict_class():
    A = OrderedDict([('general', (None, OrderedDict([('bounding', (None, OrderedDict([ ('0', (None, OrderedDict([ ('0', (100, OrderedDict())), 
      ('1', (200, OrderedDict()))]))),]))), ('path',  ('blablabla', OrderedDict()))]))),])
    n = nested.Nested(A,nested.paramtodict,nested.pre_paramtodict,tupletype=list)
    assert n.data == {'general':{'bounding':[[100,200]],'path':'blablabla'}}
   
   
def test_paramtodict2():
    B = OrderedDict([('general', (None, OrderedDict([
                        ('bounding', (None, OrderedDict([
                            ('0', (None, OrderedDict([
                                ('0', (100, OrderedDict())), 
                                ('1', (200, OrderedDict()))]))),
                            ('1', (None, OrderedDict([
                                ('0', (300, OrderedDict())), 
                                ('1', (400, OrderedDict()))])))]))), 
                        ('path', 
                             ('blablabla', OrderedDict()))]))), 
                 ('pois', (23, OrderedDict([
                     ('0', (1, OrderedDict())), 
                     ('1', (2, OrderedDict())), 
                     ('2', (3, OrderedDict())), 
                     ('3', (4, OrderedDict()))])))])
    print(B)
    n = nested.Nested(B,nested.paramtodict,nested.pre_paramtodict,tupletype=list)
    print(n.data)
    right = {'general':{'bounding':[[100,200],[300,400]],'path':'blablabla'},'pois':[1,2,3,4]}
    assert n.data == right
    
if __name__ == "__main__":    
    test_paramtodict_class()