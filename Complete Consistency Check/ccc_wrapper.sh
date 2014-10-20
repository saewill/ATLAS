#!/bin/bash

# Example of how to set up environment and run ccc_pnfs_rucio.py

ccc_path=/usr/local/ccc
ccc_outputdir=/usr/local/ccc/output

exec 1>>$ccc_outputdir/ccc-`date -I`.log 2>&1

cd $ccc_path
source $ccc_path/setup.sh

$ccc_path/ccc_pnfs_rucio.py  -nl -o $ccc_outputdir/
