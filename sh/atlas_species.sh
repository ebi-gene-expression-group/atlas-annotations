#!/bin/bash
# This script creates the species file for Expression Atlas based on bioentity annotations

target=${1:-`pwd`/species-properties.json}

python3 `dirname $0`/../src/atlas/atlas_species.py > $target

if [ -s $target ]
then
  echo "Generated species file at " $target
else
  rm $target
fi
