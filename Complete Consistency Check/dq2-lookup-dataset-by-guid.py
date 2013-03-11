#!/bin/env python

from dq2.clientapi.DQ2 import DQ2
from dq2.repository.client.RepositoryClient import RepositoryClient
import sys
dq2=DQ2()
client = RepositoryClient()

try:
	guid=sys.argv[1]
	print sys.argv[1]
	vuids=dq2.contentClient.queryDatasetsWithFileByGUID(guid)
	for vuid in vuids:
		print client.queryDatasetByUID(vuid)
except IndexError,e:
	for line in sys.stdin:
                guid=line.strip()
                print guid
		vuids=dq2.contentClient.queryDatasetsWithFileByGUID(guid)
		for vuid in vuids:
			print client.queryDatasetByUID(vuid)
