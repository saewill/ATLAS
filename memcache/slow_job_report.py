#!/usr/bin/env python

import sys, os, time, string
import memcache

verbose = False
mc = None
suppressEmptyEmails = True
MIN_WALLTIME=3 #hours
MAX_EFF=5 #percent 
PANDA_URL='http://panda.cern.ch/server/pandamon/query?job='
CONDOR_URL='http://www.mwt2.org/sys/view/job_info/'

def mc_init():
    global mc
    if not mc:
        mc = memcache.Client(['mc.mwt2.org:11211'])

def mc_get(key):
    mc_init()
    try:
        r = mc.get(key)
    except:
	r = None
    if verbose:
	print "GET", key, r
    return r

def HMS(x):
    x = int(x)
    s, x = x%60, int(x/60)
    m, x = x%60, int(x/60)
    return "%02d:%02d:%02d" % (x,m,s)

def strip_chars(x):
    valid_chars = "-_.%s%s" % (string.ascii_letters, string.digits)
    if x is None:
        x = "None"
    return ''.join(c for c in x if c in valid_chars)

def write_email_header(jobs, ofile=sys.stdout):
    emptyFlag = 'sys/sjr/EmptyJobsList'
    #create a flag if there are no jobs
    if (suppressEmptyEmails and not jobs):
        f = open(emptyFlag, 'w')
        f.close()
    else:
        #if empty flag exists remove it
        if (os.access(emptyFlag, os.W_OK)):
            os.remove(emptyFlag)
        ofile.write("""To: support@mwt2.org
Subject: Low Efficiency Jobs
Mime-Version: 1.0
Content-Type: text/html

""")

def write_header(ofile=sys.stdout):
    ofile.write("""<html><head><title>Low Efficiency User/Job summary for MWT2</title></head>
<script src='sorttable.js'></script>
<style type="text/css">
th, td {
    padding: 3px !important;
    }

table.sortable thead {
    background-color:#eee;
    color:#666666;
    font-weight: bold;
    cursor: default;
    }
</style>

<body>
<h3>Low Efficiency User/Job summary for MWT2</h3>
<h3>Generated on %s</h3>""" % time.ctime())

def mask_eq(k1, k2, mask):
    return  ((mask&1 or k1[0]==k2[0])
             and (mask&2 or k1[1]==k2[1])
             and (mask&4 or k1[2]==k2[2]))

def merge_keys(keys, mask=0):
    groups = []
    keys = keys[:] # copy
    while keys:
        k1, keys = keys[0], keys[1:]
        group = [k1]
        for k2 in keys[:]:
            if mask_eq(k1, k2, mask):
                group.append(k2)
                keys.remove(k2)
        groups.append(group)
    return groups

def write_job_table(jobs, group, ofile=sys.stdout, merge_mask=0):
    fields = ["User", "Type", "Site", "Panda ID", "Condor ID", "Walltime", "CPU time", "%Efficiency"]
    merge_user = merge_mask & 1
    merge_type = merge_mask & 2
    merge_site = merge_mask & 4
    ofile.write("<table class='sortable'><thead><tr>")
    for i, field in enumerate(fields):
        text = field
        if i < 3:
            merge_field = merge_mask & (1<<i)
            link = merge_mask^(1<<i) # or ''
        ofile.write("<th align='center'>%s</th>" % text)
    ofile.write("</tr></thead>")
    ofile.write("<tbody>")
    rows=[]
    for keys in group:
	    user, jobtype, site = keys
	    for job in jobs[keys]:
	       jobid = job[0]
	       try:
			walltime = job[2][0] 
	       except TypeError, e:
			walltime=0
	       try:
			cputime = job[2][1]
	       except TypeError, e:
			cputime=0

	       if walltime:
		    effcy  = 100.0 * cputime / walltime
	       else:
		    effcy = 0
               try:
		    panda_id=panda_condor_map[jobid]
               except KeyError, e:
                    panda_id=None
	       rows.append((-walltime, """<tr><td>%s</td>
<td>%s</td>
<td align='center'>%s</td>
<td align='right'><a href='%s%s'>%s</a></td>
<td align='right'><a href='%s%s.html'>%s</a></td>
<td sorttable_customkey='%s' align='right'>%s</td>
<td sorttable_customkey='%s' align='right'>%s</td>
<td align='right'>%.2f</td>
</tr>\n""" % (user, jobtype, site, PANDA_URL, jobid, jobid,  CONDOR_URL, panda_id, panda_id, walltime, HMS(walltime), cputime, HMS(cputime), effcy)))

    #rows.sort()
    for row in rows:
        ofile.write(row[1])
    ofile.write("</table>")

