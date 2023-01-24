import database

def listtodict(lst):
    dic = {}
    for i in lst:
        if not i[0] in dic:
            dic[i[0]]={}
        if len(i) == 3:     
            dic[i[0]][i[1]]=i[2]
        if len(i) == 2:
            dic[i[0]]=i[1]
    return dic

def dict_generator(indict, pre=None):
    pre = pre[:] if pre else []
    if isinstance(indict, dict):
        for key, value in indict.items():
            if isinstance(value, dict):
                for d in dict_generator(value, pre + [key]):
                    yield d
            elif isinstance(value, list) or isinstance(value, tuple):
                for v in value:
                    for d in dict_generator(v, pre + [key]):
                        yield d
            else:
                yield pre + [key, value]
    else:
        yield pre + [indict]
        
db = database.DB("C:/Users/marti/OneDrive/Dokumente/GitHub/poitagger2/poitagger/poitagger_default.db")
CONF = db.query("SELECT ConfigGroup.name,Config.name,value FROM Config JOIN ConfigGroup ON group_fk = ConfigGroup.id ")
C = listtodict(CONF)

C["PATHS"]["rootdir"] = "C:/Testaverzeichnis"
C['IMPORT']['nurFlugBilder'] =  'trdddddue'

cg = db.query("SELECT name,id FROM ConfigGroup")
CG = listtodict(cg)
CONF2 = db.query("SELECT ConfigGroup.name,Config.name,value FROM Config JOIN ConfigGroup ON group_fk = ConfigGroup.id ")
out = []
for i in dict_generator(C):
    tup = (i[0],i[1],i[2])
    if tup not in CONF2:
        out.append(i)

for i in out:
    update = "UPDATE Config SET value = '"+i[2]+"' WHERE name = '"+i[1]+"' AND group_fk = '"+str(CG[i[0]])+"' "
    db.cur.execute(update)
    #print(update)

db.disconnect()
