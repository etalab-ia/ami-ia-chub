#! /bin/bash

echo -e "\e[1m\e[32mDB GENERATION - waiting 10s for neo4j start\e[0m"
sleep 10s

echo -e "\e[1m\e[32mDB GENERATION - Starting db generation\e[0m"

function insert_file {
  file_name=$1

  echo -e "\e[1m\e[32mDB GENERATION - Adding ${file_name}\e[0m"
  cypher-shell -u "${NEO4J_LOGIN}" -p "${NEO4J_PWD}" < /var/lib/neo4j/import/db_generation/${file_name}.cypher
  return_code=$?
  if [ ${return_code} -eq 0 ]
  then
    echo -e "\e[1m\e[32mDB GENERATION - ... ${file_name} added\e[0m"
  else
    echo "\e[1m\e[31mDB GENERATION - error inserting ${file_name}\e[0m"
    exit ${return_code}
  fi
}

insert_file add_diseases
insert_file add_biology
insert_file add_specialties
insert_file add_symptoms
insert_file add_medoc
insert_file add_drugclass
insert_file add_ingredient
insert_file add_brand_name
echo -e "\e[1m\e[32mDB GENERATION - ... DB finalized\e[0m"