def write_table(jobs, ofile=sys.stdout, merge_mask=0):
    fields = ["User", "Type", "Site", "#Jobs", "Walltime", "CPU time", "%Efficiency"]
    merge_user = merge_mask & 1
    merge_type = merge_mask & 2
    merge_site = merge_mask & 4
    ofile.write("<table class='sortable'><thead><tr>")
    for i, field in enumerate(fields):
        text = field
        if i < 3:
            merge_field = merge_mask & (1<<i)
            link = merge_mask^(1<<i) # or ''
            if merge_field:
                text += '<a href=userjobs%s.html>(show)</a>' % link
            else:
                text += '<a href=userjobs%s.html>(hide)</a>' % link

                
        ofile.write("<th align='center'>%s</th>" % text)
    ofile.write("</tr></thead>")
    ofile.write("<tbody>")

    keys = jobs.keys()
    keys.sort()
    groups = merge_keys(keys, merge_mask)
    rows = []
    for group in groups:
        data = []
        for key in group:
            user, jobtype, site = key
            #if user is None:
            #    continue
            data += jobs[key]
        if merge_user:
            user = ""
        if merge_type:
            jobtype = ""
        if merge_site:
            site = ""
        njobs = len(data)
        #job_index_filename= '_'.join([ strip_chars(k) for k in key]) + ".html"
        job_index_filename=strip_chars("%s_%s_%s.html" % ( user, jobtype,site))
	ji_file = open("sys/sjr/." + job_index_filename, 'w') 
        write_header(ji_file)
	#write_job_table(data, key, ji_file, merge_mask)
        write_job_table(jobs, group, ji_file, merge_mask)
        write_footer(ji_file)
	ji_file.close()
        walltime = sum([x[2][0] for x in data if x[2] is not None])
        cputime = sum([x[2][1] for x in data if x[2] is not None])
        if walltime:
            effcy  = 100.0 * cputime / walltime
        else:
            effcy = 0
        rows.append((-walltime, """<tr><td>%s</td>
<td>%s</td>
<td align='center'>%s</td>
<td align='right'><a href='.%s'>%d</a></td>
<td sorttable_customkey='%s' align='right'>%s</td>
<td sorttable_customkey='%s' align='right'>%s</td>
<td align='right'>%.2f</td>
</tr>\n""" % (user, jobtype, site, job_index_filename, njobs, walltime, HMS(walltime), cputime, HMS(cputime), effcy)))

    rows.sort()
    for row in rows:
        ofile.write(row[1])
    ofile.write("</table>")

def write_footer(ofile=sys.stdout):
    ofile.write("</body></html>\n")

panda_condor_map = mc_get('MWT2.panda_condor_map')
if not panda_condor_map:
    sys.exit(1)
condor_ids = panda_condor_map.values()
condor_ids.sort()

jobs = {}  # key is (user, type, site)
for condor_id in condor_ids:
    host = mc_get('%s.host' % condor_id)
    # Defaults
    user = 'Unknown'
    times = (0, 0)
    if host:
        #site = host[:2] # host.split('-')[0]
        site = host.split('.')[1]
        if site == 'mwt2':
            if 'uc3' in host.split('.')[0]:
                site = 'uc3'
            else:
                site = 'uc'
        elif site == 'iu':
            site = 'iu'
        elif site == 'campuscluster':
            site = 'uiuc'
        elif site == 'dmz':
            site = 'IllinoisLX'
        else:
            site = '??'
        panda_id = mc_get('%s.panda_id' % condor_id)
        info = mc_get('%s.info' % panda_id)
        if info:
            user = info[0]
            jobtype = info[1]
        else:
            user = jobtype = None
        times = mc_get('%s.times' % condor_id)
        if not times:
            times=(0.0, 0.0)
        #if user is None:
        #    user = 'unknown'
        #if times is None or times[0] is None or times[1] is None:
        #    continue
        
        if times[0] >= 3600*MIN_WALLTIME and times[1] / times[0] <= MAX_EFF/100.0:
            #print user, jobtype, site, condor_id, panda_id, times
            key = (user, jobtype, site)
            if not jobs.has_key(key):
                jobs[key] = []
            jobs[key].append((panda_id, host, times))
#if not jobs:
#    print "No Low Efficiency Jobs."
    
for merge_mask in xrange(8):
    fname = 'userjobs%d.html' % merge_mask
    ofile = open("sys/sjr/." + fname, 'w') # open as hidden file
    write_header(ofile)
    write_table(jobs, ofile, merge_mask)
    write_footer(ofile)
    ofile.close()
    os.rename("sys/sjr/."+fname, "sys/sjr/"+fname)

fname = 'userjobs_report.html'
ofile = open("sys/sjr/."+fname, 'w')
write_email_header(jobs, ofile)
write_header(ofile)
keys=jobs.keys()
sorted(keys, key=lambda name: name[0])
write_job_table(jobs, keys, ofile, 0)
write_footer(ofile)
ofile.close()
os.rename("sys/sjr/."+fname, "sys/sjr/"+fname)
