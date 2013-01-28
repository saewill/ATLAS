#!/bin/sh

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
dcmd.sh "ls /dcache/pool*/data/$id 2>/dev/null" uct2-s[14] iut2-s[6].iu.edu


