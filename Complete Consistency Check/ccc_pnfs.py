#!/usr/bin/env python

rcs_id="$Id: ccc_pnfs.py,v 1.13 2010/01/26 19:44:32 cgw Exp $"

# ccc_pnfs.py: Complete Consistency Check
#  Three-way consistency check between LFC, dCache pools and /pnfs

import sys, os, fcntl, stat, socket, time, re, marshal, pprint
import fcntl, errno
from select import select

# Make sure another instance is not already running
LOCKFILE="/tmp/ccc.lock"
_lock = open(LOCKFILE, 'w')
os.chmod(LOCKFILE, 0666)
try:    
    status = fcntl.lockf(_lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
except IOError, e:
    if e.errno in (errno.EAGAIN, errno.EACCES):
        print "Cannot lock %s, another instance of ccc may be running" % LOCKFILE
        sys.exit(1)
    else:
        raise
    
t1 = t0 = time.time()
print "Started at", time.ctime(t0)
timestamp = time.strftime("%F-%H%M", time.localtime(t0))
parts = rcs_id.split()
if len(parts) > 2:
    version = parts[2]
else:
    version = "test"

hostname = socket.gethostname()
version_msg = "ccc_pnfs.py version %s running on %s" % (version, hostname)
print version_msg

config_file = "ccc_config.py"
pnfs_dump_file = None
lfc_dump_file = None
check_pools = True
check_dq2 = True
check_lfc = True
min_age = 6*3600 # 7 hours, don't flag any files newer than this
dq2_cache_dir = '/var/tmp/dq2/' # For caching dq2 lookups
dq2 = None
output_dir = ''

def Usage(progname):
    print "Usage: %s [-o output_dir] [-p pnfs_file] [-l lfc_file] [-np] [-nd] [-nl]" % progname
    print "   normal usage requires no options"
    print "   -m min_age: don't flag files newer than this (default=2 hours)"
    print "         use 's' for seconds(default), 'm'=minutes, 'h'=hours, 'd'=days"
    print "   -o specifies directory for (html) output, default is working directory"
    print "   -p pnfs_file reads pnfsDump output from file, instead of "
    print "         using ssh to run pnfsDump on the pnfs server"
    print "   -l lfc_file reads lfc database dump from file, instead of"
    print "         using ssh to execute mysql on the lfc server"
    print "   -np (no pool) skips checking of /dcache/pool on pool nodes"
    print "   -nd (no dq2) skips checking of registered dq2 datasets"
    print "   -nl (no lfc) skips checking of lfc entries"

if "pychecker" in sys.argv[0]:     
    args = sys.argv[2:] 
else: 
    args = sys.argv[1:] 

while args:
    arg = args.pop(0)
    if arg == '-o':
        output_dir = args.pop(0)
    elif arg == '-m':
        min_age = args.pop(0)
        mult = None
        suff = min_age[-1]
        if suff in 'sS':
            mult = 1
        elif suff in 'mM':
            mult = 60
        elif suff in 'hH':
            mult = 3600
        elif suff in 'dD':
            mult = 3600*24
        if mult:
            min_age = min_age[:-1]
        else:
            mult = 1
        min_age = float(min_age)*mult
    elif arg == '-p':
        pnfs_dump_file = args.pop(0)
    elif arg == '-l':
        lfc_dump_file = args.pop(0)
    elif arg == '-np':
        check_pools = False
    elif arg == '-nd':
        check_dq2 = False
    elif arg == '-nl':
        check_lfc = False
    elif arg == '-h':
        Usage(sys.argv[0])
        sys.exit(0)
    else:
        print "Invalid option", arg
        Usage(sys.argv[0])
        sys.exit(1)

if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir)
    
if os.path.exists(config_file):
    print "Loading configuration from", config_file
    try:
        from ccc_config import pnfs_root, \
             pnfs_host, pnfs_dump, \
             lfc_host, lfc_user, lfc_passwd, \
             pools, sites
    except:
        exc, msg, tb = sys.exc_info()
        print "Error loading configuration file", config_file
        print  exc, msg
        print "You may need to delete", config_file
        sys.exit(1)
        
