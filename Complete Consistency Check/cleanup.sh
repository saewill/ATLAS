#!/bin/bash

. /usr/local/ccc/setup.sh

# Compare two days of CCC dataset results

day1=2014-06-16-1623
day2=2014-06-17-1503

ccc_output=/usr/local/ccc/output
output=/usr/local/ccc/cleanup-2014-06-18

ls $ccc_output/*MISSING*$day2 $ccc_output/*DAMAGED*$day2 | \
	while read day2log; do
		day1log=$( echo $day2log | sed "s,$day2,$day1,")
		comlog=$output/$( basename $day2log )
		if [ -f $day1log ]; then
			comm -1 -2 \
				<( cat $day1log | cut -f1 -d' ' | sort ) \
				<( cat $day2log | cut -f1 -d' ' | sort ) \
				>$comlog
		fi
			
	done

#Given a list of datamaged datasets, identify which are recoverable
# ( Based on code from sortdamaged.sh by David Lesny )
# Limitation: does not differentiate between complete & incomplete replicas
# TODO: fix that

sortdamaged() {

	DataSetList=$1
	DamagedSite=$2
	Date=$3
	OutputDir=$4

	for DataSet in `cat $DataSetList`; do

	  Sites=$(dq2-list-dataset-replicas $DataSet)
	  Sites=$(echo $Sites | cut -f3 -d ":" )
	  Sites=${Sites#* }
	  Sites=${Sites% *}


	  SiteList="$Sites,"

	  SiteReplica=""

	  until [ -z $SiteList ]; do

	    Site=${SiteList%%,*}
	    SiteList=${SiteList#*,}
  
	    if [ "$Site" == "$DamagedSite" ]; then
		continue
	    fi
	     
	    if [[ -z $SiteReplica ]]; then
		SiteReplica=$Site
	    else
		SiteReplica="$SiteReplica,$Site"
	    fi

	  done

	  if [[ -z $SiteReplica ]]; then
	    echo "$DataSet" >> $OutputDir/NoReplica-$DamagedSite-$Date.txt
	  else
	    echo "$DataSet : $SiteReplica" >> $OutputDir/Replica-$DamagedSite-$Date.txt
	  fi

	done

}

ls $output/*$day2* | while read DatasetList; do
	site=$( echo $DatasetList | sed 's,^.*datasets-,,; s,-DAMAGED.*$,,; s,-MISSING.*$,,;' )
	sortdamaged $DatasetList $site $day2 $output
done
