Complete Consistency Check (CCC) is a tool developed within  US ATLAS to
perform consistency checking between our storage catalog systems. Currently
supported systems are DQ2, Rucio, generic disk, and dCache (PNFS/Chimera).
Support for LFC is deprecated.

ccc_pnfs_rucio.py will download the list of datasets listed in DQ2 for a site, compute
Rucio paths for each file in the datasets, and check that against what is in PNFS. It will 
additionally check PNFS against disk. A report is generated in the output directory with a 
summary of discrepancies found.

ccc_generic.py checks a list of datasets in DQ2 against files on a generic mounted disk. It
is as of this writing not updated to compute Rucio paths.  Please contact support@mwt2.org
if you are interested in a version of ccc_generic.py that supports Rucio.

ccc_pnfs.py is a deprecated script that compares DQ2, LFC, and PNFS.  It is replaced by
ccc_pnfs_rucio.py.

Concepts and terminology:

When the storage catalog systems are compared they are organized in a heirarchy, from highest to lowest
level, that being closest to physical disk.  In order these are DQ2 -> Rucio File Catalog ->
PNFS -> filesystem.  

GHOST: A file that is present in a higher level storage catalog, but not in a lower one or on disk.
Ghost files often cause job failures when a job runs at the site and fails to fetch the missing input
file.

ORPHAN: A file that is missing in the higher level storage catalog, but is present in the lower one or
on disk.  Orphans do not cause job failures.  They are typically 'dark data', and may need to be
removed manually.  

DAMAGED DATASET: A dataset that is listed as haing a complete replica at the site, but lower level
catalogs or disk show missing files.  Damaged datasets may cause job failures, for the same reason
as ghost files.

MISSING DATASET: A dataset that is listed as haing a complete replica at the site, but lower level
catalogs or disk show all files are missing.  Missing datasets may cause job failures, for the same reason
as ghost files.

INCOMPLETE DATASET: A dataset is listed as having a incomplete replica at the site, and the lower
level catalog and file system confirm that.  These are not a problem. 

EMPTY DATASET: A dataset listed as having 0 files in the catalog. These are not a problem.

UNKNOWN DATASET: The catalog lists the dataset as present at the site, but when the catalog was
queried for a list of files it returned an 'unknown dataset' error.  If a dataset appears in this
catagory repeatedly it may be broken in the catalog and need attention by the catalog admins.

OK DATASET:  A dataset that is listed as haing a complete replica at the site, and the lower level
catalogs and file system show all files present. Most datasets should be in this category.