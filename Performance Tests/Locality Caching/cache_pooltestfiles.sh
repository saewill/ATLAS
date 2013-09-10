#!/bin/bash

cat pooltestNTUP_SMWZ.txt | sed 's,^,/pnfs/uchicago.edu/atlasdatadisk/pool/ROOTIOTests/NTUP_SMWZ.01120689._000089.root.1/,' | \
   while read file; do 
      pnfsid=$( ~sarah/repo.mwt2.org/admin-scripts/dcache/pnfsidof.sh $file | tr -d ' ' );
      source_pool=$( basename $file )
      echo -e "\"$source_pool\"\t\"$pnfsid\"" >&2
      echo -e "cd $source_pool\nmigration copy -tmode=precious -target=pgroup -include=iut2-s* -pnfsid=$pnfsid reserved\n..\n"
done | dcache-admin
