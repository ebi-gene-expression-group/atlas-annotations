#!/usr/bin/env bash

PATH_BIOENTITY_PROPERTIES=$ATLAS_PROD/bioentity_properties
PROJECT_ROOT=$(realpath $(dirname $0)/../..)

export SINGULARITYENV_PREPEND_PATH=$PROJECT_ROOT/sh/ensembl
export SINGULARITYENV_ATLAS_PROD=$ATLAS_PROD
export SINGULARITYENV_GET_GO_DEPTHS=${GET_GO_DEPTHS:-"no"}
export SINGULARITYENV_USE_EXISTING_ONTOLOGY_FILES=${USE_EXISTING_ONTOLOGY_FILES:-"no"}
export SINGULARITYENV_EXPERIMENT_SOURCES=$EXPERIMENT_SOURCES

# Note: This uses the generic Python image. For production, consider building
# a custom image based on python:3.9-slim with the requirements.txt pre-installed
# and all necessary dependencies (mysql-client, etc.) for the full pipeline.
singularity exec \
  --bind $PATH_BIOENTITY_PROPERTIES,$PROJECT_ROOT \
  docker://python:3.9-slim ensemblUpdate.sh $@