else:
    print "Configuration file", config_file, "not found"
    print "Entering ccc configuration, please enter values for your site"
    parts = hostname.split('.')
    domain = '.'.join(parts[1:])
    default = '/pnfs/' + domain
    pnfs_root = raw_input("pnfs root? (default: %s) " % default).strip() or default
    if not pnfs_root.endswith('/'):
        pnfs_root += '/'
    pnfs_host = raw_input("pnfs server? ").strip()
    default = "/opt/pnfs/tools/pnfsDump"
    pnfs_dump = raw_input("full path to pnfsDump util? (default: %s) "%
                          default).strip() or default
    if check_lfc:
        lfc_host = raw_input("lfc host? ").strip()
        lfc_user = raw_input("lfc user? ").strip()
        lfc_passwd = raw_input("lfc password? ").strip()
    else:
        lfc_host = lfc_user = lfc_passwd = None
        
    
    if check_dq2:
        print "Enter TiersOfATLAS endpoints to check, one per line"
        sites = []
        while True:
            line = raw_input("> ").strip()
            if not line:
                break
            words = line.split()
            if len(words) != 1:
                print "Invalid input"
                continue
            sites.append(words[0])
    else:
        sites = None

    if check_pools:
        print "Enter a list of dCache pools, one per line"
        print "Each line should contain a hostname and a path, separated by whitespace"
        default = '/dcache/pool'
        print "If the path is omitted, the default location %s will be used" % default
        print "If a host has multiple pools, enter each pool on its own line"
        print "End with an empty line"
        pools = []
        while True:
            line = raw_input("> ").strip()
            if not line:
                break
            words = line.split()
            if len(words) == 1:
                host = words[0]
                path = default
            elif len(words) == 2:
                host = words[0]
                path = words[1]
            else:
                print "Invalid input"
                continue
            while path.endswith('/'):
                path = path[:-1]
            pools.append((host, path))
    else:
        pools = None
    
    # Write out config file
    print "Saving config to", config_file
    try:
        f = open(config_file, "w")
    except IOError, detail:
        print "Cannot save config file", config_file, detail
        f = None
    if f:
        print >>f, """
#!/usr/bin/env python
'''config file for ccc_pnfs.py'''
pnfs_root='%s'
pnfs_host='%s'
pnfs_dump='%s'
lfc_host='%s'
lfc_user='%s'
lfc_passwd='%s'
pools=%s
sites=%s
""" % (pnfs_root, pnfs_host, pnfs_dump,
       lfc_host, lfc_user, lfc_passwd,
       pprint.pformat(pools), pprint.pformat(sites))
        f.close()
        
print "Using pnfs root", pnfs_root
print "Min age = ", min_age, "(seconds)"

poolinfo_by_pnfsid = {} #value is list of tuples (pool,time,size)
pnfsid_by_path = {}     #value is pnfsid
lfc_by_path = {}        #value is (fileid,ctime,guid)

#keys for data tuples
POOL,TIME,SIZE = 0, 1, 2
FILEID,CTIME,GUID = 0, 1, 2

def unitize(x):
    suff = 'BKMGTPEZY'
    while x > 1024 and suff:
        x /= 1024.0
        suff = suff[1:]
    return "%.4g%s" % (x, suff[0])

def plural(var, label):
    fmt="%d %s"
    if var != 1: fmt += 's'
    return fmt % (var, label)

class Page:
    def __init__(self, basename, title=None, html=False):
        title = title or basename
        if html:
            suffix = '.html'
        else:
            suffix = ''
        self.html = html
        self.title = title
        self.filename = "%s-%s%s" % (basename, timestamp, suffix)
        self.fullname = os.path.join(output_dir, self.filename)
        self._f = None # File is not opened until we write to it
    def close(self):
        if not self._f:
            return
        if self.html:
            self._f.write("\n</pre></body></html>\n")
        self._f.close()
        self._f = None
    def write(self, text):
        if self._f is None:
            self._f = open(self.fullname, 'w')
            if self.html:
                self._f.write("<html><head><title>%s</title></head><body>\n<pre>" % self.title)
        self._f.write(text)
        self._f.flush()
    def __del__(self):
        if self._f:
            self.close()

