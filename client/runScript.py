import json
import requests
import time
import os
import subprocess

# connect to service
headerData = {
    'Content-Type': "application/json"
}

# Init configuration file
configFile = open("config.json")
clientData = json.load(configFile)
configFile.close()

if "id" not in clientData:
    # execute HTTP POST to try and authenticate
    resp = requests.post(clientData["masterUrl"] + "/client/add", data=json.dumps(clientData), headers=headerData)
    respObj = json.loads(resp.text)
    clientId = respObj.get('clientId', '')
    clientData["id"] = clientId
    configFile = open("config.json", "w")
    json.dump(clientData, configFile)
    configFile.close()

print("Starting with client ID " + str(clientData["id"]))

taskDir = "tasks"
if not os.path.exists(taskDir):
    os.mkdir(taskDir)

runIdDir = "runIds"
if not os.path.exists(runIdDir):
    os.mkdir(runIdDir)

ioVolumeFolder = clientData["dockerSettings"]["inputOutputFolderPath"]
ioVolumeName = clientData["dockerSettings"]["inputOutputVolumeName"]

if not os.path.exists(ioVolumeFolder):
    print("ioVolumeFolder does not exist!")

abort = 0

while abort == 0:
    taskList = list()

    # Connect to central host, if fails do nothing
    try:
        resp = requests.get(clientData["masterUrl"] + "/client/" + str(clientData["id"]) + "/task")
        taskList = json.loads(resp.text)
    except:
        print("Could not retrieve result from master.")

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

        #put the input arguments in a text file
        inputFilePath = os.path.join(ioVolumeFolder,"input.txt")
        text_file = open(inputFilePath, "w")
        text_file.write(inputText)
        text_file.close()

        outputFilePath = os.path.join(ioVolumeFolder,"output.txt")
        text_file = open(outputFilePath, "w")
        text_file.write("")
        text_file.close()

        logFilePath = os.path.join(ioVolumeFolder,"log.txt")
        text_file = open(logFilePath, "w")
        text_file.write("")
        text_file.close()

        #pulling the image for updates or download
        subprocess.Popen("docker pull " + image, shell=True)

        tmpVolume = "tmp_" + str(runId)
        subprocess.Popen("docker volume create " + tmpVolume, shell=True)

        dockerParams = "--rm " #container should be removed after execution
        dockerParams += "-v " + ioVolumeName + ":/input_output " #mount input file
        dockerParams += "-v " + tmpVolume + ":/tmp " #mount runId folder
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

        # execute HTTP POST to send back result (response)
        resp = requests.post(
            clientData["masterUrl"] + "/client/" + str(clientData["id"]) + "/task/" + str(taskId) + "/result/add",
            data=json.dumps(responseData), headers=headerData)
        respObjResult = json.loads(resp.text)
        print("resultId" + str(respObjResult["taskId"]))
        iTask += 1
