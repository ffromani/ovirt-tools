#!/usr/bin/env python

import csv
import argparse
from collections import defaultdict
import logging
import subprocess
import sys
import time

from ovirtsdk.xml import params
from ovirtsdk.api import API


class VMHandle(object):
    def __init__(self, api, i, name):
        self._api = api
        self._name = name % i
        self._marks = {'created': time.time()}

    def _mark(self, state):
        if state not in self._marks:
            self._marks[state] = time.time()

    @property
    def startup_time(self):
        return self._marks['up'] - self._marks['created']

    @property
    def _handle(self):
        return self._api.vms.get(self._name)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        st = self._handle.status.state
        if st == 'powering_up':
            self._mark('powered')
        elif st == 'up':
            self._mark('up')
        return st

    @property
    def running(self):
        return self.state == 'up'

    def start(self):
        if not self.running:
            logging.info('Starting VM: %s', self._name)
            self._mark('started')
            self._handle.start()

    def stop(self):
        if self.running:
            logging.info('Stopping VM: %s', self._name)
            self._handle.stop()
            self._mark('stopped')


def start(vms):
    logging.info('start: serial execution')
    for vm in vms:
        vm.start()
        time.sleep(1)


def stop(vms):
    for vm in vms:
        vm.stop()


def wait(vms, state='up'):
    step = 1
    pending = set(vm for vm in vms)
    while pending:
        logging.info('* step #%02i: still pending: %i VMs (%s)',
                     step, len(pending), ','.join(vm.name for vm in pending))
        npending = set()
        for vm in pending:
            if vm.state == state:
                logging.info('* step #%02i: VM %s ready! (%s)',
                             step, vm.name, vm.state)
            else:
                npending.add(vm)
        pending = npending
        step += 1
        time.sleep(1)


def idle(secs_, chunk=10):
    elapsed, secs = 0, int(secs_) if secs_ is not None else 0
    while elapsed < secs:
        logging.info('idling for %i more seconds, %i elapsed', secs-elapsed, elapsed)
        time.sleep(chunk)
        elapsed += chunk


def monitor(host, action, args, workdir='$HOME', path=''):
    subprocess.call(['ssh', host,
                      'PATH=$PATH:'+ path, 'vdsmmon.py', '-D',
                      '-o', workdir + '/test.csv',
                      '-p', workdir +  '/mon.pid'])

    action(*args)

    subprocess.call(['ssh', host,
                     'kill', '-USR1',
                     '$(', 'cat', workdir + '/mon.pid', ')'])
    data = subprocess.check_output(['ssh', host,
                                    'cat', 'test.csv'])
    subprocess.call(['ssh', host,
                     'rm', 'test.csv', 'mon.pid'])
    return data


def bench(host, name, first, last, api, outfile, delay=None):
    vms = [ VMHandle(api, i, name) for i in range(first, last) ]
    start(vms)
#    wait(vms)

    begin = time.time()
    data = monitor(host, idle, (delay,))
    end = time.time()

    stop(vms)
    return data


if __name__ == '__main__':
    if len(sys.argv) != 6:
        print 'usage: host start stop mins outfile'
        sys.exit(1)

    host = sys.argv[1]
    first = int(sys.argv[2])
    last = int(sys.argv[3])
    mins = int(sys.argv[4])
    outfile = sys.argv[5]

    logging.basicConfig(level=logging.DEBUG)
    api = API(url='http://HOST:8080/api',
              username='USER',
              password='PASS')

    data = bench(host, 'SuperTiny_C%03i', first, last, api, outfile, mins * 60.)

    with open(outfile, 'wb') as out:
        out.write(data)