main_page = Page('ccc', title='ccc results for %s'%timestamp, html=True)
msg = "Started at %s" % time.ctime(t0)
print "Writing to", os.path.join(output_dir,main_page.filename)
print >> main_page, msg
print >> main_page, version_msg

index_page = os.path.join(output_dir, 'index.html')
if os.path.exists(index_page):
    print "Updating", index_page
    f = open(index_page, 'r')
    lines = f.readlines()
    f.close()
    f = open(index_page, 'w')
    marker = lines.index("<!---MARKER>\n")
    for line in lines[:marker]:
        f.write(line)
else:
    print "Creating", index_page
    f = open(index_page, 'w')
    f.write(
"""<html><head><title>Complete Consistency Check</title></head><body>
<H3>CCC: Complete Consistency Check</H3>
<pre>\n""")
f.write("<a href=%s>Results for %s</a>\n" % (main_page.filename, timestamp))
f.write("""<!---MARKER>
</pre>
</body></html>\n""")
f.close()


datasets_by_site={} #Complete and incomplete replicas, value is dictionary

if check_dq2:
    try:
        from dq2.clientapi.DQ2 import DQ2
        from dq2.common.DQConstants import DatasetState
        dq2 = DQ2()
    except:
        msg = """Cannot import dq2.clientapi, not checking dq2
Finished at %s""" % time.ctime()
        print >> main_page, msg
        print msg
        sys.exit(0)
    print "Starting DQ2 check at %s" % time.ctime()
    for site in sites:
        exception_occurred = False
        all = None
        completes = None
        datasets_by_site[site] = {} #Value is dict dsn->complete (True/False)
        for retry in xrange(5):
            try:
                print "Listing dq2 datasets for", site
                all = dq2.listDatasetsByNameInSite(site) #,complete=0)
                completes = dq2.listDatasetsByNameInSite(site,complete=1)
                break
            except:
                exc, msg, tb = sys.exc_info()
                exception_occurred = True
                if retry<4:
                    time.sleep(60)
        if (completes is None or all is None) and exception_occurred:
            print msg
            continue # next site
        d = datasets_by_site[site]
        for r in all:
            d[r] = False
        for r in completes:
            d[r] = True
        del all
        del completes
        
cmds = []

