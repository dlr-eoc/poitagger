from collections import MutableMapping, MutableSequence,OrderedDict
import logging
import re


def nothing(key,value,**kwargs):
    return value


def reduce_rdf(k,v,**kwargs): 
    '''
    this is a callback function for nested. 
    it reduces single rdf-lists to its value
    example:
    >>>rdfdict = {'@rdf:about': '', 
        'camera:bandname': OrderedDict([('rdf:seq',OrderedDict([('rdf:li', 'LWIR')]))]),
        'camera:centralwavelength': OrderedDict([('rdf:seq', OrderedDict([('rdf:li', '10000')]))]),
        'camera:wavelengthfwhm': OrderedDict([('rdf:seq',OrderedDict([('rdf:li', '4500')]))]),
        'camera:tlineargain': '0.00',}
    
    >>>nested.Nested(rdfdict,reduce_rdf).data
    {'@rdf:about': '', 
        'camera:bandname': 'LWIR', 
        'camera:centralwavelength': '10000',
        'camera:wavelengthfwhm': '4500', 
        'camera:tlineargain': '0.00'}
     '''
    if type(v) == dict:
        if len(v)==1 and next(iter(v)) == "rdf:seq":
            if type(v["rdf:seq"])==dict and len(v["rdf:seq"]) ==1: 
                return v["rdf:seq"].get("rdf:li",v)
    return v   
    
def pre_paramtodict(k,v,**kwargs):
    '''
    this is a callback function for nested. it converts the output of getValues() from a Parameter from the pyQtGraph module.
    This output is an OrderedDict with specific structure like the following:
    >>>A = OrderedDict([('general', (None, OrderedDict([('bounding', (None, OrderedDict([ ('0', (None, OrderedDict([ ('0', (100, OrderedDict())), 
      ('1', (200, OrderedDict()))]))),]))), ('path',  ('blablabla', OrderedDict()))]))),])
    
    calling nested with this callbackfunction leads tO a reduced dictionary:
    >>>nested(A,callback_paramtodict)  
    {'general': [{'bounding': [[100, 200]], 'path': 'blablabla'}]}
    '''
    if (type(v) == tuple) and len(v)==2 and (type(v[1]) == OrderedDict): 
        if (not v[0] is None) and (type(v[1])== OrderedDict) and (len(v[1])==0): #not nested
            return [v[0]]
        elif v[0]== None and type(v[1])== OrderedDict: #nested
            return [dict(v[1])]
        else: # this is just the ambiguous case. e.g.: ("myvalue", OrderedDict([('1',"one"),('2',"two")]))
            if kwargs.get("keep_children",True): #keep the OrderedDict([('1',"one"),('2',"two")]) as value
                return [v[1]] #the list is necessary because else the returned value is not iterable anymore. 
                                #It will be removed by post_callback
            else: # keep "myvalue" as value
                return [v[0]] #the list is necessary because else the returned value is not iterable anymore. 
                                #It will be removed by post_callback
    return v

def paramtodict(k,v,**kwargs): 
    '''
    this callback function only reduces the unnecessary List-brackets around single length data
    '''
    if type(v) == list and len(v) ==1 and not type(v[0]) in [dict,list,tuple]:
        v = v[0]
    elif type(v) == list and len(v) == 1 and type(v[0]) == dict:
        if list(v[0].keys()) == [str(i) for i in range(0,len(v[0]))]:
            v = list(v[0].values())
        else:
            v = v[0]
    return v
    
def lowerkeys(k,v,**kwargs): 
    '''
    this is a callback function for nested. 
    it just converts all keys to lowercase
     '''
    if type(v) == dict:
        return {k1.lower() if type(k1) in [bytes,str] else k1: v1 for k1,v1 in v.items()}
    return v       
   
def getBranch(container,branchlist):
    '''
        useful for inner callback usage.
        example: nested.getBranch(a,kwargs["parentlist"])
    '''
    if len(branchlist)==0:
        return container
    else: 
        return getBranch(container.get(branchlist.pop(0)),branchlist)
        
class Nested():
    def __init__(self,container=None,callback=nothing,callback_pre=nothing,rootname="root",**kwargs):
        self.input = container
        self.callback = callback
        self.callback_pre = callback_pre
        self.rootname = rootname
        self.dicttype = kwargs.get("dicttype",None)    
        self.listtype = kwargs.get("listtype",None)    
        self.tupletype = kwargs.get("tupletype",tuple)
        if container:
            self.load(container,**kwargs)
            
    def load(self,container,**kwargs):    
        self.branches = ["/"]
        kwargs["parent"]="/"
        kwargs["parentlist"]= []
        
        if isinstance(container, MutableMapping):
            self.data = self.nestedDict(self.rootname,container,**kwargs)
        elif isinstance(container, MutableSequence):
            self.data = self.nestedList(self.rootname,container,**kwargs)
        elif isinstance(value, tuple):
            self.data = self.nestedTuple(self.rootname,container,**kwargs)
        else:
            self.data = self.nestedValue(self.rootname,container,**kwargs)
        return self.data
        
    def inner(self,container,key,value,appendfunction,kwargs):
        value = self.callback_pre(key,value,**kwargs)
        before = kwargs["parent"]
        kwargs["parent"] += re.sub(r'(?<!\\)/', "\/",str(key)) + "/" 
        kwargs["parentlist"].append(key)
        if not isinstance(value,(MutableMapping,MutableSequence,tuple)):
            appendfunction(key,self.nestedValue(key,value,**kwargs))
        else:    
            self.branches.append(kwargs["parent"])
            if isinstance(value, MutableMapping):
                appendfunction(key,self.nestedDict(key,value,**kwargs))
            elif isinstance(value, MutableSequence):
                appendfunction(key,self.nestedList(key,value,**kwargs))
            elif isinstance(value, tuple):
                appendfunction(key,self.nestedTuple(key,value,**kwargs))
        kwargs["parent"] = before #"/".join(re.split(r'(?<!\\)/', kwargs["parent"])[:-1])
        kwargs["parentlist"].pop()
        #print ("\x1b[32m\"DATA", container,key,value,kwargs,"\"\x1b[32m")
        return container
    
    def nestedList(self,key,lst,**kwargs):
        if self.listtype==None:
            tree = type(lst)()
        else:
            tree = self.listtype()
        for k,v in enumerate(lst):
            self.inner(tree,k,v,lambda k,v: tree.append(v),kwargs)
        return self.callback(key,tree,**kwargs)

    def nestedTuple(self,key,lst,**kwargs):
        tree = []
        for k,v in enumerate(lst):
            self.inner(tree,k,v,lambda k,v: tree.append(v),kwargs)
        return self.callback(key,self.tupletype(tree),**kwargs)

    def nestedValue(self,key,value,**kwargs):
        return self.callback(key,value,**kwargs)

    def nestedDict(self,key,dic,**kwargs):
        if self.dicttype==None:
            tree = type(dic)()
        else:
            tree = self.dicttype()
        for k,v in dic.items():
            self.inner(tree,k,v,tree.__setitem__,kwargs)
        return self.callback(key,tree,**kwargs)
   
if __name__ == '__main__':
    pass