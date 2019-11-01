FROM python:3-stretch

ADD . /ptm

RUN curl -sSL https://get.docker.com | sh

WORKDIR /ptm

RUN pip install -r requirements.txt

CMD ["python", "runScript.py"]