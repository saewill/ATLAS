#!/bin/bash

(	find /usr/local/ccc/output/*MISSING*  -mtime -1
	find /usr/local/ccc/output/*DAMAGED*  -mtime -1) | \
 	 while read file; do 
		site=$( echo $file | cut -f2 -d'-' ); 
		echo "Site $site"
		cat $file | \
		while read dataset junk; do 
			dq2-check-replica-consistency $dataset $site; 
		done 
	done
