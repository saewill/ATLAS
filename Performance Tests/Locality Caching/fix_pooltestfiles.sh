#!/bin/bash

find /pnfs/uchicago.edu/atlasdatadisk/pool -type f | \
   while read file; do 
      pnfsid=$( ~sarah/repo.mwt2.org/admin-scripts/dcache/pnfsidof.sh $file | tr -d ' ' );
      target_pool=$( basename $file )
      echo -e "\"$target_pool\"\t\"$pnfsid\"" >&2
      ~sarah/repo.mwt2.org/admin-scripts/dcache/cacheinfoof.sh $file | \
          sed 's,^ *,,; s, ,\n,;' | \
          grep -v $target_pool | \
          while read pool; do
              echo -e "\"$target_pool\"\t\"$pool\"\t\"$pnfsid\"" >&2
              echo -e "cd $pool\nmigration move -target=pool -pnfsid=$pnfsid $target_pool\n..\n"
          done
   done | dcache-admin
