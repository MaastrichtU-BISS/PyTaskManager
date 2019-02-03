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
        dbCon.row_factory = self.dbLib.Row
        cur = dbCon.cursor()
        cur.execute(query, myVars)
        data = cur.fetchall()
        dbCon.close()
        return [dict(ix) for ix in data]
    def modifyQuery(self, query, myVars=None):
        dbCon = self.dbLib.connect(self.dbLoc)
        cur = dbCon.cursor()
        cur.execute(query, myVars)
        id = cur.lastrowid
        dbCon.commit()
        dbCon.close()
        return id
    def getClients(self):
        return self.selectQuery("SELECT * FROM client")
    def addClient(self,name,email,institute,country,ip):
        return self.modifyQuery("INSERT INTO client (name, email, institute, country, ip) VALUES ( ?, ?, ?, ?, ?)",
            (name, email, institute, country, ip))
    def addTask(self, clientId, runId, image, inputStr):
        return self.modifyQuery("INSERT INTO task (client, runId, image, input) VALUES ( ?, ?, ?, ?)",
            (str(clientId), str(runId), image, inputStr))
    def getClientOpenTasks(self,clientId):
        return self.selectQuery("SELECT t.id, t.runId, t.input, t.image FROM task t LEFT OUTER JOIN task_result tr ON t.id = tr.task WHERE t.client = ? AND tr.id IS NULL", str(clientId))
    def addTaskResult(self,taskId,response,log):
        return self.modifyQuery("INSERT INTO task_result (task, response, log) VALUES ( ?, ?, ?)",
            (str(taskId), response, log))
    def getTaskResult(self, taskId):
        return self.selectQuery("SELECT * FROM task_result WHERE task = ?", str(taskId))
    def setClientTimestamp(self, clientId):
        return self.modifyQuery("UPDATE client SET last_seen = DATETIME('now') WHERE id = ?", str(clientId))