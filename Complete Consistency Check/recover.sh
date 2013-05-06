#!/bin/bash

# given the output of sortdamaged.sh, resubscribe the recoverable datasets
sort_dir=$1
cd $sort_dir

ls Replica-* | \
    while read file; do 
        site=$( echo $file | cut -f2 -d'-' | cut -f1 -d. ); 
        cat $file | \
            xargs -P8 -i sh -c " dq2-register-subscription {} $site"; 
    done


