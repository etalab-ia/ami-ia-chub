#! /bin/bash -eu

cmd="$1"

#echo "neo4j login is ${NEO4J_LOGIN}"
#echo "neo4j NEO4J_PWD is ${NEO4J_PWD}"
#echo "neo4j NEO4J_AUTH is ${NEO4J_AUTH}"
#echo "script arg is ${cmd}"

if [ "${cmd}" == "generate_db" ]; then
  /var/lib/neo4j/import/db_generation.sh &
fi

/sbin/tini -g -- /docker-entrypoint.sh neo4j

