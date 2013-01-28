#!/bin/sh
. /usr/local/dcache/lib/functions.sh
 pool_list | xargs -i echo -e "cd {}\nmigration clear\n.." | dcache-admin >/dev/null 2>&1
