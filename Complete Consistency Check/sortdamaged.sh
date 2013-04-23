#!/bin/sh

#Given a list of datamaged datasets, identify which are recoverable

rm -f Replica*.txt
rm -f NoReplica*.txt

DataSetList=$1

if [ -z $DataSetList ]; then
  echo "Need a datsetlist files"
  exit
fi


for DataSet in `cat $DataSetList`; do

  Sites=$(dq2-list-dataset-replicas $DataSet)
  Sites=$(echo $Sites | cut -f3 -d ":")
  Sites=${Sites#* }
  Sites=${Sites% *}


  SiteList="$Sites,"

  SiteReplica=""

  until [ -z $SiteList ]; do

    Site=${SiteList%%,*}
    SiteList=${SiteList#*,}
     
    echo $Site | grep -q "^MWT2_"

    if [[ $? -eq 0 ]]; then 
      SiteMWT2=$Site
    else
      if [[ -z $SiteReplica ]]; then
        SiteReplica=$Site
      else
        SiteReplica="$SiteReplica,$Site"
      fi
    fi

  done

  if [[ -z $SiteReplica ]]; then
    echo "$DataSet" >> NoReplica.txt
    echo "$DataSet" >> NoReplica-$SiteMWT2.txt
  else
    echo "$DataSet : $SiteReplica" >> Replica.txt
    echo "$DataSet : $SiteReplica" >> Replica-$SiteMWT2.txt
  fi

done


