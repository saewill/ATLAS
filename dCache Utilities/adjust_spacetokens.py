#!/usr/bin/env python

# $Id: adjust_spacetokens.py,v 1.4 2011/07/05 17:42:27 cgw Exp $

import sys, os, time

GB = 1000*1000*1000
TB = GB*1000
MIN_SIZE = 5 * TB
PRODDISK_MIN_FREE = 5 * TB
CAP = 1000 * TB
CAP_FREE =  0.1 * CAP
CAP_SPECIFIC= { 'ATLASPRODDISK': { 'SIZE': 250*TB, 'FREE': 25*TB },  'ATLASDATADISK': {'SIZE': 1300*TB, 'FREE': 100*TB} }

def run(cmd):
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

# Note - we should probably look at link group ID here
reservations = [r for r in reservations if 'TEST' not in r.description]
tot_size = sum([r.size for r in reservations])

reserved_link_line = [l for l in srm_info if 'Name:reserved-link-group' in l][0]
avail_tok = [t for t in reserved_link_line.split() if t.startswith("AvailableSpace:")][0]
avail =  int(avail_tok.split(':')[1])

tot_size = sum([r.size for r in reservations]) + avail
tot_used = sum([r.used for r in reservations])
tot_alloc = sum([r.allocated for r in reservations])
tot_free = tot_size - (tot_used+tot_alloc)
if tot_size==0:
    sys.exit(1)
usage = (tot_used+tot_alloc)/float(tot_size)


#print "Tot: size %s\tused %s\talloc %s\tfree %s" % ( unitize(tot_size), unitize(tot_used), unitize(tot_alloc), unitize(tot_free))

factor = 1.0 / max(usage, 0.01)
adj_reservations=[]

tmp_res = reservations[:] # Copy of array for use in loop
for r in tmp_res:
    if( ('PRODDISK' in r.description or 'SCRATCHDISK' in r.description ) and (
((r.used + r.allocated )* factor ) - r.used) < PRODDISK_MIN_FREE ):
        r.size=r.used + r.allocated + PRODDISK_MIN_FREE
        adj_reservations.append(r)
        reservations.remove(r)
        tot_size -= r.size
        tot_used -= r.used
        tot_alloc -= r.allocated
        tot_free = tot_size - (tot_used + tot_alloc)

    elif( (r.used + r.allocated )* factor < MIN_SIZE ):
        r.size=MIN_SIZE
        adj_reservations.append(r)
        reservations.remove(r)
        tot_size -= MIN_SIZE
        tot_used -= r.used
        tot_alloc -= r.allocated
        tot_free = tot_size - (tot_used + tot_alloc)
    elif ( r.description in CAP_SPECIFIC.keys() ):
        if (r.used > CAP_SPECIFIC[r.description]['SIZE'] ):
            r.size = r.used + CAP_SPECIFIC[r.description]['FREE']
            adj_reservations.append(r)
            reservations.remove(r)
            tot_size -= r.size
            tot_used -= r.used
            tot_alloc -= r.allocated
            tot_free = tot_size - (tot_used + tot_alloc)
    elif ( r.used > CAP ):
        r.size = r.used + CAP_FREE
        adj_reservations.append(r)
        reservations.remove(r)
        tot_size -= r.size
        tot_used -= r.used
        tot_alloc -= r.allocated
        tot_free = tot_size - (tot_used + tot_alloc)



usage = (tot_used+tot_alloc)/float(tot_size)
factor = 1.0 / max(usage, 0.01)

for r in reservations:
    r.size= (r.used + r.allocated )* factor
    r.free = r.size - (r.used + r.allocated)
        
#print "Tot: size %s\tused %s\talloc %s\tfree %s" % (unitize(tot_size), unitize(tot_used), unitize(tot_alloc), unitize(tot_free))

#print "floating:"
#print "\n".join([str(r) for r in reservations])
#print "fixed:"
#print "\n".join([str(r) for r in adj_reservations])

for r in reservations:
    r.size= (r.used + r.allocated )* factor
    r.free = r.size - (r.used + r.allocated)

for r  in reservations:
    print r.description, r.id, int(r.size)
for r in adj_reservations:
    print r.description, r.id, int(r.size)

