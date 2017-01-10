#!/bin/bash

IFS="
"
# Send Report
send_report() {
    log=$1
    email=$2
    subject=$3
    label=$4
    if [ -z "$label" ]; then
	label="atlas3"
    fi
    numOfNonEmptyLinesInReport=`egrep -v '^$' ${log}.report | wc -l`
    if [ $numOfNonEmptyLinesInReport -gt 0 ]; then 
        today="`eval date +%Y-%m-%d`"
        mailx -s "[$label/cron] Process new experiments for $today: $subject" $email < ${log}.report
        cat ${log}.report >> $log
    fi

    rm -rf ${log}.out
    rm -rf ${log}.err
    rm -rf ${log}.report
}

# Returns prod or test, depending on the Atlas environment in which the script calling it is running
# It is assuming that all atlasinstall_<env>s are under ${ATLAS_PROD}/sw (it will fail otherwise)
atlas_env() {
    scriptDir=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
    atlasInstallSubDir=$(echo $scriptDir | awk -F"/" '{print $8}')
    echo $atlasInstallSubDir | awk -F"_" '{print $2}'
}

# This procedure returns 0 if process $arg is running; otherwise it returns 1
lsf_process_running() {
    arg=$1
    bjobs -l | tr -d "\n" | perl -p -e 's/\s+/ /g' | perl -p -e 's/Job/\nJob/g' | grep 'Job Priority' | grep "$arg" > /dev/null
    return $?
}

function capitalize_first_letter {
    arg=$1
    echo -n $arg | sed 's/\(.\).*/\1/' | tr "[:lower:]" "[:upper:]" | tr -d "\n"; echo -n $arg | sed 's/.\(.*\)/\1/'
}

# Applies fixes encoded in $fixesFile to $exp.$fileTypeToBeFixed.txt
applyFixes() {
    exp=$1
    fixesFile=$2
    fileTypeToBeFixed=$3
    atlasEnv=`atlas_env`

    # Apply factor type fixes in ${fileTypeToBeFixed} file
    for l in $(cat $ATLAS_PROD/sw/atlasinstall_${atlasEnv}/atlasprod/experiment_metadata/$fixesFile | sed 's|[[:space:]]*$||g');
    do
	if [ ! -s "$exp/$exp.${fileTypeToBeFixed}" ]; then
	    echo "ERROR: $exp/$exp.${fileTypeToBeFixed} not found or is empty" >&2
	    return 1
	fi 
	echo $l | grep -P '\t' > /dev/null
	if [ $? -ne 0 ]; then
	    echo  "WARNING: line: '$l' in automatic_fixes_properties.txt is missing a tab character - not applying the fix " 
	fi
	correct=`echo $l | awk -F"\t" '{print $1}'`
	toBeReplaced=`echo $l | awk -F"\t" '{print $2}' | sed 's/[^-A-Za-z0-9_ ]/\\\&/g'`

	if [ "$fixesFile" == "automatic_fixes_properties.txt" ]; then
	    # in sdrf or condensed-sdrv fix factor/characteristic types only
	    #if [ "$fileTypeToBeFixed" == "sdrf.txt" ]; then
		#perl -pi -e "s|\[${toBeReplaced}\]|[${correct}]|g" $exp/$exp.${fileTypeToBeFixed}
	    if [ "$fileTypeToBeFixed" == "condensed-sdrf.tsv" ]; then
		# In condensed-sdrf, the factor/characteristic type is the penultimate column - so tabs on both sides
		perl -pi -e "s|\t${toBeReplaced}\t|\t${correct}\t|g" $exp/$exp.${fileTypeToBeFixed}
	    else 
		# idf
		perl -pi -e "s|\t${toBeReplaced}\t|\t${correct}\t|g" $exp/$exp.${fileTypeToBeFixed}
		perl -pi -e "s|\t${toBeReplaced}$|\t${correct}|g" $exp/$exp.${fileTypeToBeFixed}
	    fi
	elif [ "$fixesFile" == "automatic_fixes_values.txt" ]; then
	    #if [ "$fileTypeToBeFixed" == "sdrf.txt" ]; then
		#perl -pi -e "s|\t${toBeReplaced}\t|\t${correct}\t|g" $exp/$exp.${fileTypeToBeFixed}
		#perl -pi -e "s|\t${toBeReplaced}$|\t${correct}|g" $exp/$exp.${fileTypeToBeFixed}
	    if [ "$fileTypeToBeFixed" == "condensed-sdrf.tsv" ]; then
		# In condensed-sdrf, the factor/characteristic value is the last column - so tab on the left and line ending on the right
		perl -pi -e "s|\t${toBeReplaced}$|\t${correct}|g" $exp/$exp.${fileTypeToBeFixed}
	    fi
	fi
    done
}

