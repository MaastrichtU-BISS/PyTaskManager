class DbDao:
    dbLib = __import__('psycopg2')
    def __init__(self):
        self.dbLoc = 'postgresql://postgres:ppdli@localhost:5432/ptm'
        dbCon = self.dbLib.connect(self.dbLoc)
        cur = dbCon.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS client ( "
            "id serial PRIMARY KEY, "
            "name varchar(255), "
            "email varchar(255), "
            "institute varchar(255), "
            "country varchar(255), "
            "ip varchar(255),"
            "last_seen timestamp );")
        cur.execute("CREATE TABLE IF NOT EXISTS task ( "
            "id serial PRIMARY KEY, "
            "client integer, "
            "runId varchar(255), "
            "image varchar(255), "
            "input text, "
            "FOREIGN KEY (client) REFERENCES client(id) );")
        cur.execute("CREATE TABLE IF NOT EXISTS task_result ( "
            "id serial PRIMARY KEY, "
            "task integer, "
            "response text, "
            "log text, "
            "FOREIGN KEY(task) REFERENCES task(id) );" )
        dbCon.commit()
        dbCon.close()
    def selectQuery(self, query, myVars=None):
        dbCon = self.dbLib.connect(self.dbLoc)
        cur = dbCon.cursor()
        cur.execute(query, myVars)
        data = cur.fetchall()
        dbCon.close()

        columns = [ ]
        for column in cur.description:
            columns.append(column.name)

        myData = [ ]
        for row in data:
            myRow = dict()
            for i in range(len(columns)):
                myRow[columns[i]] = row[i]
            myData.append(myRow)
        
        return myData
    def modifyQuery(self, query):
        dbCon = self.dbLib.connect(self.dbLoc)
        cur = dbCon.cursor()
        cur.execute(query + " RETURNING id")
        id = cur.fetchone()[0]
        dbCon.commit()
        dbCon.close()
        return id
    def getClients(self, timeString=True):
        results = self.selectQuery("SELECT * FROM client")

        if timeString:
            for result in results:
                if result["last_seen"] is not None:
                    result["last_seen"] = str(result["last_seen"])
        
        return results
    def addClient(self,name,email,institute,country,ip):
        return self.modifyQuery("INSERT INTO client (name, email, institute, country, ip) VALUES ( '%s', '%s', '%s', '%s', '%s')" % (name, email, institute, country, ip))
    def addTask(self, clientId, runId, image, inputStr):
        return self.modifyQuery("INSERT INTO task (client, runId, image, input) VALUES ( %s, %s, '%s', '%s')" % (clientId, runId, image, inputStr))
    def getClientOpenTasks(self,clientId):
        return self.selectQuery("SELECT t.id, t.runId, t.input, t.image FROM task t LEFT OUTER JOIN task_result tr ON t.id = tr.task WHERE t.client = %s AND tr.id IS NULL" % (clientId))
    def addTaskResult(self,taskId,response,log):
        return self.modifyQuery("INSERT INTO task_result (task, response, log) VALUES ( %s, '%s', '%s')" % (taskId, response, log))
    def getTaskResult(self, taskId):
        return self.selectQuery("SELECT * FROM task_result WHERE task = %s" % (taskId))
    def setClientTimestamp(self, clientId):
        return self.modifyQuery("UPDATE client SET last_seen = now() WHERE id = %s" % (clientId))