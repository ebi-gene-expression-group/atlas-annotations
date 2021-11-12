#!/usr/bin/env bash

# This script retrieves the latest mapping between Interpro ids and their types (family/domain) and terms
# Author: rpetry@ebi.ac.uk
PROJECT_ROOT=`dirname $0`/../..

outputDir=$1
if [[ -z "$outputDir" ]]; then
    echo "Usage: $0 outputDir"  >&2
    exit 1
fi

source $PROJECT_ROOT/sh/util_functions.sh

INTERPRO_VERSION=${INTERPRO_VERSION:-"62.0"}

download_file http://ftp.ebi.ac.uk/pub/databases/interpro/$INTERPRO_VERSION/interpro.xml.gz $outputDir/interpro.xml.gz
zcat $outputDir/interpro.xml.gz > $outputDir/interpro.xml && rm $outputDir/interpro.xml.gz
download_file http://ftp.ebi.ac.uk/pub/databases/interpro/$INTERPRO_VERSION/interpro.dtd $outputDir/interpro.dtd

pushd $PROJECT_ROOT
echo "Parse the file we obtained from Interpro's FTP site"
export JAVA_OPTS="-Dfile.encoding=utf8 -Xmx3000M"
amm -s -c "import \$file.src.interpro.Parse; Parse.main(\"$outputDir/interpro.xml\")" > $outputDir/interproIDToTypeTerm.tsv.tmp
if [ $? -ne 0 ]; then
    echo "Ammonite errored out, exiting..." >&2
    exit 1
fi
popd
echo "Regenerate Interpro files"
mv $outputDir/interproIDToTypeTerm.tsv.tmp $outputDir/interproIDToTypeTerm.tsv
cat $outputDir/interproIDToTypeTerm.tsv | awk -F"\t" '{print $2"\t"$1}' | sort -k1,1 -t$'\t' > $outputDir/interproIDToTypeTerm.tsv.decorate.aux
