#!/usr/local/bin/bash
#$Id: cacheinfoof.sh,v 1.3 2009/12/17 21:30:47 sarah Exp $
get_cacheinfoof() {
	/usr/local/bin/dcache-admin << EOF  2>/dev/null | strings | egrep -v '^\[|dCache Admin|dmg.util.CommandExitException|Connection reset by peer' 
cd PnfsManager
cacheinfoof $1
..
logoff
EOF
}

get_cacheinfoof $1
if [ $? != 0 ] ; then
        exit 1
fi
exit 0
