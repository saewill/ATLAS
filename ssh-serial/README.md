The ssh_serial script is a convenience script for accessing machines connected
to cyclades terminal servers. This script reads from a serial map file that
contains a machine alias, the cyclades server, and the port number of the
machine. While it is possible to use the mapping on the cyclades itself,
we hae found that the NVRAM on older terminal servers is not as stable as we
would like.

Usage: ssh_serial [machine]

Serial map format: [machine] [terminal server] [port] 