applyAllFixesForExperiment() {
   exp=$1
   echo "Applying fixes for $exp ..." 
    # Apply factor type fixes in idf file
    applyFixes $exp automatic_fixes_properties.txt idf.txt
    if [ $? -ne 0 ]; then
	echo "ERROR: Applying factor type fixes in idf file for $exp failed" >&2
	return 1
    fi
    
    # Commenting out SDRF bit as should not be needed any more.
    # Apply factor/sample characteristic type fixes to sdrf
    #applyFixes $exp automatic_fixes_properties.txt sdrf.txt 
    #if [ $? -ne 0 ]; then
	#echo "ERROR: Applying sample characteristic/factor types fixes in sdrf file for $exp failed" >&2
	#return 1
    #fi
    # Apply sample characteristic/factor value fixes in sdrf file
    #applyFixes $exp automatic_fixes_values.txt sdrf.txt
    #if [ $? -ne 0 ]; then
	#echo "ERROR: Applying sample characteristic/factor value fixes in sdrf file for $exp failed" >&2
	#return 1
    #fi

    # Apply factor/sample characteristic type fixes to the condensed-sdrf file
    applyFixes $exp automatic_fixes_properties.txt condensed-sdrf.tsv 
    if [ $? -ne 0 ]; then
	echo "ERROR: Applying sample characteristic/factor types fixes in sdrf file for $exp failed" >&2
	return 1
    fi
    # Apply sample characteristic/factor value fixes to the condensed-sdrf file
    applyFixes $exp automatic_fixes_values.txt condensed-sdrf.tsv 
    if [ $? -ne 0 ]; then
	echo "ERROR: Applying sample characteristic/factor value fixes in sdrf file for $exp failed" >&2
	return 1
    fi
}

# Restriction to run prod scripts as the prod user only
check_prod_user() {
    user=`whoami`
    if [ "$user" != "fg_atlas" ]; then
	echo "ERROR: You need be sudo-ed as fg_atlas to run this script" >&2
	return 1
    fi
    return 0
}

# Get sudo-ed user
get_sudoed_user() {
    realUser=`TTYTEST=$(ps | awk '{print $2}' |tail -1); ps -ef |grep "$TTYTEST$" |awk '{print $1}'`
    echo $realUser
}

get_pass() {
    dbUser=$1
    if [ -e "${ATLAS_PROD}/sw/${dbUser}" ]; then
	cat ${ATLAS_PROD}/sw/${dbUser}
    else
	echo "ERROR: Failed to retrieve DB password" >&2
	return 1
    fi
}

