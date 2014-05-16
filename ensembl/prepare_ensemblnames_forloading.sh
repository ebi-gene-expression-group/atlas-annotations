# This script geneartes sqlloader file for bioentity_name table, containing Ensmebl genes, using $dir/../bioentityOrganisms.dat as the organism reference

dir="/nfs/ma/home/atlas3-production/bioentity_properties/ensembl"

IFS="
"
pushd $dir
out=geneName.dat
rm -rf $out
for f in $(ls *.ensgene.symbol.tsv); do
    prettyOrganism=`echo $f | awk -F"." '{print $1}' | sed 's/.*/\u&/' | tr "_" " "`
    organismId=`grep "${prettyOrganism}$" $dir/../bioentityOrganism.dat | awk -F"\t" '{print $1}'`
    if [ -z "$organismId" ]; then
	echo "ERROR: Could not retrieve organismid for '$prettyOrganism'" >&2
	exit 1
    fi
    
    IFS=$'\t'
    cat $f | while read identifier name; do 
	if [ ! -z "$name" ]; then 
	    echo -e "${identifier}\t${organismId}\tgene\t${name}"
	else 
	    echo -e "${identifier}\t${organismId}\tgene"
	fi
    done
    IFS="
"
done > $out
popd
exit 0
