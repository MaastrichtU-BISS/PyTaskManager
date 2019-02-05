FROM python:3.7

RUN mkdir /app
COPY DbDao.py /app/DbDao.py
COPY TaskMaster.py /app/TaskMaster.py
COPY requirements.txt /app/requirements.txt
COPY config.json /app/config.json

WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "TaskMaster.py"]