FROM ubuntu:18.04

# Install dependent packages
RUN apt-get update && apt-get install -y curl unzip wget python python-pip

# Install docker
RUN curl -s https://raw.githubusercontent.com/jvsoest/UnixSettings/master/installDockerFromRoot.sh | sh

# Download PyTaskManager latest master
RUN mkdir /ptm_client
COPY config.json /ptm_client/config.json
COPY FileService.py /ptm_client/FileService.py
COPY requirements.txt /ptm_client/requirements.txt
COPY runScript.py /ptm_client/runScript.py
COPY docker_run.sh /run.sh

# Install python dependencies
RUN cd ptm_client && pip install -r requirements.txt

# Make these ports available to the outside world
EXPOSE 5001

# Set run script as default locations
CMD ["sh", "run.sh"]
