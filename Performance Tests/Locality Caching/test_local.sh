#!/bin/bash

TESTNAME=$1
ITERATIONS=10

 . Tutorial-master/Tutorial/getROOTsl6.sh


xrdcp root://uct2-s14.uchicago.edu:1096//pnfs/uchicago.edu/atlasdatadisk/pool/ROOTIOTests/NTUP_SMWZ.01120689._000089.root.1/iut2-s6_1 /tmp/NTUP_SMWZ.01120689._000089.root.1
for i in `seq 1 $ITERATIONS`; do
        cat ref_points.txt | while read val; do
		./releaseFileCache /tmp/NTUP_SMWZ.01120689._000089.root.1
		sleep 5
		./Tutorial-master/Tutorial/ReadingWritingFile/readDirect /tmp/DUMMY_NTUP_SMWZ.01120689._000089.root.1 physics 0 30
                sh -c "time ./Tutorial-master/Tutorial/ReadingWritingFile/readDirect /tmp/NTUP_SMWZ.01120689._000089.root.1 physics $val 30" >>$TESTNAME.`hostname -s`.NTUP_SMWZ.locdisk.log 2>&1
        done
done

