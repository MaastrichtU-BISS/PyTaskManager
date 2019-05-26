import os
import subprocess
import time
import threading
import json
import shutil

class JobServiceDocker:
    def __init__(self, taskDir, runIdDir, pullImagesFirst, endpointUrl, endpointType, endpointToken, dockerHostIp, sleepTime, inputOutputInstructions):
        self.__taskDir = taskDir
        self.__runIdDir = runIdDir
        self.__pullImagesFirst = pullImagesFirst
        self.__endpointUrl = endpointUrl
        self.__endpointType = endpointType
        self.__endpointToken = endpointToken
        self.__dockerHostIp = dockerHostIp
        self.__inputOutputInstructions = inputOutputInstructions
        self.__sleepTime = sleepTime

        if not os.path.exists(self.__taskDir):
            os.mkdir(self.__taskDir)
        if not os.path.exists(self.__runIdDir):
            os.mkdir(self.__runIdDir)
    
    def start(self):
        self.__myThread = threading.Thread(target=self.__execute__)
        self.__stopSignal = False
        self.__myThread.start()

    def stop(self):
        if self.__myThread.isAlive():
            self.__stopSignal = True
        
        while(self.__myThread.isAlive()):
            time.sleep(1)
        self.__myThread.join()

    def __execute__(self):
        while not self.__stopSignal:
            self.__runTaskList__()
            time.sleep(self.__sleepTime)

    def __readPtmInstructionsFolder__(self, rootDir):
        tasks = [ ]

        rootDir = rootDir

        if not os.path.exists(rootDir):
            os.mkdir(rootDir)

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
    
    def __getInstructions__(self):
        tasks = [ ]
        if self.__inputOutputInstructions["inputMethod"]=="folder":
            tasks = self.__readPtmInstructionsFolder__(self.__inputOutputInstructions["inputLocation"])
        return tasks
    
    def __handleExecutionResult__(self, taskFolderPaths, outputLog, taskId, tmpFolderPath):
        if self.__inputOutputInstructions["outputMethod"]=="folder":
            self.___handleExecutionResultFolder__(taskFolderPaths, outputLog, taskId, tmpFolderPath)
            return
        print("Result handling for outputMethod %s not found" % self.__inputOutputInstructions["outputMethod"])
        
    def ___handleExecutionResultFolder__(self, taskFolderPaths, outputLog, taskId, tmpFolderPath):
        text_file = open(taskFolderPaths["logFilePath"], "a")
        text_file.write(outputLog)
        text_file.close()

        ## create folder in output location
        if not os.path.exists(self.__inputOutputInstructions["outputLocation"]):
            os.mkdir(self.__inputOutputInstructions["outputLocation"])
        
        for fileType in self.__inputOutputInstructions["filesToOutput"]:
            if fileType=="logs":
                shutil.copyfile(taskFolderPaths["logFilePath"], os.path.join(self.__inputOutputInstructions["outputLocation"], "log.txt"))
            if fileType=="output":
                shutil.copytree(taskFolderPaths["outputFolderPath"], os.path.join(self.__inputOutputInstructions["outputLocation"], "output"))
                shutil.copyfile(taskFolderPaths["outputFilePath"], os.path.join(self.__inputOutputInstructions["outputLocation"], "output.txt"))
            if fileType=="tmpFolder":
                targetPath = os.path.join(self.__inputOutputInstructions["outputLocation"], "tmp")
                if os.path.exists(targetPath):
                    shutil.rmtree(targetPath)
                shutil.copytree(tmpFolderPath, targetPath)


    def __createTaskFolder__(self, taskId):
        curFolder = os.path.join(self.__taskDir, "task"+str(taskId))
        if not os.path.exists(curFolder):
            os.mkdir(curFolder)
        return curFolder
    
    def __createRunIdFolder__(self, runId):
        runIdFolder = os.path.join(self.__runIdDir, str(runId))
        if not os.path.exists(runIdFolder):
            os.mkdir(runIdFolder)
        return runIdFolder
    
    def __createInputOutputLogFiles__(self, taskFolderPath, inputText):
        inputFilePath = os.path.join(taskFolderPath,"input.txt")
        text_file = open(inputFilePath, "w")
        text_file.write(inputText)
        text_file.close()

        outputFilePath = os.path.join(taskFolderPath,"output.txt")
        text_file = open(outputFilePath, "w")
        text_file.write("")
        text_file.close()

        outputFolderPath = os.path.join(taskFolderPath, "output")
        if os.path.exists(outputFolderPath):
            os.rmdir(outputFolderPath)
        os.mkdir(outputFolderPath)

        logFilePath = os.path.join(taskFolderPath,"log.txt")
        text_file = open(logFilePath, "w")
        text_file.write("")
        text_file.close()

        return {
            "inputFilePath": inputFilePath,
            "outputFilePath": outputFilePath,
            "outputFolderPath": outputFolderPath,
            "logFilePath": logFilePath
        }

    def __createDockerCommand__(self, runId, taskFolderPaths, tmpFolderPath, image):
        if (self.__pullImagesFirst):
            subprocess.Popen("docker pull " + image, shell=True)
        
        dockerParams = "--rm " #container should be removed after execution
        dockerParams += "-v " + os.path.abspath(taskFolderPaths['inputFilePath']) + ":/input.txt " #mount input file
        dockerParams += "-v " + os.path.abspath(taskFolderPaths['outputFilePath']) + ":/output.txt " #mount output file
        dockerParams += "-v " + os.path.abspath(taskFolderPaths['outputFolderPath']) + ":/output " #mount output file
        dockerParams += "-v " + os.path.abspath(taskFolderPaths['logFilePath']) + ":/log.txt " #mount output file
        dockerParams += "-v " + os.path.abspath(tmpFolderPath) + "/:/temp/ " #mount runId folder
        dockerParams += "-e RUN_ID=%s " % str(runId)
        dockerParams += "-e SPARQL_ENDPOINT=%s " % self.__endpointUrl
        dockerParams += "-e endpointUrl=%s " % self.__endpointUrl
        dockerParams += "-e endpointType=%s " % self.__endpointType
        dockerParams += "-e endpointToken=%s " % self.__endpointToken
        dockerParams += "--add-host dockerhost:%s " % self.__dockerHostIp

        return "docker run  " + dockerParams + image

    def __runDockerCommand__(self, dockerExecLine):
        # Run the actual script
        p = subprocess.Popen(dockerExecLine, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        log = out.decode("utf-8")  + "\r\n" + err.decode("utf-8") 
        
        return log

    def __runTaskList__(self):
        taskList = self.__getInstructions__()

        iTask = 0
        while iTask < len(taskList):
            myTask = taskList[iTask]
            taskId = myTask.get('id')
            image = myTask.get('image')
            runId = myTask.get('runId')
            inputText = myTask.get("input")

            taskFolderPaths = self.__createTaskFolder__(taskId)
            tmpFolderPath = self.__createRunIdFolder__(runId)

            taskFiles = self.__createInputOutputLogFiles__(taskFolderPaths, inputText)

            dockerCommand = self.__createDockerCommand__(runId, taskFiles, tmpFolderPath, image)
            outputLog = self.__runDockerCommand__(dockerCommand)

            self.__handleExecutionResult__(taskFiles, outputLog, taskId, tmpFolderPath)

            iTask = iTask + 1