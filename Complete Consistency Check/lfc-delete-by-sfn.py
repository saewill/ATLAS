#!/bin/env python
import lfc
import sys

CHUNK=500  # How many replicas to delete in each call to LFC
# Files are often registered in LFC with different URLs. List here
# all the known url prefixes that can be added to your dq2-orphans
# output to make LFC-registered SFNs
SFN_PREFIXES=['srm://uct2-dc1.uchicago.edu/pnfs/uchicago.edu/',
              'srm://uct2-dc1.uchicago.edu:8443/srm/managerv2?SFN=/pnfs/uchicago.edu/']
# Set your LFC server.
s=lfc.lfc_startsess('ust2lfc.usatlas.bnl.gov',"")

def del_replicas(sfns,guids):
     	rem_guids=[]
	rem_sfns=[]
	for sfn_prefix in SFN_PREFIXES:
		prefixed_sfns=[ sfn_prefix + sfn for sfn in sfns ]
		result,err_nums=lfc.lfc_delreplicasbysfn(prefixed_sfns,guids)
		#print err_nums
		for i in range(len(err_nums)):
			err_num=err_nums[i]
			if err_num == 2:
				rem_guids.append(guids[i])
				rem_sfns.append(sfns[i])
			elif err_num != 0:
				err_string = lfc.sstrerror(err_num)
				print  "There was an error for guid " + guids[i] + ": " + str(err_num) + " (" + err_string  + ")"
		guids=rem_guids
		sfns=rem_sfns
                rem_guids=[]
                rem_sfns=[]
		if len(guids) < 0:
			break
	for guid in guids:
		print "There was an error for guid " + guid + ": 2 (No such file or directory), Correct SFN may not be in list or file already deleted."

### MAIN

# If command-line arguments are passed, delete single replica
try:
        sfn=sys.argv[1]
        guid=sys.argv[2]
	del_replicas([sfn],[guid])
except IndexError,e:
# If there are no command-line arguments, wait for stdout
	print "Waiting for input on STDIN..."
	print "Expected format is SFN UNUSEDFIELD GUID"
	print "Compatible with dq2-orphans files"
        sfns=[]
        guids=[]
        for line in sys.stdin:
                fields=line.split()
                sfns.append(fields[0])
                guids.append(fields[2])
                if len(guids) >= CHUNK:
			del_replicas(sfns,guids)
			sfns=[]
			guids=[]
	if len(guids) >= 0:
		del_replicas(sfns,guids)

