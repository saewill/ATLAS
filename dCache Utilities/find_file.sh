#!/bin/sh

. /usr/local/dcache/setup.sh

f=$1
if echo $f | grep -q '^00' ; then
    id=$f
else 
    id=$(cat $(dirname $f)/.'(id)('$(basename $f)')')
    if ! echo $id | grep -q '^00'; then
        echo "No such file"
        exit 1
    fi
fi
dcmd.sh "ls /dcache/pool*/data/$id 2>/dev/null" $( pool_list | cut -f1 -d_ | sort -u )


