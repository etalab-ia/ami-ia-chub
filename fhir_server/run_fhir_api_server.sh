#!/usr/bin/env bash

#########################
#  Run docker
#
#  Options:
#     --bash : runs the container with bash as entrypoint
#     --port : configure port
#########################


# Transform long options to short ones
for arg in "$@"; do
  shift
  case "$arg" in
    "--bash") set -- "$@" "-b" ;;
    "--port") set -- "$@" "-p" ;;
    *)        set -- "$@" "$arg"
  esac
done

## get call arguments
RUN_BASH=0
PORT=5000
while getopts :bp: option
do
	case "${option}"
	in
	b) RUN_BASH=1;;
	p) PORT=${OPTARG};;
	\?) echo "Option not supported: ${OPTARG}";;
	esac
done

CONTAINER=starclay/fhir_api_server:latest

APP_LOG_LEVEL=DEBUG

POSTGRESQL_HOST="localhost:5432"
POSTGRESQL_DBNAME="chu-bordeaux"
POSTGRESQL_USER="admin"
POSTGRESQL_PWD="admin"

SPARQL_HOST="http://localhost:8888/sparql-endpoint"


if [[ "${RUN_BASH}" -eq "1" ]]; then
    docker run -it \
            -p $PORT:5000 \
            -e APP_LOG_LEVEL=${APP_LOG_LEVEL} \
            -e POSTGRESQL_HOST=${POSTGRESQL_HOST} \
            -e POSTGRESQL_DBNAME=${POSTGRESQL_DBNAME} \
            -e POSTGRESQL_USER=${POSTGRESQL_USER} \
            -e POSTGRESQL_PWD=${POSTGRESQL_PWD} \
            -e SPARQL_HOST=${SPARQL_HOST} \
            ${CONTAINER} bash
else
    docker run \
            -p $PORT:5000 \
            --network="host" \
            -e APP_LOG_LEVEL=${APP_LOG_LEVEL} \
            -e POSTGRESQL_HOST=${POSTGRESQL_HOST} \
            -e POSTGRESQL_DBNAME=${POSTGRESQL_DBNAME} \
            -e POSTGRESQL_USER=${POSTGRESQL_USER} \
            -e POSTGRESQL_PWD=${POSTGRESQL_PWD} \
            -e SPARQL_HOST=${SPARQL_HOST} \
            ${CONTAINER}
fi



#docker run -it --cpus=4 --gpus all -p 8888:8888 -p 27017:27017 octave_intent_matcher:latest bash