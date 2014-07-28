#!/usr/bin/python

import sys
from ovirtsdk.xml import params
from ovirtsdk.api import API


api = API(url='http://engine:8080/api', username='user@internal', password='pass')


args = sys.argv[1:]
if len(args) == 1:
    seq = xrange(int(args[0]))
elif len(args) == 2:
    seq = xrange(int(args[0]), int(args[1]))

for i in seq:
    param = params.VM(name='SuperTiny_C%03i' % i,
                      cluster=api.clusters.get(name='Default'),
                      template=api.templates.get(name='SuperTiny_C0_T'))
    my_vm = api.vms.add(param)


