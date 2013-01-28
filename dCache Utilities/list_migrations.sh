#!/bin/sh
. /usr/local/dcache/lib/functions.sh
( pool_list | while read pool; do echo -e "cd $pool\nmigration ls\n..\n"; done ; echo logoff; ) | \
    dcache-admin 2>/dev/null | sed 's,^.,,g' | tr -d '[]()' | egrep 'migration copy|migration move|migration ls' | \
    while read a b c d e; do
        if [[ $e == "migration ls" ]]; then
            pool=$b
            #echo "pool=$pool"
        else
            echo $pool $a $b $e | cut -c1-70
        fi
    done
