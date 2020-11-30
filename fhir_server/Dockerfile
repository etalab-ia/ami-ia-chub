FROM python:3.6-slim-buster

RUN mkdir -p /fhir_server
WORKDIR /fhir_server

COPY requirements.txt ./
RUN pip3 install -r requirements.txt

COPY src/ .

EXPOSE 5000

CMD ["python3", "web.py"]
