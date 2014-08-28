#!/bin/sh

./slow_job_report.py
if [ ! -f '/opt/sysview/sys/sjr/EmptyJobsList'  ]
then
    cat ./sys/sjr/userjobs_report.html | /usr/sbin/sendmail -t
fi