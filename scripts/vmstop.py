#!/usr/bin/python

import sys
import time
from ovirtsdk.xml import params
from ovirtsdk.api import API


api = API(url='http://engine:8080/api', username='user@internal', password='pass')

start = int(sys.argv[1])
stop = int(sys.argv[2])

for a in range(start, stop):
    name = 'Tiny%02i' % a
    print 'Stopping VM: %s' % name
    try:
        api.vms.get(name).stop()
    except:
        pass
