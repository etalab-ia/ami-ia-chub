#!/usr/bin/env bash

#########################
#  Run starclay/chub_neo4j
#
#  Options:
#     -g  --generate : runs the container in generate_db mode
#########################


# Transform long options to short ones
for arg in "$@"; do
  shift
  case "$arg" in
    "--generate") set -- "$@" "-g" ;;
    *)        set -- "$@" "$arg"
  esac
done

## get call arguments
RUN_GENERATE=0
while getopts :g option
do
	case "${option}"
	in
	g) RUN_GENERATE=1;;
	\?) echo "Option not supported: ${OPTARG}";;
	esac
done

START_COMMAND=""
if [[ "${RUN_GENERATE}" -eq "1" ]]; then
  START_COMMAND="generate_db"
fi

DOCKER_IMAGE_TAG="1.0.0"
DOCKER_INSTANCE_NAME="chub-neo4j"

# Ports Neo4j
FHIR_SERVER_HTTP_PORT=7474
FHIR_SERVER_FTP_PORT=7687

# Mapping data
FHIR_SERVER_DATA_DIR=$HOME/neo4j/data
FHIR_SERVER_LOGS_DIR=$HOME/neo4j/logs
FHIR_SERVER_PLUGINS_DIR=$HOME/neo4j/plugins

# Neo4j AUTH
FHIR_SERVER_NEO4J_LOGIN="neo4j"
FHIR_SERVER_NEO4J_PWD="test"

docker run \
    --name ${DOCKER_INSTANCE_NAME} \
    -p ${FHIR_SERVER_HTTP_PORT}:7474 -p ${FHIR_SERVER_FTP_PORT}:7687 \
    -d \
    -v "${FHIR_SERVER_DATA_DIR}":/data \
    -v "${FHIR_SERVER_LOGS_DIR}":/logs \
    -v "${FHIR_SERVER_PLUGINS_DIR}":/plugins \
    --env NEO4J_LOGIN="${FHIR_SERVER_NEO4J_LOGIN}" \
    --env NEO4J_PWD="${FHIR_SERVER_NEO4J_PWD}" \
    --env NEO4J_AUTH="${FHIR_SERVER_NEO4J_LOGIN}/${FHIR_SERVER_NEO4J_PWD}" \
    starclay/chub_neo4j:${DOCKER_IMAGE_TAG} ${START_COMMAND}
