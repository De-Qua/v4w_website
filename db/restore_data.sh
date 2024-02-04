#!/bin/bash

CUR_DIR=$(dirname "$0")
declare -A DUMP_FILES
DUMP_FILES[opendata_ve_pg]="opendata.sql" 
DUMP_FILES[dequa_internal]="internal.sql" 
DUMP_FILES[dequa_collected_data]="collected.sql" 
DUMP_FILES[dequa_config_data]="config.sql" 

CONTAINER_NAME=dq_postgres
POSTGRES_USER=dequa

DUMP_DIR=$CUR_DIR/db_dump

for db in "${!DUMP_FILES[@]}"
do
    file=${DUMP_FILES[$db]}
    echo "Copying $file in docker"
    docker cp $DUMP_DIR/$file $CONTAINER_NAME:/tmp/
    echo "Restoring db $db"
    docker exec -it $CONTAINER_NAME psql -U $POSTGRES_USER -f /tmp/$file $db
done