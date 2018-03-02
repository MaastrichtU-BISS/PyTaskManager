# PyTaskManager

License: [Apache 2.0](./LICENSE)

## Introduction
This package contains the software to run the open-source Personal Health Train and/or Distributed learning infrastructure. This infrastructure can be setup between different collaborative partners who do trust each other.

## How does it work?
This infrastructure builds on the concept of a public registry of tasks (e.g. jobs), encapsulated in Docker images. This registry **only** holds a reference to a docker container (e.g. `hello-world:latest`), and a configuration file which can be used how the docker container developer envisioned. Results of containers are stored again in this registry.

Next to this registry, there is a client, which polls a central registry, to check for new tasks to execute. If a new task is available, the referenced container is pulled from the docker hub (e.g. `docker pull <container name>`) irrespective of whether it was pulled before. Afterwards, this container is executed (e.g. `docker run --rm -d <container name>`), with mounts for configuration files and output folders. Furthermore, the *internal* SPARQL endpoint URL is passed to the container as an environment variable (`$SPARQL_ENDPOINT=<url>`).

This means the researcher is free to implement any application/script, embedded in a docker container. Sites running the client are able to limit the docker containers being able to run on their system. It is possible to limit the user/organization which developed the container (e.g. only allowing the regular expression `myConsortium/.*:.*` of container images), or even on the repository level (e.g. `myConsortium/myImage:.*`).

# How to use it?

## Prerequisites

At the (hospital) site:

* A Windows Server 2012R2 (or higher) machine, or a unix machine supporting Docker
* Docker installed, and given rights to the user executing the client rights to perform docker commands
* Python 2.7 or 3 (tested on both)

At the central registry:

* A Windows Server 2012R2 (or higher) machine, or a unix machine supporting Docker
* Docker installed, and given rights to the user executing the client rights to perform docker commands
* Python 2.7 or 3 (tested on both)

## How to run?

In general:

1. Checkout this repository
2. Go to the checked out repository folder
3. Run `pip install -e .`

At the central registry:

1. Run `ptm server load_fixtures` to create API keys
2. Run the server using `ptm server start`

At the (hospital) sites:

1. Create a yaml file containing your local configuration. The example yaml can be found in `pytaskmanager/_data/client_config_skeleton.yaml`
2. Fill in the config file the API key, received from the server
3. Run the client using `ptm client start --config=<path_to_config.yaml>`


## How to build and run an algorithm?

The registry is based on REST commands. The docker containers are *only* needed for execution at the sites. As a researcher, this means you have to develop a docker container which can run on *every* site.

To merge results from all sites, and to run the *centralised* part of your analysis, you can develop a script on your own computer. This computer can retrieve the results from the registry, perform its calculations, and (optionally, in an iterative algorithm) post a new request to run an image on the contributing sites. This can also be the same Docker image, using an updated configuration file.

# How to contribute?
If you have any requests, you can fork this repository, develop the addition/change, and send a pull request (using the [Gitflow workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)). If you have a request for a change, please add it to the issue tracker (see "Issues" in the left navigation bar).

This readme and documentation still needs work, as the code for this infrastructure is still work in progress. If you have any question regarding use, please use the issue tracker as well. We might update the readme file accordingly, but also helps us to define where the need for help is.