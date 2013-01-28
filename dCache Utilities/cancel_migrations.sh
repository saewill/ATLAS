#!/bin/bash
#
# cancel_migrations.sh
#
# With no arguments, cancels all remigrations
# If an argument is given, cancels migrations that contain the arg as a string

if [[ "$1" != "" ]]; then
   list_migrations.sh | grep $1 | while read pool id junk; do echo -en "cd $pool\nmigration cancel $id\n..\n"; done | dcache-admin
else
   list_migrations.sh| while read pool id junk; do echo -en "cd $pool\nmigration cancel $id\n..\n"; done | dcache-admin
fi