if not poolinfo_by_pnfsid:
    print "Fetching data...",
    sys.stdout.flush()
    lfc_sql_cmd = 'select sfn,r.fileid,r.ctime,guid from \
Cns_file_replica r, Cns_file_metadata m \
where r.fileid=m.fileid'
    
    ssh_cmd = "ssh -x -oStrictHostKeyChecking=no -n"
    if check_pools:
        cmds += [(host+':'+path, os.popen(
            "%s %s ls --full-time %s/data" %
            (ssh_cmd, host, path)))
                for (host,path) in pools]

    if check_lfc and not lfc_dump_file:
        cmds += [('lfc', os.popen(
            '''%s %s "mysql -u %s -p%s -B -N cns_db <<<'%s'"''' %
            (ssh_cmd, lfc_host, lfc_user, lfc_passwd, lfc_sql_cmd)))]
    
    if not pnfs_dump_file:
        cmds += [('pnfs', os.popen("%s %s '%s -d 10 files -f -l'" %
                                   (ssh_cmd, pnfs_host, pnfs_dump)))]

    cmd_fds = dict([(fd, name) for (name, fd) in cmds])
    cmd_out = dict([(name, ([],'')) for (name, p) in cmds])
    ## first element is list of lines, second element is partial line buffer
    print "Data gathering started at %s" % time.ctime()
    while cmd_fds:
        for fd in select(cmd_fds.keys(), [], [], 60)[0]:
            key = cmd_fds[fd]
            data = fd.read(8192)
            if not data:
                status = fd.close()
                if status:
                    print "command failed for", key, "status", status, cmd_fds[fd]
                    os._exit(-1)
                print "Command finished at %s: %s" % (time.ctime(), cmd_fds[fd])
                del cmd_fds[fd]
            else:
                lines, buf = cmd_out[key]
                if buf:
                    buf += data
                else:
                    buf = data
                l = buf.split('\n')
                if buf.endswith('\n'):
                    buf = ''
                else:
                    buf = l[-1]
                lines += l[:-1] #last line is either empty or incomplete
                cmd_out[key] = (lines, buf)

    del cmds, cmd_fds ## close all open file descriptors

    if lfc_dump_file:
        print "reading lfc dump from", lfc_dump_file+"...",
        sys.stdout.flush()
        fd = open(lfc_dump_file, 'r')
        cmd_out['lfc'] = (fd.readlines(), '')
        fd.close()
        
    if pnfs_dump_file:
        print "reading pnfs dump from", pnfs_dump_file+"...",
        sys.stdout.flush()
        fd = open(pnfs_dump_file,'r')
        cmd_out['pnfs'] = (fd.readlines(), '')
        fd.close()
    
    print "done"

    # Build dictionary of pnfsid -> list of pools
    if check_pools:
        for (host,path) in pools:
            pool = host + ':' + path
            lines = cmd_out[pool][0]
            del cmd_out[pool]
            for line in lines:
                words = line.split()
                if words[0] == 'total':
                    continue
                if len(words) != 9:
                    print "Cannot parse ls output", pool, line
                    #sys.exit(-1)
                    continue
    ### -rw-r--r--  1 root root   0 2008-11-15 10:00:08.000000000 -0600 trace.out
                perm, nlink, u, g, size, date, time_string, timezone, name = words
                time_string = time_string.split('.')[0]
                size=int(size)
                t = time.mktime(time.strptime(date+" "+time_string,"%Y-%m-%d %H:%M:%S"))
                val = poolinfo_by_pnfsid.get(name)
                if val:
                    val.append((pool,t,size))
                else:
                    poolinfo_by_pnfsid[name] = [(pool,t,size)]

    # Build dictionary of (reduced) pathname -> pnfsid
    lines = cmd_out['pnfs'][0]
    del cmd_out['pnfs']
    prefix = pnfs_root
    prefix_len = len(prefix)
    for line in lines:
        try:
            pnfsid, path = line.split()
        except:
            print "ERR", line
            continue
        if not path.startswith(prefix):
            continue
        path = path[prefix_len:]
        pnfsid_by_path[path] = pnfsid

    # Build dictionary of LFC entries.
    if check_lfc:
        lines = cmd_out['lfc'][0]
        del cmd_out['lfc']
        for line in lines:
            sfn,fileid,ctime,guid = line.split()
            ctime = float(ctime)
            parts = sfn.split(pnfs_root, 1)
            if len(parts) == 2:
                prefix, path = parts
                lfc_by_path[path] = (fileid, ctime, guid)
        del lines #save some memory
    
# Check pools for files which are not in pnfs
if check_pools:
    msg = "Checking pools against PNFS..."
    print >> main_page, msg,
    print msg,
    sys.stdout.flush()
    valid_pnfsids = {}
    for pnfsid in pnfsid_by_path.values():
        valid_pnfsids[pnfsid] = True
    pnfsids = poolinfo_by_pnfsid.keys()
    pnfsids.sort()
    orphans_by_pool={}
    for pnfsid in pnfsids:
        if not valid_pnfsids.get(pnfsid):
            for (pool, t, s) in poolinfo_by_pnfsid[pnfsid]:
                if t0 - t > min_age:
                    orphans_by_pool[pool] = orphans_by_pool.get(pool,[])+[(pnfsid,s)]
    del pnfsids

    n_orphans=0
    orphan_bytes=0
    pools=orphans_by_pool.keys()
    pools.sort()
    pnfs_orphans = Page("pnfs-orphans")
    for pool in pools:
        data=orphans_by_pool[pool]
        data.sort()
        for pnfsid, size in data:
            print >> pnfs_orphans, pool, pnfsid
            n_orphans += 1
            orphan_bytes += size
    del pools
    if n_orphans:
        msg = "%s (%s)" % (plural(n_orphans, "PNFS orphan"), unitize(orphan_bytes))
        print msg
        print >> main_page, "<a href=%s>%s</a>" % (pnfs_orphans.filename, msg)
    else:
        print "OK"
        print >> main_page, "OK"
    sys.stdout.flush()
    pnfs_orphans.close()

