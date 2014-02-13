#!/usr/bin/env python

# $Id: adjust_spacetokens.py,v 1.4 2011/07/05 17:42:27 cgw Exp $

import sys, os, time
from datetime import datetime

GB = 1000*1000*1000
TB = GB*1000
MIN_SIZE = 5 * TB # Default minimum for a space token reservation
CAP = 1000 * TB   # Default cap - above this size the token will be assigned
                  #               used space + CAP_FREE
CAP_FREE =  5 * TB

debug = True
 
#Caps for specific space tokens.
CAP_SPECIFIC= { 'ATLASPRODDISK': { 'SIZE': 250*TB, 'FREE': 25*TB } ,
                'ATLASDATADISK': {'SIZE': 1300*TB, 'FREE': 100*TB} }

#Minimums for specific space tokens.  It will check that it is no more than
#PERCENT full, and that it has at least FREE space unused
MIN_SPECIFIC= { 'ATLASPRODDISK':    { 'FREE': 5*TB, 'PERCENT': 79.0 }, 
                'ATLASUSERDISK':    { 'FREE': 5*TB, 'PERCENT': 79.0 },
                'ATLASSCRATCHDISK': { 'FREE': 10*TB, 'PERCENT': 79.0 } }

def run(cmd):
    if debug:
        print  >> sys.stderr, "running cmd %s" % cmd
    p = os.popen(cmd)
    output = p.readlines()
    status = p.close()
    return status, output

def unitize(x):
    suff='BKMGTPEZY'
    while x >= 1000 and suff:
        x /= 1000.0
        suff = suff[1:]
    return "%.4g%s" % (x, suff[0])

class R:
    def __init__(self, s):
        tok = s.split() #removes \r
        if tok:
            self.id=tok[0]
        for x in tok:
            if ':' in x:
                k,v = x.split(':',1)
                try:
                    v = int(v)
                except:
                    pass
                setattr(self, k, v)
    def __repr__(self):
        return "%s\t%s\t%s\t%s\t%s\t%s" % ( self.description, int(100*( (self.used+self.allocated)/self.size)), unitize(self.size), unitize(self.used), unitize(self.allocated), unitize(self.free) )
status, srm_info = run("""
    echo -e "cd SrmSpaceManager\nls -l\n..\nlogoff\n" |  dcache-admin 2>/dev/null| egrep -v 'UNALLOCATED|UNPOWERED' 
    """) 


# Note - we get error from successful command here... 
#if status:
#    print "Error getting data from SrmSpaceManager", status
#    #sys.exit(1)

if debug:
    print  >> sys.stderr,"Adjuster starting %s" % datetime.now()

reservations = [R(x.strip()) for x in srm_info if 'description' in x]
reservations = [ r for r in reservations if 'test' not in r.description.lower()]
reservations.sort(lambda a,b: cmp(a.description, b.description))

for r in reservations:
    if r.size == 0:
        r.size=0.01
        #print r.description, "size = 0, exiting"
        #sys.exit(1)
    r.free = r.size-(r.used+r.allocated)
    r.usage = (r.used+r.allocated)/float(r.size)

if debug:
    print >> sys.stderr, "reservations at start:"
    for r in reservations:
        print  >> sys.stderr, r


# Note - we should probably look at link group ID here
reservations = [r for r in reservations if 'TEST' not in r.description]
tot_size = sum([r.size for r in reservations])

reserved_link_line = [l for l in srm_info if 'Name:reserved-link-group' in l][0]
avail_tok = [t for t in reserved_link_line.split() if t.startswith("AvailableSpace:")][0]
avail =  int(avail_tok.split(':')[1])
# Avail number appears to be no longer reliable, removing --Sarah
tot_size = sum([r.size for r in reservations])# + avail
tot_used = sum([r.used for r in reservations])
tot_alloc = sum([r.allocated for r in reservations])
tot_free = tot_size - (tot_used+tot_alloc)
if tot_size==0:
    sys.exit(1)
usage = (tot_used+tot_alloc)/float(tot_size)

factor = 1.0 / max(usage, 0.01)

if debug:
    print  >> sys.stderr,  map(unitize, (tot_size, tot_used, tot_alloc, tot_free ))

adj_reservations=[]

rationale={}

for i in range(0,2):
    tmp_res = reservations[:] # Copy of array for use in loop

    # Loop through reservations, and see if need to be adjusted to fit minimum or maximum cap requirements
    for r in tmp_res:
        if( (r.used + r.allocated )* factor < MIN_SIZE ):
            rationale[r.description]='MIN_SIZE'
            r.size=MIN_SIZE
        elif ( r.description in CAP_SPECIFIC.keys() and r.used > CAP_SPECIFIC[r.description]['SIZE'] ):
            rationale[r.description]='CAP_SPECIFIC'
            r.size = r.used + CAP_SPECIFIC[r.description]['FREE']
        elif ( r.used > CAP and r.description not in CAP_SPECIFIC.keys()):
            rationale[r.description]='CAP'
            r.size = r.used + CAP_FREE
        elif ( r.description in MIN_SPECIFIC.keys() and (100.0*(r.allocated+r.used)/r.size) > MIN_SPECIFIC[r.description]['PERCENT']):
            rationale[r.description]='MIN_SPECIFIC_PERCENT'
            f = 100.0/MIN_SPECIFIC[r.description]['PERCENT']
            r.size = (r.used+r.allocated) * f
            if (r.size - (r.allocated+r.used)) < MIN_SPECIFIC[r.description]['FREE']:
                rationale[r.description]='MIN_SPECIFIC_PERCENT MIN_SPECIFIC_FREE'
                r.size=r.used+r.allocated+MIN_SPECIFIC[r.description]['FREE']
        elif (  r.description in MIN_SPECIFIC.keys() and (r.size - (r.allocated+r.used)) < MIN_SPECIFIC[r.description]['FREE']):
            rationale[r.description]='MIN_SPECIFIC_FREE'
            r.size=r.used+r.allocated+MIN_SPECIFIC[r.description]['FREE']
        else:
            continue # If the reservation does not need to be adjusted, move on to the next reservation
        adj_reservations.append(r) 
        reservations.remove(r)
        tot_size -= r.size
        tot_used -= r.used
        tot_alloc -= tot_alloc
        tot_free = tot_size - (tot_used + tot_alloc)

    if debug:
        print  >> sys.stderr, adj_reservations
        print  >> sys.stderr, rationale

    usage = (tot_used+tot_alloc)/float(tot_size)
    factor = 1.0 / max(usage, 0.01)

    for r in reservations:
        r.size= (r.used + r.allocated )* factor
        r.free = r.size - (r.used + r.allocated)

for r  in adj_reservations:
    print r.description, r.id, int(r.size)

for r in reservations:
    print r.description, r.id, int(r.size)

if debug:
    print >> sys.stderr, "reservations at end:"
    for r in reservations:
        print  >> sys.stderr, r
    for  r  in adj_reservations:
        print  >> sys.stderr, r

