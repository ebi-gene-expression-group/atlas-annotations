#!/usr/bin/env bash

host_port=$(grep 'mySqlDbUrl' $config_file | awk -F'=' '{ print $2 }')
MYSQL_HOST=$(echo $host_port | awk -F':' '{ print $1 }')
MYSQL_PORT=$(echo $host_port | awk -F':' '{ print $2 }')
SOFTWARE_VERSION=$(grep 'software.version' $config_file | awk -F'=' '{ print $2 }')

MYSQL_DB_NAME=$(grep 'mySqlDbName' $config_file | awk -F'=' '{ print $2 }')"_core_"$SOFTWARE_VERSION

if [[ $type =~ ensembl ]]; then
    MYSQL_USER=anonymous
elif [[ $type =~ wbps ]]; then
    MYSQL_USER=ensro
else
    echo "ERROR: for $config_file: unknown annotator: $type" >&2
    exit 1
fi


echo "mysql -u $MYSQL_USER --port $MYSQL_PORT -h $MYSQL_HOST"
echo "SHOW DATABASES LIKE '$MYSQL_DB_NAME%'"

latestReleaseDB=$(mysql -s -u $MYSQL_USER --port $MYSQL_PORT -h $MYSQL_HOST -e "SHOW DATABASES LIKE '$MYSQL_DB_NAME%'" | grep "^$MYSQL_DB_NAME")

if [ -z "$latestReleaseDB" ]; then
    echo "ERROR: for $annSrc: Failed to retrieve the database name for release number: $softwareVersion" >&2
    exit 1
else
    echo "Database found: "$latestReleaseDB
fi
