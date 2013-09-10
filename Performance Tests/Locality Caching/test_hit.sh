#!/bin/bash
. /usr/local/dcache/setup.sh
cat testshosts.txt | while read testhost; do
    echo echo 'Start test on $testhost `date`'
    cat ref_points.txt | while read val; do
        cat pooltestNTUP_SMWZ.txt |  while read pool; do 
            echo echo  -n $pool " ";
            echo ssh $testhost '"cd /home/sarah/lc-2013-08-05; . Tutorial-master/Tutorial/getROOTsl6.sh; time ./Tutorial-master/Tutorial/ReadingWritingFile/readDirect root://uct2-s14.uchicago.edu:1096//pnfs/uchicago.edu/atlasdatadisk/pool/ROOTIOTests/NTUP_SMWZ.01120689._000089.root.1/'$pool' physics '$val' 30 2>&1"  >>cachehit.$testhost..NTUP_SMWZ.log 2>&1'
        done
        #echo ~sarah/fix_pooltestfiles.sh
        #echo sleep 30
    done
    echo echo 'Test complete `date`'
done
