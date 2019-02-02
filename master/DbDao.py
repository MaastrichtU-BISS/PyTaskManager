class DbDao:
    sqlite = __import__('sqlite3')
    def __init__(self):
        self.dbLoc = 'db.sqlite'
        dbCon = self.sqlite.connect(self.dbLoc)
        dbCon.execute("CREATE TABLE IF NOT EXISTS client ( "
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name CHAR(255), "
            "email CHAR(255), "
            "institute CHAR(255), "
            "country CHAR(255), "
            "ip CHAR(255),"
            "last_seen DATETIME );")
        dbCon.execute("CREATE TABLE IF NOT EXISTS task ( "
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "client INT, "
            "runId CHAR(255), "
            "image CHAR(255), "
            "input TEXT, "
            "FOREIGN KEY (client) REFERENCES client(id) );")
        dbCon.execute("CREATE TABLE IF NOT EXISTS task_result ( "
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "task INTEGER, "
            "response TEXT, "
            "log TEXT, "
            "FOREIGN KEY(task) REFERENCES task(id) );" )
        dbCon.commit()
        dbCon.close()
    def selectQuery(self, query, myVars=None):
        dbCon = self.sqlite.connect(self.dbLoc)
        dbCon.row_factory = self.sqlite.Row
        cur = dbCon.cursor()
        cur.execute(query=query, vars=myVars)
        data = cur.fetchall()
        dbCon.close()
        return [dict(ix) for ix in data]
    def getClients(self):
        return self.selectQuery("SELECT * FROM client")
    def addClient(self,name,email,institute,country,ip):
        dbCon = self.sqlite.connect(self.dbLoc)
        cur = dbCon.cursor()
        cur.execute("INSERT INTO client (name, email, institute, country, ip) VALUES ( ?, ?, ?, ?, ?)",
            (name, email, institute, country, ip))
        id = cur.lastrowid
        dbCon.commit()
        dbCon.close()
        return id
    def addTask(self, clientId, runId, image, inputStr):
        dbCon = self.sqlite.connect(self.dbLoc)
        cur = dbCon.cursor()
        cur.execute("INSERT INTO task (client, runId, image, input) VALUES ( ?, ?, ?, ?)",
            (str(clientId), str(runId), image, inputStr))
        id = cur.lastrowid
        dbCon.commit()
        dbCon.close()
        return id
    def getClientOpenTasks(self,clientId):
        return self.selectQuery("SELECT t.id, t.runId, t.input, t.image FROM task t LEFT OUTER JOIN task_result tr ON t.id = tr.task WHERE t.client = ? AND tr.id IS NULL", str(clientId))
    def addTaskResult(self,taskId,response,log):
        dbCon = self.sqlite.connect(self.dbLoc)
        cur = dbCon.cursor()
        cur.execute("INSERT INTO task_result (task, response, log) VALUES ( ?, ?, ?)",
            (str(taskId), response, log))
        id = cur.lastrowid
        dbCon.commit()
        dbCon.close()
        return id
    def getTaskResult(self, taskId):
        return self.selectQuery("SELECT * FROM task_result WHERE task = %d" % taskId)
    def setClientTimestamp(self, clientId):
        dbCon = self.sqlite.connect(self.dbLoc)
        cur = dbCon.cursor()
        cur.execute("UPDATE client SET last_seen = DATETIME('now') WHERE id = ?", str(clientId))
        dbCon.commit()
        dbCon.close()
        return id