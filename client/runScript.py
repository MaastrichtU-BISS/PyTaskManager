import json
import time
import os
import subprocess
from DockerImageImportService import DockerImageImportService

# connect to service
headerData = {
    'Content-Type': "application/json"
}

# Init configuration file
configFile = open("config.json")
clientData = json.load(configFile)
configFile.close()

taskDir = "tasks"
if not os.path.exists(taskDir):
    os.mkdir(taskDir)

runIdDir = "runIds"
if not os.path.exists(runIdDir):
    os.mkdir(runIdDir)

abort = 0

diis = DockerImageImportService("myFiles", 5)
diis.start()

import signal
import sys
def signal_handler(sig, frame):
        diis.stop()
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def readPtmInstructions(rootDir = "myFiles"):
    tasks = [ ]

    historyDir = rootDir + "_history"
    if not os.path.exists(historyDir):
        os.mkdir(historyDir)

    for dirName, subdirList, fileList in os.walk(rootDir):
        for fname in fileList:
            if(fname.endswith(".ptmjob")):
                with open(os.path.join(dirName, fname)) as json_file:  
                    tasks.append(json.load(json_file))
                os.rename(os.path.join(dirName, fname), os.path.join(historyDir, fname))
    return tasks

while abort == 0:
    taskList = list()

    # Connect to central host, if fails do nothing
    taskList = readPtmInstructions()

    # If no task retrieved (or central host down) wait again
    if len(taskList) == 0:
        print("Waiting....")
        time.sleep(clientData["interval"])

    # If there are tasks retrieved, proces task list
    iTask = 0
    while iTask < len(taskList):
        myTask = taskList[iTask]
        taskId = myTask.get('id')
        image = myTask.get('image')
        runId = myTask.get('runId')
        inputText = myTask.get("input")

        #create directory to put files into for this run
        curFolder = os.path.join(os.getcwd(), taskDir, "task"+str(taskId))
        if not os.path.exists(curFolder):
            os.mkdir(curFolder)

        #create directory to stay alive over runs (based on runId)
        runIdFolder = os.path.join(os.getcwd(), runIdDir, str(runId))
        if not os.path.exists(runIdFolder):
            os.mkdir(runIdFolder)

        #put the input arguments in a text file
        inputFilePath = os.path.join(curFolder,"input.txt")
        text_file = open(inputFilePath, "w")
        text_file.write(inputText)
        text_file.close()

        outputFilePath = os.path.join(curFolder,"output.txt")
        text_file = open(outputFilePath, "w")
        text_file.write("")
        text_file.close()

        logFilePath = os.path.join(curFolder,"log.txt")
        text_file = open(logFilePath, "w")
        text_file.write("")
        text_file.close()

        #pulling the image for updates or download
        #subprocess.Popen("docker pull " + image, shell=True)

        dockerParams = "--rm " #container should be removed after execution
        dockerParams += "-v " + inputFilePath + ":/input.txt " #mount input file
        dockerParams += "-v " + outputFilePath + ":/output.txt " #mount output file
        dockerParams += "-v " + logFilePath + ":/log.txt " #mount output file
        dockerParams += "-v " + runIdFolder + "/:/temp/ " #mount runId folder
        dockerParams += "-e RUN_ID=%s " % str(runId)
        dockerParams += "-e SPARQL_ENDPOINT=%s " % clientData["endpointUrl"]
        dockerParams += "-e endpointUrl=%s " % clientData["endpointUrl"]
        dockerParams += "-e endpointType=%s " % clientData["endpointType"]
        dockerParams += "-e endpointToken=%s " % clientData["endpointToken"]
        dockerParams += "--add-host dockerhost:%s " % clientData["dockerHost"]

        #create the command line execution line
        dockerExecLine = "docker run  " + dockerParams + image
        print("running: " + dockerExecLine)
        p = subprocess.Popen(dockerExecLine, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        log = out.decode("utf-8")  + "\r\n" + err.decode("utf-8") 

        file = open(outputFilePath, 'r')
        responseText = file.read()
        file.close()

        # Read internal log file
        file = open(logFilePath, 'r')
        internalLog = file.read()
        file.close()

        responseData = {
            'response': str(responseText),
            'log': str(log) + "\r\n" + "=======================INTERNAL FILE LOG===================== \r\n" + internalLog
        }

        print(responseData)
        file = open(logFilePath, 'w')
        file.writelines(responseData["log"])
        file.close()

        # execute HTTP POST to send back result (response)
        # resp = requests.post(
        #     clientData["masterUrl"] + "/client/" + str(clientData["id"]) + "/task/" + str(taskId) + "/result/add",
        #     data=json.dumps(responseData), headers=headerData)
        # respObjResult = json.loads(resp.text)
        # print("resultId" + str(respObjResult["taskId"]))
        iTask += 1     