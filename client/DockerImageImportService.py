import threading
import os
import subprocess
import time

class DockerImageImportService:
    def __init__(self, folderPath, sleepTime):
        self.__folderPath = folderPath
        self.__sleepTime = sleepTime
    
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
            self.__importImagesFromFolder(self.__folderPath)
            time.sleep(self.__sleepTime)

    def __readDockerImages(self, rootDir = "myFiles"):
        returnList = [ ]
        for dirName, subdirList, fileList in os.walk(rootDir):
            for fname in fileList:
                if(fname.endswith(".dockerimage")):
                    returnList.append(os.path.join(dirName, fname))

        return returnList

    def __importImage(self, imagePath):
        cmdString = "docker load -i " + imagePath
        p = subprocess.Popen(cmdString, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        if(len(err)>0):
            print(err)
            return False
        return True

    def __importImagesFromFolder(self, rootDir = "myFiles"):
        dockerImages = self.__readDockerImages(rootDir)
        for imagePath in dockerImages:
            success = self.__importImage(imagePath)
            if success:
                os.remove(imagePath)