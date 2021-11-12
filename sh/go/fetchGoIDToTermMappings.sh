#!/usr/bin/env bash
# This script retrieves the latest mapping between GO ids and terms
# Author: rpetry@ebi.ac.uk, wbazant@ebi.ac.uk
set -euo pipefail

PROJECT_ROOT=`dirname $0`/../..
export JAVA_OPTS=-Xmx3000M

# To avoid using the depths functionality, set env var $GET_GO_DEPTHS to something different to "yes".
GET_GO_DEPTHS=${GET_GO_DEPTHS:-"yes"}
USE_EXITING_ONTOLOGY_FILES=${USE_EXISTING_ONTOLOGY_FILES:-"no"}

IFS="
"
outputDir=$1
if [[ -z "$outputDir" ]]; then
    echo "Usage: $0 outputDir"  >&2
    exit 1
fi

source $PROJECT_ROOT/sh/util_functions.sh

echo "Fetching GO and PO owl files"
if [ $USE_EXISTING_ONTOLOGY_FILES == "no" ]; then
  download_file "http://current.geneontology.org/ontology/go.owl" $outputDir/go.owl
  download_file "http://purl.obolibrary.org/obo/po.owl" $outputDir/po.owl
fi

echo "Extracting GO id -> term"
amm -s $PROJECT_ROOT/src/go/PropertiesFromOwlFile.sc terms $outputDir/go.owl \
    > $outputDir/goIDToTerm.tsv

echo "Extracting PO id -> term"
# Plant ontology now comes in UTF-8
export JAVA_OPTS="-Dfile.encoding=utf8 -Xmx3000M"
amm -s $PROJECT_ROOT/src/go/PropertiesFromOwlFile.sc terms $outputDir/po.owl \
    > $outputDir/poIDToTerm.tsv

echo "Extracting GO alternativeId -> id"
export JAVA_OPTS=-Xmx3000M
amm -s $PROJECT_ROOT/src/go/PropertiesFromOwlFile.sc alternativeIds $outputDir/go.owl \
    > $outputDir/go.alternativeID2CanonicalID.tsv


# This is just for GO (i.e. not PO)
# GO Consortium no longer publish a MySQL version of their data;
# using EBI's GOA database for GO graph distance between any two GO terms is used for mapping depth for any GO term
get_ontology_id2Depth_mappings() {
echo "select
    go_id, min(distance) min_distance
from
    (
        select
            level distance, connect_by_root child_id go_id, parent_id ancestor_id
        from
            (
                select
                    child_id, parent_id
                from
                    go.relations
                where
                    --relation_type in ('I', 'P', 'O')
                    relation_type = 'I'
            )
        connect by
            child_id = prior parent_id
    union all
        select
            0 distance, go_id, go_id ancestor_id
        from
            go.terms
        where
            is_obsolete = 'N'
    )
group by go_id, ancestor_id;" | sqlplus goselect/selectgo@goapro | grep '^GO:'  | sort -t$'\t' -rk2,2  | awk -F"\t" '{ print $1"\t"$2+1 }' | sort -buk1,1
}

if [ $GET_GO_DEPTHS == "yes" ]; then
  get_ontology_id2Depth_mappings > $outputDir/goIDToDepth.tsv
else
  # write file with just zero depths
  echo "As requested, ignoring GO depths and writing dummy file with all depths 0 based on $outputDir/goIDToTerm.tsv ."
  awk -F'\t' '{ print $1"\t0" }' $outputDir/goIDToTerm.tsv > $outputDir/goIDToDepth.tsv
fi


# Append Plant Ontology terms at the end of the Gene Ontology file (Ensembl provides Plant Ontology (PO) and Gene Ontology (GO) terms - as GO terms)
cat $outputDir/poIDToTerm.tsv >> $outputDir/goIDToTerm.tsv
rm -rf $outputDir/poIDToTerm.tsv

join -t $'\t' -a 1 -1 1 -2 1 $outputDir/goIDToTerm.tsv $outputDir/goIDToDepth.tsv > $outputDir/goIDToTermDepth.tsv
rm -rf $outputDir/goIDToDepth.tsv
mv $outputDir/goIDToTermDepth.tsv $outputDir/goIDToTerm.tsv

# this 'thin' file is needed for GSEA plots as irap_GSE_piano expects two column annotations
cut -d $'\t' -f 1,2 $outputDir/goIDToTerm.tsv > $outputDir/goIDToTerm.tsv.decorate.aux
