FROM ubuntu:18.04

# Install dependent packages
RUN apt-get update && apt-get install -y curl unzip wget python python-pip

# Install docker
RUN curl -s https://raw.githubusercontent.com/jvsoest/UnixSettings/master/installDockerFromRoot.sh | sh

# Download PyTaskManager latest master
RUN wget https://github.com/PersonalHealthTrain/PyTaskManager/archive/master.zip
RUN unzip master.zip

# Install python dependencies
RUN pip install requests flask

# Add the run script
COPY docker_run.sh /run.sh

# Make these ports available to the outside world
EXPOSE 5000
EXPOSE 5001

# Set run script as default locations
CMD ["sh", "run.sh"]