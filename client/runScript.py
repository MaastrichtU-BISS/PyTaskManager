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

inputOutputOptions = {
    "inputMethod": "folder",
    "inputLocation": "myFiles",
    "outputMethod": "folder",
    "outputLocation": "myFilesOut",
    "filesToOutput": ["logs", "output"]
}
jsd = JobServiceDocker("tasks", "runIds", True, "http://dockerhost:7200/repositories/data/sparql", "SPARQL", "", "172.10.0.1", 5, inputOutputOptions)

import signal
import sys
def signal_handler(sig, frame):
    print("stop!")
    diis.stop()
    jsd.stop()
signal.signal(signal.SIGINT, signal_handler)

diis.start()
jsd.start()