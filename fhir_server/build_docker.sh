#!/usr/bin/env bash

########################
#  Build docker
#
#  basic : creates starclay/fhir_api_server:latest
#######################

echo "Building CPU version"
docker build -t starclay/fhir_api_server:latest .