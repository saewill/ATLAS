#!/bin/bash

# Example of how to set up environment and run ccc_pnfs_rucio.py

ccc_path=/usr/local/ccc
ccc_outputdir=/usr/local/ccc/output

exec 1>>$ccc_outputdir/ccc-`date -I`.log 2>&1

cd $ccc_path

export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
export ALRB_localConfigDir=$HOME/localConfig
source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh
setupATLAS
localSetupDQ2Client --skipConfirm

$ccc_path/ccc_pnfs_rucio.py -o $ccc_outputdir/