# Fetch properties for ensemblProperty1 and (optionally) ensemblProperty2 from the Ensembl biomart identified by url, serverVirtualSchema and datasetName)
# Called in fetchAllEnsemblMapings.sh
function fetchProperties {
    url=$1
    serverVirtualSchema=$2
    datasetName=$3
    ensemblProperty1=$4
    ensemblProperty2=$5
    chromosomeList=$6
    wbpsFilterField=$7
    wbpsFilterValue=$8
    
    if [[ -z "$url" || -z "$serverVirtualSchema" || -z "$datasetName" || -z "$ensemblProperty1" ]]; then
	echo "ERROR: Usage: url serverVirtualSchema datasetName ensemblProperty1 [ensemblProperty2] [chromosomeList]" >&2
	exit 1
    fi

    # Stem for the temporary files storing each chromosome.
    tempFileStem=~/tmp/$datasetName.$ensemblProperty1

    if [ ! -z "$ensemblProperty2" ]; then
        tempFileStem=$tempFileStem.$ensemblProperty2
    fi

    # Remove old versions of temp files (if any).
    rm -rf $tempFileStem.*.tsv

    if [ ! -z "$chromosomeList" ]; then
        
        for chromosome in $( echo $chromosomeList | sed 's|,|\n|g' ); do

            chromosomeFilter="<Filter name = \"chromosome_name\" value = \"${chromosome}\"/>"

            query="query=<?xml version=\"1.0\" encoding=\"UTF-8\"?><!DOCTYPE Query><Query virtualSchemaName = \"${serverVirtualSchema}\" formatter = \"TSV\" header = \"1\" uniqueRows = \"1\" count = \"0\" ><Dataset name = \"${datasetName}\" interface = \"default\" >${chromosomeFilter}<Attribute name = \"${ensemblProperty1}\" />"
            
            if [ ! -z "$wbpsFilterField" ]; then

                if [ -z "$wbpsFilterValue" ]; then
                    echo "ERROR: No WBPS species name provided for filter."
                fi

                query="$query<Filter name = \"$wbpsFilterField\" value = \"$wbpsFilterValue\"/>"
            fi

            if [ ! -z "$ensemblProperty2" ]; then
                query="$query<Attribute name = \"${ensemblProperty2}\" />"
            fi
            
            tempFile=$tempFileStem.$chromosome.tsv
            
            curl -s -G -X GET --data-urlencode "$query</Dataset></Query>" "$url" | tail -n +2 | sort -k 1,1 | grep -vP '^\t' > $tempFile
        done
        
        # Now we've got all the temp files. Need to concatenate them.
        allChromosomes=`cat $tempFileStem.*.tsv`

        # Clean up.
        rm $tempFileStem.*.tsv
        
        echo "$allChromosomes"

    else
        chromosomeFilter=""
        
        # In some cases a line '^\t$ensemblProperty2' is being returned (with $ensemblProperty1 missing), e.g. in the following call:
        #curl -s -G -X GET --data-urlencode 'query=<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE Query><Query virtualSchemaName = "metazoa_mart_19" formatter = "TSV" header = "1" uniqueRows = "1" count = "0" ><Dataset name = "agambiae_eg_gene" interface = "default" >${chromosomeFilter} <Attribute name = "ensembl_peptide_id" /><Attribute name = "description" /></Dataset></Query>' "http://metazoa.ensembl.org/biomart/martservice" | grep AGAP005154
        # Until this is clarified, skip such lines with grep -vP '^\t'

        query="query=<?xml version=\"1.0\" encoding=\"UTF-8\"?><!DOCTYPE Query><Query virtualSchemaName = \"${serverVirtualSchema}\" formatter = \"TSV\" header = \"1\" uniqueRows = \"1\" count = \"0\" ><Dataset name = \"${datasetName}\" interface = \"default\" >${chromosomeFilter}<Attribute name = \"${ensemblProperty1}\" />"

        if [ ! -z "$ensemblProperty2" ]; then
            query="$query<Attribute name = \"${ensemblProperty2}\" />"
        fi

        curl -s -G -X GET --data-urlencode "$query</Dataset></Query>" "$url" | tail -n +2 | sort -k 1,1 | grep -vP '^\t'
    fi

}

