from flask import Flask, Response, request
import json
from DbDao import DbDao
import signal
import sys
import time

# Init configuration file
configFile = open("config.json")
config = json.load(configFile)
configFile.close()

time.sleep(10)

app = Flask('TaskMaster')
dbDao = DbDao(config["connectionString"])

def signal_handler(sig, frame):
    print("closing application and db connection")
    dbDao.closeConnection()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

@app.route('/')
def index():
    return "Hello, World"

@app.route('/client')
def clientList():
    clientList = dbDao.getClients()
    return Response(json.dumps(clientList), mimetype='application/json')

@app.route('/client/add', methods=["POST"])
def addClient():
    try:
        data = request.get_json()
    except:
        return Response(json.dumps({"success": False, 'message': "Could not parse input as JSON"}), mimetype="application/json")

    try:
        clientId = dbDao.addClient(data["name"], data["email"], data["institute"], data["country"], request.remote_addr)
        data = {
            'success': True,
            'clientId': clientId
        }
    except:
        data = {
            'success': False,
            'message': "Could not insert data in database"
        }

    return Response(json.dumps(data), mimetype="application/json")

@app.route('/client/<int:clientId>/task')
def getClientTasks(clientId):
    openTasks = dbDao.getClientOpenTasks(clientId)
    dbDao.setClientTimestamp(clientId)
    return Response(json.dumps(openTasks), mimetype='application/json')

@app.route('/client/<int:clientId>/task/add', methods=["POST"])
def addClientTask(clientId):
    try:
        data = request.get_json()
    except:
        return Response(json.dumps({"success": False, 'message': "Could not parse input as JSON"}), mimetype="application/json")

    try:
        taskId = dbDao.addTask(clientId, data["runId"], data["image"], data["inputString"])
        data = {
            'success': True,
            'taskId': taskId
        }
    except:
        data = {
            'success': False,
            'message': "Could not insert task in database"
        }
    
    return Response(json.dumps(data), mimetype="application/json")

@app.route('/client/<int:clientId>/task/<int:taskId>/result')
def getTaskResult(clientId, taskId):
    taskResult = dbDao.getTaskResult(taskId)
    return Response(json.dumps(taskResult), mimetype='application/json')

@app.route('/client/<int:clientId>/task/<int:taskId>/result/output')
def getTaskResultOutput(clientId, taskId):
    taskResult = dbDao.getTaskResult(taskId)[0]
    responseStr = str(taskResult["response"])
    return Response(responseStr, mimetype="text/plain")

@app.route('/client/<int:clientId>/task/<int:taskId>/result/log')
def getTaskResultLog(clientId, taskId):
    taskResult = dbDao.getTaskResult(taskId)[0]
    return Response(str(taskResult["log"]), mimetype="text/plain")

@app.route('/client/<int:clientId>/task/<int:taskId>/result/add', methods=["POST"])
def addTaskResult(clientId, taskId):
    try:
        data = request.get_json()
    except:
        return Response(json.dumps({"success": False, 'message': "Could not parse input as JSON"}), mimetype="application/json")
    
    try:
        resultId = dbDao.addTaskResult(taskId, data["response"], data["log"])
        dbDao.setClientTimestamp(clientId)
        data = {
            'success': True,
            'taskId': resultId
        }
    except:
        data = {
            'success': False,
            'message': "Could not insert task result in database"
        }
    return Response(json.dumps(data), mimetype="application/json")

app.run(debug=True, host='0.0.0.0', port=5000)
