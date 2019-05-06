import json
import time
import os
import subprocess
import threading
from DockerImageImportService import DockerImageImportService
from JobServiceDocker import JobServiceDocker

# connect to service
headerData = {
    'Content-Type': "application/json"
}

print("active threads: %s" % threading.activeCount())

# Init configuration file
configFile = open("config.json")
clientData = json.load(configFile)
configFile.close()

diis = DockerImageImportService("myFiles", 5)

jsd = JobServiceDocker("tasks", "runIds", True, clientData["endpointUrl"], clientData["endpointType"], clientData["endpointToken"], clientData["dockerHost"], clientData["interval"], clientData["inputOutputOptions"])

import signal
import sys
def signal_handler(sig, frame):
    print("stop!")
    diis.stop()
    jsd.stop()
signal.signal(signal.SIGINT, signal_handler)

diis.start()
jsd.start()