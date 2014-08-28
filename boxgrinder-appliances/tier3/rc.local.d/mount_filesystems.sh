#!/bin/bash
# Mount /atlas
#mount -t fuse xrootdfs -o rdr=root://uct3-xrd.mwt2.org//atlas,allow_other,max_write=131072,attr_timeout=10,entry_timeout=10 /atlas
# Mount, but don't use, t3 homedirs. Read only.
mount -t nfs uct3-s1.uchicago.edu:/export/home /share/home -o bg,intr,noatime,soft,ro
# Mount t3 data shares, soft mounts to prevent hangs. 
mount -t nfs uct3-s1.uchicago.edu:/export/t3data /share/t3data -o bg,intr,noatime,soft
mount -t nfs uct3-s1.uchicago.edu:/export/t3data2 /share/t3data2 -o bg,intr,noatime,soft
mount -t nfs uct3-s1.uchicago.edu:/export/t3data3 /share/t3data3 -o bg,intr,noatime,soft
# Mount PNFS
mount -t nfs uct2-dc4.mwt2.org:/pnfs/uchicago.edu /pnfs/uchicago.edu  -o udp,bg,intr,noac,nosuid,nodev,vers=3