# Called in fetchAllEnsemblMapings.sh
function fetchGeneSynonyms {
    annSrc=$1
    mySqlDbHost=$2
    mySqlDbPort=$3
    mySqlDbName=$4
    softwareVersion=$5
    annotator=$6    # This is either ensembl or wbps

    if [[ $annotator =~ ensembl ]]; then    
        dbUser=anonymous
    elif [[ $annotator =~ wbps ]]; then
        dbUser=ensro
    else
        echo "ERROR: for $annSrc: unknown annotator: $annotator" >&2
        exit 1
    fi

    latestReleaseDB=`mysql -s -u $dbUser -h "$mySqlDbHost" -P "$mySqlDbPort" -e "SHOW DATABASES LIKE '${mySqlDbName}_core_${softwareVersion}%'" | grep "^${mySqlDbName}_core_${softwareVersion}"`
    if [ -z "$latestReleaseDB" ]; then
        echo "ERROR: for $annSrc: Failed to retrieve the database name for release number: $softwareVersion" >&2
        exit 1
    else 
        mysql -s -u $dbUser -h $mySqlDbHost -P $mySqlDbPort -e "use ${latestReleaseDB}; SELECT DISTINCT gene.stable_id, external_synonym.synonym FROM gene, xref, external_synonym WHERE gene.display_xref_id = xref.xref_id AND external_synonym.xref_id = xref.xref_id ORDER BY gene.stable_id" | sort -k 1,1
    fi 
}

# Get mapping between Atlas experiments and Ensembl DBs that own their species
get_experimentToEnsemblDB() {
    dbConnection=$1
    echo "select eo.experiment || chr(9) || oe.ensembldb from experiment_organism eo join bioentity_organism bo on eo.bioentity_organism = bo.name join organism_ensembldb oe on bo.organismid = oe.organismid;" | sqlplus -s $dbConnection | grep -P '^E-'
}


# Get mapping between Atlas experiments and Ensembl DBs that own their species
get_experiments_loaded_since_date() {
    dbConnection=$1
    sinceDate=$2
    echo "select accession from experiment where last_update >= to_date('$sinceDate','DDMonYYYY') and private = 'F' order by accession;" | sqlplus -s $dbConnection | grep -P '^E-'
}

email_log_error() {
    errorMsg=$1
    log=$2
    email=$3
    echo $errorMsg >> $log
    mailx -s $errorMsg $email < $log
}

# Check if $JOB_TYPE for $EXP_IRAP_DIR is currently in progress
# If $JOB_TYPE is not specified, check if any stage for $EXP_IRAP_DIR is currently in progress
get_inprogress() {
   dbConnection=$1
   JOB_TYPE=$2
   EXP_IRAP_DIR=$3
   jobTypeClause=
   if [ "$JOB_TYPE" != "any" ]; then
       jobTypeClause="jobtype='$JOB_TYPE' and"
   fi
   echo `echo "select count(*) from ATLAS_JOBS where $jobTypeClause jobobject='${EXP_IRAP_DIR}';" | sqlplus -s $dbConnection | grep -P '^\t' | awk -F"\t" '{print $NF}' | sed 's/ //g'`
}

# Set 'in-progress' flag in the DB - so that crontab-ed experiment loading calls don't ever conflict with each other
set_inprogress() {
   dbConnection=$1
   JOB_TYPE=$2
   EXP_IRAP_DIR=$3
   inProgress=`get_inprogress $dbConnection $JOB_TYPE $EXP_IRAP_DIR`
   if [ $inProgress -ne 0 ]; then
       return 1
   else
       # First delete any previous entries from $EXP_IRAP_DIR - only one job in progress per ${EXP_IRAP_DIR} is allowed
       echo "delete from ATLAS_JOBS where jobobject='${EXP_IRAP_DIR}';" | sqlplus -s $dbConnection
       echo "insert into ATLAS_JOBS values (sysdate,'$JOB_TYPE','${EXP_IRAP_DIR}');" | sqlplus -s $dbConnection
   fi
}

# Remove 'process is active' flag for $processName
remove_inprogress() {
   dbConnection=$1
   JOB_TYPE=$2
   echo "delete from ATLAS_JOBS where jobtype='$JOB_TYPE';" | sqlplus -s $dbConnection
}