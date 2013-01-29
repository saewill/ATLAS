#!/usr/bin/env python
# condor_offline.py: set a node offline in condor by pushing values
#                    into memcache
#
# $Id: condor_offline.py,v 1.1 2011/08/10 18:54:15 sarah Exp $
#
# condor_offline.py o hostname reason or condor_offline.py c hostname
import memcache, sys
usage = 'condor_offline.py o hostname reason or condor_offline.py c hostname'
def mem_get ( token ) :
        mc = memcache.Client(['mc.mwt2.org:11211'])
        return mc.get(token)
def mem_put ( token , value ) :
        mc = memcache.Client(['mc.mwt2.org:11211'])
        mc.set( token, value )
op = sys.argv[1]
host = sys.argv[2]
if op == 'o' :
	reason = sys.argv[3]
	mem_put("%s.manualstatus" % host, 'offline')
	mem_put("%s.manualreason" % host, reason )
        print "%s set offline with reason %s" % (host, reason)
elif op == 'c' :
        mem_put("%s.manualstatus" % host, 'online')
        mem_put("%s.manualreason" % host, '' )
        print "%s set online" % host
else:
        print usage

