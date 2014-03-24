#!/usr/bin/python

import sys
from ovirtsdk.xml import params
from ovirtsdk.api import API


api = API(url='http://engine:8080/api', username='user@internal', password='pass')

for a in sys.argv[1:]:
    param = params.VM(name='Tiny%s' % a,
                      cluster=api.clusters.get(name='Test'),
                      template=api.templates.get(name='TinyVM'))
    my_vm = api.vms.add(param)


