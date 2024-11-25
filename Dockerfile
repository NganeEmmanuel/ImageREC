#FROM python:3.12-slim
#WORKDIR /app
#COPY requirements.txt requirements.txt
#COPY master.py master.py
#RUN pip install --no-cache-dir -r requirements.txt
#EXPOSE 5000
#CMD ["python", "master.py"]

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements.txt
COPY worker.py worker.py
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD ["python", "worker.py"]
