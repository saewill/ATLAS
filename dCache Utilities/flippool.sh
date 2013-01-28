#!/usr/local/bin/bash
/usr/local/bin/dcache-admin << EOF 
cd $1
pool disable
pool enable
..
logoff
EOF

