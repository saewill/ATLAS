#!/usr/local/bin/bash
#$Id: pnfsidof.sh,v 1.2 2009/12/17 21:30:22 sarah Exp $
get_pnfsidof() {
	/usr/local/bin/dcache-admin  << EOF  2>/dev/null | strings | egrep -v '^\[|dCache Admin|dmg.util.CommandExitException|Connection reset by peer' 
cd PnfsManager
pnfsidof $1
..
logoff
EOF
}

get_pnfsidof $1
if [ $? != 0 ] ; then
        get_pnfsidof $1
        exit $?
fi
exit 0
