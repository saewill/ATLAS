#!/usr/local/bin/bash
#$Id: rcls.sh,v 1.2 2009/12/17 21:29:05 sarah Exp $
/usr/local/bin/dcache-admin << EOF | strings | egrep -v '^\[|dCache Admin|dmg.util.CommandExitException|Connection reset by peer'
cd PoolManager
rc ls
..
logoff
EOF

