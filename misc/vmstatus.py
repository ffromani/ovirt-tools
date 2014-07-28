#!/usr/bin/python

import sys
import time
from ovirtsdk.xml import params
from ovirtsdk.api import API


api = API(url='http://engine:8080/api', username='user@internal', password='pass')

start = int(sys.argv[1])
stop = int(sys.argv[2])

for i in range(start, stop):
    name = 'SuperTiny_C%03i' % i
    print 'VM %s: %s' % (name,
                         api.vms.get(name).status.state)
