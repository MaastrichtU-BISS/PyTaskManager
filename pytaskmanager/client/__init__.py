#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import sys, os

import json
import requests
import time, datetime
import subprocess

import logging
import jwt
from pprint import pprint

from pytaskmanager import util
from pytaskmanager.util.jsdict import JSDict


module_name = __name__.split('.')[-1]
log = logging.getLogger(module_name)


class AuthenticationError(Exception):

    def __init__(self, message):
        self.message = message



class TaskMasterClient(object):

    def __init__(self, ctx):
        """Initialize a new TaskMasterClient instance."""
        self.ctx = ctx
        self.name = ctx.instance_name
        self.config = ctx.config['app']

        self._HOST = self.config['server_url']
        self._REFRESH_URL = ''

        self.client_id = None
        self._access_token = None
        self._refresh_token = None

    def refresh_token(self):
        log.info('Refreshing token')

        url = '{}{}'.format(self._HOST, self._REFRESH_URL)
        response = requests.post(url, headers={'Authorization': 'Bearer ' + self._access_token})
        response_data = response.json()

        if response.status_code != 200:
            msg = response_data.get('message')
            raise AuthenticationError(msg)

        self._access_token = response_data['access_token']

    def request(self, url, json_data=None, method='get'):
        """Performs a PUT by default is json_data is provided without method."""
        headers = {
            'Authorization': 'Bearer ' + self._access_token,
        }

        full_url = '{baseURL}{path}'.format(
            baseURL=self._HOST,
            path=url,
        )

        if method == 'put' or json_data:
            response = requests.put(full_url, json=json_data, headers=headers)
        elif method == 'post':
            response = requests.post(full_url, json=json_data, headers=headers)
        else:
            response = requests.get(full_url, headers=headers)

        response_data = response.json()

        if response.status_code != 200:
            msg = response_data.get('message')
            log.warning('Request failed: {}'.format(msg))
            self.refresh_token()
            log.info('Retrying ...')
            return self.request(url, json_data, method)

        return response_data

    def authenticate(self):
        """Authenticate with the server using the api-key."""
        url = '{}/api/token'.format(self._HOST)
        data = {'api_key': self.config['api_key']}

        response = requests.post(url, json=data)

        if response.status_code != 200:
            msg = response.text
            raise AuthenticationError(msg)
        
        response_data = response.json()

        self._access_token = response_data['access_token']
        self._refresh_token = response_data['refresh_token']
        self._REFRESH_URL = response_data['refresh_url']

        decoded_token = jwt.decode(self._access_token, verify=False)
        self.client_id = decoded_token['identity']

        # log.debug("Access token: {}".format(self._access_token))
        log.info("Authentication succesful!")
        log.debug("Found client_id: {}".format(self.client_id))

        client = self.request(response_data['client_url'])
        log.info("Client name: '{name}'".format(**client))
        # log.info("Client for: '{name}'".format(**client))

    def get_tasks(self):
        """Retrieve a list of tasks from the server."""
        url = '/api/result?state=open&include=task&client_id={client_id}'
        url = url.format(client_id=self.client_id)
        return self.request(url)

    def get_and_execute_tasks(self):
        """Continuously check for tasks and execute them."""

        # Get tasks actually returns a list of taskresults where
        # result == null
        taskresults = self.get_tasks()

        log.info("Received {} task(s)".format(len(taskresults)))

        for taskresult in taskresults:
            self.execute_task(taskresult)

        # Sleep 10 seconds
        log.debug("Sleeping {} second(s)".format(self.config['delay']))
        time.sleep(self.config['delay'])

    def make_task_dir(self, task):

        # task_dir = util.getFileLocation(filename, self.config, name, 'client', DIRS)
        task_dir = self.ctx.get_file_location('data', "task-{0:09d}".format(task['id']))
        log.info("Using '{}' for task".format(task_dir))
        if os.path.exists(task_dir):
            log.warning("Task directory already exists: '{}'".format(task_dir))

        else:
            try:
                os.makedirs(task_dir)
            except Exception as e:
                log.error("Could not create task directory: {}".format(task_dir))
                log.exception(e)
                raise

        return task_dir

    def docker_pull(self, task):
        log.info("Pulling latest version of docker image '{}'".format(task['image']))
        p = subprocess.Popen("docker pull " + task['image'], subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        out, err = p.communicate()
        log.info(out)

    def docker_run(self, task, inputFilePath, outputFilePath):
        # FIXME: need to check for running docker daemon and/or other error messages!

        # Prepare files for input/output.
        with open(inputFilePath, 'w') as fp:
            fp.write(task['input'] or '')

        with open(outputFilePath, 'w') as fp:
            fp.write('')

        # Prepare shell statement for running the docker image
        dockerParams = "--rm " # container should be removed after execution
        dockerParams += "-v " + inputFilePath.replace(' ', '\ ') + ":/app/input.txt "   # mount input file
        dockerParams += "-v " + outputFilePath.replace(' ', '\ ') + ":/app/output.txt " # mount output file
        dockerParams += "-e DATABASE_URI=%s " % self.config['database_uri']
        dockerParams += "--add-host dockerhost:%s" % self.config['docker_host']

        dockerExecLine = "docker run  " + dockerParams + ' ' + task['image']
        log.info("Executing docker: {}".format(dockerExecLine))

        # FIXME: consider using subprocess.run(...)
        # https://docs.python.org/3/library/subprocess.html#module-subprocess
        p = subprocess.Popen(dockerExecLine, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

        # This blocks until the process finishes.
        out, err = p.communicate()
        log_data = out.decode("utf-8") # + "\r\n" + err.decode("utf-8") 
        log.info(log_data)

        if p.returncode:
            raise Exception('did not succeed in running docker!?')


        with open(outputFilePath) as fp:
            result_text = fp.read()
            log.info(result_text)

        return result_text, log_data

    def execute_task(self, taskresult):
        task = taskresult['task']

        log.info("-" * 80)
        log.info("Starting task {id} - {name}".format(**task))
        log.info("-" * 80)

        # Notify the server we've started .. 
        result_data = {
            'started_at': datetime.datetime.now().isoformat(),
        }

        path = taskresult['_id']
        response = self.request(path, json_data=result_data, method='put')
        log.debug(response)

        
        # Create directory to put files into
        task_dir = self.make_task_dir(task)

        # Pull the image for updates or download
        self.docker_pull(task)

        # Files are used for input and output
        inputFilePath = os.path.join(task_dir, "input.txt")
        outputFilePath = os.path.join(task_dir, "output.txt")

        result_text, log_data = self.docker_run(task, inputFilePath, outputFilePath)

        result_data = {
            'result': result_text,
            'log': log_data,
            'finished_at': datetime.datetime.now().isoformat(),
        }

        # Do an HTTP PUT to send back result (response)
        log.info('PUTing result to server')
        response = self.request(path, json_data=result_data, method='put')

        log.info("-" * 80)
        log.info("Finished task {id} - {name}".format(**task))
        log.info("-" * 80)
        log.info('')

    def run_forever(self):
        """Run!"""
        self.authenticate()

        while True:
            self.get_and_execute_tasks()


# ------------------------------------------------------------------------------
def run(ctx):
    """Run the client."""
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    tmc = TaskMasterClient(ctx)
    tmc.run_forever()



