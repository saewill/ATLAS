#!/bin/bash

# $Id: poolboy.sh,v 1.7 2011/02/14 21:33:31 cgw Exp $

PATH=/usr/local/bin:$PATH # for dcache-admin
. /usr/local/dcache/setup.sh
# Comma-separated list of offlined pools
offline_pools="uct2-s1_*,uct2-s2_*,uct2-s3_*"


phys=$(lynx --dump http://www.mwt2.org/sys/space/space.uc.html | grep Phys | awk '{print $8}'| tr -d %)

level=${1:-$phys}
fuzz=${2:-2}
concurrency=${3:-1}
max_migrations=${4:-18}

d=$(date)
#op_regex=$( echo "$offline_pools" | tr ',' '|' )
op_regex=$( echo "$offline_pools" | sed 's/,/|/g; s/\*/.\*/g; s/\?/.\?/g;' )
echo $d level=$level fuzz=$fuzz concurrency=$concurrency max_migrations=$max_migrations

reserved_pools=$(lynx --dump http://dcache-admin.mwt2.org:2288/poolInfo/pgroups/reserved|
    tr ' ' '\n'|grep t2-|grep -v http|cut -d] -f2 | egrep -v $op_regex)
default_pools=$(lynx --dump http://dcache-admin.mwt2.org:2288/poolInfo/pgroups/default|
    tr ' ' '\n'|grep t2-|grep -v http|cut -d] -f2 | egrep -v $op_regex)

if [[ -n "$offline_pools" ]] ; then
    x=$(tr ','  '|' <<< $offline_pools)
    reserved_pools=$(tr ' ' '\n' <<< $reserved_pools | egrep -v $offline_pools)
    default_pools=$(tr ' ' '\n' <<< $default_pools | egrep -v $offline_pools)
fi

POOL_HOSTS=$(echo $reserved_pools $default_pools | tr ' ' '\n' | cut -d_ -f1 | sort | uniq)
# Clear any existing "poolboy" migrations


list_migrations.sh |
	grep poolboy |
	egrep 'RUNNING|SLEEPING' |
	while read pool id junk; do 
		echo -e "cd $pool\nmigration cancel $id -force\nmigration clear\n.."
	done | dcache-admin

exclude="poolboy" # marker
if [[ -n "$offline_pools" ]]; then exclude="$exclude,$offline_pools"; fi
     dcmd.sh 'df -Ph |grep dcache' $POOL_HOSTS | (
     while read host dev     sz used free pct mountpoint ; do
     ##         s10 /dev/sdb 24T 22T 2.3T 91% /dcache/pool1
     pct=$(echo $pct|cut -d% -f1)
     num=$(echo $mountpoint | tr -d -c '0-9')
     poolname=${host}_${num}
     ## Only handle reserved pools for now
     grep -q $poolname <<< $default_pools && continue 
     if (( pct > level )) ; then
        export exclude="${exclude},${poolname}" 
     fi
     if (( pct > level + fuzz )) ; then
        [[ -n "$full" ]] && full="${full} "
        #full="${full}${poolname}"
        echo $pct $poolname
     fi
     done >/tmp/poolboy.$$
    cat /tmp/poolboy.$$ | sort -rn  | cut -f2 -d' ' | head -$max_migrations | while read pool; do
	echo cd $pool
	echo migration move -select=random -concurrency=$concurrency -exclude=$exclude -order=lru -target=pgroup reserved
	echo ..
	done
    echo logoff )  | dcache-admin
rm -f /tmp/poolboy.$$