# Check pnfs for entries which are not in any pool
if check_pools:
    msg = "Checking PNFS against pools..."
    print msg,
    print >> main_page, msg,
    sys.stdout.flush()
    n_ghosts=0
    n_duplicates=0
    pnfs_ghosts = Page("pnfs-ghosts")
    pnfs_duplicates = Page("pnfs-duplicates")
    paths = pnfsid_by_path.keys()
    paths.sort()
    for path in paths:
        pnfsid = pnfsid_by_path[path]
        pools = [pool for (pool, t, s) in poolinfo_by_pnfsid.get(pnfsid, ())]
        if len(pools) != 1:
            if not pools:
                try:
                    # Skip symlinks, as long as they are not dangling
                    sb = os.lstat(pnfs_root + path)
                    if stat.S_ISLNK(sb[stat.ST_MODE]):
                        if os.path.exists(os.readlink(pnfs_root + path)):
                            continue
                    # Skip recent files
                    t = sb[stat.ST_MTIME]
                    if t0 - t < min_age:
                        continue # File is too new
                    # Skip empty files
                    if sb[stat.ST_SIZE] == 0:
                        continue
                except:
                    print "Cannot stat", pnfs_root + path
                    del pnfsid_by_path[path]
                    continue
                print >> pnfs_ghosts, path
                n_ghosts += 1
            else:
                print >> pnfs_duplicates, path, pnfsid, ' '.join(pools)
                n_duplicates += 1
    del paths
    pnfs_ghosts.close()
    pnfs_duplicates.close()
    if n_ghosts or n_duplicates:
        ghost_msg =  plural(n_ghosts, "PNFS ghost")
        dup_msg = plural(n_duplicates, "duplicate")
        print "%s, %s" % (ghost_msg, dup_msg)
        if n_ghosts:
            print >> main_page, "<a href=%s><b>%s</b></a>,"%(pnfs_ghosts.filename,ghost_msg),
        else:
            print >> main_page, ghost_msg+",", 
        if n_duplicates:
            print >> main_page, "<a href=%s>%s</a>"%(pnfs_duplicates.filename,dup_msg)
        else:
            print >> main_page, dup_msg
    else:
        print "OK"
        print >> main_page, "OK"
    sys.stdout.flush()

# Check lfc for entries which are not in pnfs
if check_lfc:
    msg = "Checking LFC against PNFS..."
    print msg,
    print >> main_page, msg,
    sys.stdout.flush()
    n_ghosts=0
    lfc_ghosts = Page("lfc-ghosts")
    paths = lfc_by_path.keys()
    paths.sort()
    for path in paths:
        fileid, ctime, guid = lfc_by_path[path]
        if not pnfsid_by_path.has_key(path) and t0 - ctime > min_age:
            print >> lfc_ghosts, path, fileid, guid, ctime
            n_ghosts += 1
    del paths
    lfc_ghosts.close()
    if n_ghosts:
        msg = plural(n_ghosts, "LFC ghost")
        print msg
        print >> main_page, "<a href=%s><b>%s</b></a>" % (lfc_ghosts.filename, msg)
    else:
        print "OK"
        print >> main_page, "OK"
    sys.stdout.flush()

    # Check pnfs for entries which are not in lfc
    msg = "Checking PNFS against LFC..."
    print msg,
    print >> main_page, msg,
    sys.stdout.flush()
    n_orphans = 0
    orphan_bytes = 0
    lfc_orphans = Page("lfc-orphans")
    paths = pnfsid_by_path.keys()
    paths.sort()
    for path in paths:
        if not path.startswith('atlas'):
            continue
            ## skip files we don't expect to be registered in LFC
            ### XXXX this is a hack

        if '/test/' in path or '/loadtest/' in path:
            continue
        if not lfc_by_path.has_key(path):
            t = None
            pnfsid = pnfsid_by_path[path]
            poolinfo = poolinfo_by_pnfsid.get(pnfsid)
            if poolinfo:
                pool,mtime,size = poolinfo[0]
            else:
                try:
                    statinfo = os.stat(pnfs_root + path)
                except:
                    print "Cannot stat", pnfs_root + path
                    continue
                mtime = statinfo[stat.ST_MTIME]
                size = statinfo[stat.ST_SIZE] ## PNFS may lie
            if t0 - mtime < min_age:
                continue
            print >>lfc_orphans, path, mtime
            n_orphans += 1
            orphan_bytes += size
    del paths
    lfc_orphans.close()
    if n_orphans:
        msg = "%s (%s)" % (plural(n_orphans, "LFC orphan"), unitize(orphan_bytes))
        print msg
        print >> main_page, "<a href=%s>%s</a>" % (lfc_orphans.filename, msg)
    else:
        print "OK"
        print >> main_page, "OK"
    sys.stdout.flush()

