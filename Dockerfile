FROM alpine:3.4

# Update
RUN apk add --update python py-pip openssl patch bash

# Install dependencies
COPY requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt

# Install scripts
WORKDIR /dell
COPY . /dell/

# Patch rac module with better ssl support
RUN /bin/bash start.sh
