#!/bin/bash

wait_interval=300
total_wait=1000000
lfc_dumpfile_path=/tmp/Clean-PM
ccc_path=/usr/local/ccc
ccc_outputdir=/usr/local/ccc/output

exec 1>>$ccc_outputdir/ccc-`date -I`.log 2>&1

cd $ccc_path

source $ccc_path/setup.sh
checks=$(( $total_wait / $wait_interval ))
for i in $( seq 0 $checks ); do
	echo -n "Check number $i ..."
	/usr/local/Clean-PM/clean-PM.sh fetchDB  2>&1 | egrep -v 'Using the existing|Setting up VDT'
	lfc_dumpfile=$( find $lfc_dumpfile_path/*.lfc -mmin -60  | tail -1)
	if [ "$lfc_dumpfile" ]; then
		echo "Run ccc"
		nohup $ccc_path/ccc_pnfs.py -o $ccc_outputdir -l $lfc_dumpfile 
                $ccc_path/dq2-fix-damaged-datasets.sh
		exit 0
	fi
	echo  " waiting $wait_interval"
	sleep $wait_interval
done
echo "Did not get LFC dump file in time - exiting."
exit 2