def read_cache(dataset):
    data = None
    parts = dataset.split('.')
    cache_dir = dq2_cache_dir + '/'.join(parts[:-1])
    cache_file = cache_dir + '/' + parts[-1] + '.m'
    if os.path.exists(cache_file):
        try:
            cf = open(cache_file)
            data = marshal.load(cf)
            cf.close()
        except: #possibly corrupt file? 
            try:
                os.unlink(cache_file)
            except:
                pass
    return data

def write_cache(dataset, data):
    parts = dataset.split('.')
    cache_dir = dq2_cache_dir + '/'.join(parts[:-1])
    cache_file = cache_dir + '/' + parts[-1] + '.m'
    try: 
        os.makedirs(cache_dir)
    except:
        pass
    try:
        cf = open(cache_file, 'w')
        marshal.dump(data, cf)
        cf.close()
    except: #Don't leave bad data around
        try: 
            os.unlink(cache_file)
        except:
            pass

def is_obsolete(dataset, site):
    # Only user datasets which are > 30 days old
    if not dq2:
        print "WARNING, dq2 API not initialized"
        return False
    if not "USERDISK" in site:
        return False
    try:
        result = dq2.getMetaDataAttribute(dataset, ['creationdate'])
    except:
        exc, msg, tb = sys.exc_info()
        print "WARNING, dq2GetMetaDataAttribute(%s) fails" % dataset
        print msg
        return False
    if result:
        result = result.get('creationdate')
        try:
            t = time.strptime(result, '%Y-%m-%d %H:%M:%S')
            if time.time() - t > 30*24*3600: # 30 days
                return True
        except:
            print "WARNING cannot parse timestamp '%s'" % result
        
    return False


def delete_dataset(dataset, site):
    if not dq2:
        print "WARNING, dq2 API not initialized"
        return
    print "Deleting", dataset, "at", site
    try:
        dq2.deleteDatasetReplicas(dataset, [site])
        dq2.eraseDataset(dataset)
    except:
        exc, msg, tb = sys.exc_info()
        print msg, dataset, site

