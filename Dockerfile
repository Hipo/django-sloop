FROM ubuntu:18.04

# Needed to be able to install python versions.
RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa

RUN apt-get update && apt-get install -y \
	python3.5 \
	python3.6 \
	python3.7 \
	libpq-dev \
	gdal-bin \
	python3-distutils \
	python-pip

WORKDIR /app

COPY requirements.txt .
COPY requirements_dev.txt .

RUN pip install --upgrade pip
RUN pip install tox
RUN pip install -r requirements_dev.txt