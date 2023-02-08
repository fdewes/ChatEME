FROM nvidia/cuda:11.7.0-base-ubuntu22.04

ENV TZ=Etc/UTC
ENV DEBIAN_FRONTEND=noninteractive 

RUN apt-get update && apt-get dist-upgrade -y

RUN apt-get install -y python3-pip python3-setuptools python3-wheel git \
    python-is-python3 tzdata


RUN useradd -ms /bin/bash chateme
USER chateme
WORKDIR /home/chateme

RUN git clone https://github.com/fdewes/ChatEME.git
RUN pip3 install -r ChatEME/requirements.txt
RUN cd ChatEME/ChatEME; make init
RUN echo SECRET_KEY=\"`tr -dc A-Za-z0-9 </dev/urandom | head -c 50 ; echo ''`\" \
    >> ChatEME/ChatEME/ChatEME_app/settings.py

EXPOSE 8000
CMD ChatEME/ChatEME/manage.py runserver 0:8000