# Check against DQ2, if possible
if check_dq2:
    msg = "Checking DQ2 against LFC"
    print msg
    print >> main_page, msg
    print "Will check sites:", " ".join(sites)
    lfc_by_guid={} # Key is guid, value is [path, in_dq2]
    for path, (fileid, t, guid) in lfc_by_path.items():
        lfc_by_guid[guid] = [path, False]

    status_codes = (UNKNOWN, EMPTY, MISSING, DAMAGED, INCOMPLETE, OK) = (
        "UNKNOWN", "EMPTY", "MISSING",  "DAMAGED", "INCOMPLETE", "OK")

    for site in sites:
        datasets_by_status = {} # status_code -> [datasets]
        for s in status_codes:
            datasets_by_status[s] = []
        msg ="%s..."%site
        print msg,
        print >> main_page, msg,
        replica_complete = datasets_by_site[site]  ### XXX RENAME THIS VRBL!
        datasets = replica_complete.keys()
        datasets.sort()
        n_complete = 0
        for dataset in datasets:
            if replica_complete[dataset]: 
                n_complete += 1
        msg = "%s, %s complete" % (plural(len(datasets), "replica"),
                                   n_complete)
        print msg
        sys.stdout.flush()
        print >> main_page, msg
        
        for dataset in datasets:
            frozen = False
            dq2_reply = read_cache(dataset)
            data_cached = dq2_reply
            if not data_cached: 
                exception_occurred = False
                for retry in xrange(5):
                    try:
                        dq2_reply = dq2.listFilesInDataset(dataset)
                        frozen = (dq2.getState(dataset) == DatasetState.FROZEN)
                        break
                    except:
                        exc, msg, tb = sys.exc_info()
                        print "ERROR", msg
                        exception_occurred = True
                        dq2_reply = None

                        if "unknown dataset" in str(msg).lower():  #  should use exception class instead
                            break
                        if retry < 4:
                            print "RETRY", retry
                            time.sleep(60)
                if dq2_reply is None:
                    if not exception_occurred:
                        print "ERROR, listFilesInDataset(%s) returns None" % dataset
                    datasets_by_status[UNKNOWN].append(dataset)
                    continue
                
            if dq2_reply:
                if frozen and not data_cached:
                    write_cache(dataset, dq2_reply)
                file_dict, dq2_timestamp = dq2_reply
                guids = file_dict.keys()
                guids.sort()
            else:
                ## XXXX disable this for now, it's slow and it requires a proxy which we may not have
                ##if is_obsolete(dataset, site):
                ##    delete_dataset(dataset, site)
                ##    continue
                ##print "WARNING, listFilesInDataset(%s) returns %s" % (
                ##    dataset,str(dq2_reply))
                guids = ()

            ok = True
            n = 0
            for guid in guids:
                if lfc_by_guid.has_key(guid):
                    lfc_by_guid[guid][1] = True
                    n += 1
                else:
                    lfn = file_dict[guid].get('lfn','???')
                    ok = False
            if replica_complete[dataset]:
                if ok:
                    if guids:
                        status = OK
                    else:
                        status = EMPTY
                else:
                    if n==0:
                        status = MISSING
                    else:
                        status = DAMAGED
            else:
                if guids:
                    status = INCOMPLETE
                else:
                    status = EMPTY
            datasets_by_status[status].append("%s [%d/%d]" %
                                              (dataset, n, len(guids)))

        for status in status_codes:
            n_status = len(datasets_by_status[status])
            if n_status:
                msg = "%s %s" % (plural(n_status, "replica"), status)
                print "\t"+msg
                if status in ('DAMAGED', 'MISSING'):
                    msg = "<b>%s</b>" % msg
                p = Page("datasets-%s-%s" % (site, status))
                print >> main_page, "\t<a href=%s>%s</a>" % (p.filename, msg)
                for d in datasets_by_status[status]:
                    print >> p, d
                p.close()

    msg = "Checking LFC against DQ2..."
    print msg,
    print >> main_page, msg,
    sys.stdout.flush()

    dq2_orphans = Page("dq2-orphans")
    n_orphans = 0
    orphan_bytes = 0
    paths = lfc_by_path.keys()
    paths.sort()
    sub_re = re.compile("_sub[0-9]+/")
    dis_re = re.compile("_dis[0-9]+/")
    for path in paths:
        if sub_re.search(path) or dis_re.search(path):
            continue
            ## _sub and _dis datasets are PandaMover, not expected to be in dq2
        if '/test/' in path or '/loadtest/' in path:
            continue
        fileid, ctime, guid = lfc_by_path[path]
        if t0 - ctime < min_age:  #Too new
            continue
        ignore, in_dq2 = lfc_by_guid.get(guid, [False, False])
        if not in_dq2:
            n_orphans += 1
            size = 0
            pnfsid = pnfsid_by_path.get(path)
            if pnfsid:
                poolinfo = poolinfo_by_pnfsid.get(pnfsid)
                if poolinfo:
                    size = poolinfo[0][SIZE]
            if not size:
                try:
                    size = os.stat(pnfs_root + path)[stat.ST_SIZE] #PNFS may lie
                except:
                    print "Cannot stat", pnfs_root + path
            orphan_bytes += size
            print >> dq2_orphans, path, fileid, guid, ctime
    del paths
    if n_orphans:
        msg = "%s (%s) (dark data)" % (plural(n_orphans, "dq2 orphan"), unitize(orphan_bytes))
        print msg
        print >> main_page, "<a href=%s>%s</a>" % (dq2_orphans.filename, msg)
    else:
        print "OK"
        print >> main_page, "OK"
    dq2_orphans.close()
        
done_msg = "Finished at %s" % time.ctime()
print >> main_page, done_msg
main_page.close()



print done_msg

            
