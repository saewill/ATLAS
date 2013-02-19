#!/usr/bin/env python
# memclient.py: store or retrieve values from memcached
#
# $Id: memclient.py,v 1.1 2011/06/15 20:08:13 sarah Exp $
#
# memclient.py get token or memclient.py put token value
import memcache, sys
usage = 'memcache.py get token or memcache.py put token value'
def mem_get ( token ) :
        mc = memcache.Client(['mc.mwt2.org:11211'])
        return mc.get(token)
def mem_put ( token , value ) :
        mc = memcache.Client(['mc.mwt2.org:11211'])
        mc.set( token, value )
op = sys.argv[1]
token = sys.argv[2]
if op == 'get' :
        print mem_get(token)
elif op == 'put' :
        tok_value = sys.argv[3]
        mem_put(token, tok_value)
else:
        print usage

