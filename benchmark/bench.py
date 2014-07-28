#!/usr/bin/env python

import sys
import time
import logging
import argparse
from collections import defaultdict
from multiprocessing import Pool

from ovirtsdk.xml import params
from ovirtsdk.api import API


class VMHandle(object):
    def __init__(self, api, a, name='Tiny'):
        self._api = api
        self._name = '%s%i' % (name, a)
        logging.info(self._name)
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


def _run(vm):
    vm.start()


def start(vms, pool=None):
    if pool is None:
        logging.info('start: serial execution')
        for vm in vms:
            vm.start()
    else:
        logging.info('start: parallel execution')
        pool.map(_run, vms)


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


def mass_start(name, n, pool, api):
    vms = [ VMHandle(api, a, name) for a in range(n) ]
    start(vms, pool)
    wait(vms)
    stop(vms)
    return dict((vm.name, vm.startup_time) for vm in vms)


def bench(n, func, *args):
    aggr = defaultdict(list)
    for i in range(n):
        res = func(*args)
        for k, v in res.items():
            aggr[k].append(v)
    return aggr


def dump(res, store_file):
    def _write(res, dst):
        for k in sorted(res.keys()):
            dst.write('%s\t%s\n' % (k, '\t'.join('%f' % v for v in res[k])))
    if store_file:
        tag = time.strftime('%Y%m%d_%H%M%S')
        with open('bench_%s.csv' % tag, 'wt') as dst:
            _write(res, dst)
    else:
        _write(res, sys.stdout)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--runs', help='amount of runs to do [3]',
                        type=int, default=3)
    parser.add_argument('-n', '--num-vms', help='number of VMs [32]',
                        type=int, default=32)
    parser.add_argument('-N', '--vm-name', help='basename of VM [Tiny]',
                        type=str, default='Tiny')
    parser.add_argument('-s', '--serially', help='run VMs serially',
                        action='store_false', dest='parallel')
    parser.add_argument('-S', '--store-result', help='store result to file',
                        action='store_true')
    args = parser.parse_args()

    api = API(url='http://engine:8080/api', username='user@internal', password='pass')

    if args.parallel:
        logging.info('pool size is %i', args.num_vms)
        pool = Pool(args.num_vms)
    else:
        pool = None

    res = bench(args.runs, mass_start, args.vm_name, args.num_vms, pool, api)
    dump(res, args.store_result)
