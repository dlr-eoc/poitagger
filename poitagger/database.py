import sqlite3



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
        

class DB(object):
    def __init__(self,database='poitagger_default.db'):
        self.connect(database)
        pass
    def connect(self, database):
        self.con = sqlite3.connect(database)
        self.cur = self.con.cursor()
        
    def disconnect(self):
        self.cur.close()
        self.con.commit()
        self.con.close()
        
    def showtables(self):
        return [i[0] for i in db.query("SELECT name FROM sqlite_master")]
    
    def columns(self,table):
        return self.query("PRAGMA table_info({});".format(table))
        
    def query(self,sql):    
        self.cur.execute(sql)
        self.lastresult = self.cur.fetchall()
        return self.lastresult
        
    def update(self,sql):
        self.cur.execute(sql)
        self.con.commit()
    
    def insert(self,sql):
        self.cur.execute(sql)
        self.con.commit()
        if self.cur.rowcount>0:
            return self.lastid()
        else:
            return self.cur.rowcount
    
    def lastid(self):
        return self.cur.lastrowid
        
    
    def uniqueinsert(self,table,column,value,idcol="id"):
        '''
        inserts values in one or more columns. If there is already an 
        identical entry it gives back the id of this row, else the id of the last entry
        '''
        if isinstance(column, (list, tuple)):
            columns = "'"+"','".join(column)+"'"
            values = "'"+"','".join(value)+"'"
            where = " AND ".join(["{0} = '{1}'".format(c,v) for c,v in zip(column,value)])
        else:
            columns = "'{}'".format(column)
            values = "'{}'".format(value)
            where = "{0} = '{1}'".format(column,value)
        sql = "INSERT INTO {0}({1}) SELECT {2} WHERE NOT EXISTS(SELECT 1 FROM {0} WHERE {3})".format(table,columns,values,where)    
        idx = self.insert(sql)
        if idx > 0:
            return idx
        else:
            sql = "SELECT {0} from {1} WHERE {2}".format(idcol,table,where)
            return self.query(sql)[0][0]
        
    
    def commit(self):
        self.con.commit()
        
    def gettable(self,sql):
        Sql = list(map(str.upper, sql.split()))
        try:
            return Sql[Sql.index("FROM")+1]
        except ValueError:
            return ""
        
    def fetchall(self,sql):
        '''
        fetches all rows of a sql query into a list of dictionaries.
        '''
        res = self.query(sql)
        table = self.gettable(sql)
        col = self.query("PRAGMA table_info({});".format(table))
        matrix = []
        for row in res:
            dic = {}
            for i in range(len(col)): 
                dic[col[i][1]] = row[i]
            matrix.append(dic)    
        return matrix
     
    
    def load_config(self):
        conflist = self.query("SELECT ConfigGroup.name,Config.name,value FROM Config JOIN ConfigGroup ON group_fk = ConfigGroup.id ")
        conf = listtodict(conflist)
        return conf
        
    def safe_config(self, conf):
        cg = self.query("SELECT name,id FROM ConfigGroup")
        CG = listtodict(cg)
        CONF2 = self.query("SELECT ConfigGroup.name,Config.name,value FROM Config JOIN ConfigGroup ON group_fk = ConfigGroup.id ")

        for i in dict_generator(conf):
            if i[2] == None: 
                update = "UPDATE Config SET value = ? WHERE name = '"+str(i[1])+"' AND group_fk = '"+str(CG[i[0]])+"' "
                self.cur.execute(update,(None,))
            else:
                update = "UPDATE Config SET value = '"+str(i[2])+"' WHERE name = '"+str(i[1])+"' AND group_fk = '"+str(CG[i[0]])+"' "
                self.cur.execute(update)
        self.commit()    