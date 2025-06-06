#!/bin/bash
# A script to increment release numbers in annotation source config files for ensembl and ensemblgenoms to $ENSEMBL_RELNUM and $ENSEMBLGENOMES_RELNUM respectively
# Author: rpetry@ebi.ac.uk, spruced up by wbazant@ebi.ac.uk

function update {
  filterPhrase=software.name=$1
  updateCommand="s|software.version=\d+$|software.version=${2}|"
  dir=$3

   find $dir -type f -exec grep -l $filterPhrase {} \; | xargs perl -pi -e $updateCommand  
}

if [ $# -lt 4 ]; then
  echo "Usage: $0 ENSEMBL_RELNUM ENSEMBLGENOMES_RELNUM WBPS_RELNUM ENSEMBL_PROTISTS"
	echo "e.g. $0 86 34 8 7"
  exit 1;
fi
scriptDir=`dirname $0`/../annsrcs

if [ $(git diff --name-only --cached | wc -l ) != 0 ] ; then
 echo "Dirty worktree: "
 git diff --name-only --cached
else
  update "ensembl" $1 $scriptDir
  update "plants" $2 $scriptDir
  update "metazoa" $2 $scriptDir
  update "fungi" $2 $scriptDir
  update "protists" $4 $scriptDir
  update "parasite" $2 $scriptDir # now fetched from Ensembl Genomes 
  git commit $scriptDir -m "Update release numbers- Ensembl $1 EnsemblGenomes $2 E!Protists $4 Wormbase $3"
fi
