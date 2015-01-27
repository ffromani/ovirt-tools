#!/usr/bin/env python

import getopt
import logging
import os
import os.path
import json
import signal
import subprocess
import sys
import time

try:
    import psutil
except ImportError:
    sys.stderr.write(
        'you need psutil from '
        'https://pypi.python.org/pypi/psutil'
        '\n')
    sys.exit(1)

try:
    import daemon
except ImportError:
    sys.stderr.write(
            'you need python-daemon from '
            'https://pypi.python.org/pypi/python-daemon'
            '\n')
    sys.exit(2)


class StopSampling(Exception):
    """Stop sampling right now"""


def handler(signum, frame):
    logging.info('Signal handler called with signal %i', signum)
    raise StopSampling


def mangle_pid(out):
    try:
        return list(sorted(int(token) for token in out.split()))
    except:
        return 0


def find_pids():
    pids = {
        'libvirtd': mangle_pid(
            subprocess.check_output(
                ['/usr/sbin/pidof', 'libvirtd'])),
        'vdsm': mangle_pid(
            subprocess.check_output(
                ['/usr/bin/pgrep', '-u', 'vdsm', 'vdsm']))}
    try:
        pids['vmon'] = mangle_pid(
            subprocess.check_output(
                ['/usr/sbin/pidof', 'vmon']))
    except:
        pass  # nevermind
    try:
        pids['momd'] = mangle_pid(
            subprocess.check_output(
                ['/usr/bin/pgrep', '-f', 'momd']))
    except:
        pass  # nevermind
    return pids


def write_pid_file(pidfile):
    try:
        with open(pidfile, 'wt') as out:
            out.write('%i' % os.getpid())
    except IOError as exc:
        logging.error('savepid(%s) failed: %s', pidfile, str(exc))


def _get_name(proc):
    name = proc.name()
    if name == 'vdsm':
        if proc.ppid() == 1:
            return name + '_main'
        else:
            return name + '_sampler'
#    elif name == 'vmon':
#        return 'vdsm_sampler'
    return name


def sampler(procs, out, delay=0.5):
    # see psutil docs. Discard the first one
    for proc in procs:
        proc.cpu_percent()

    SYNC = 60
    step = 0

    while True:
        try:
            record = {
                'timestamp': time.time(),
                'host': {
                    'cpu': psutil.cpu_percent()}}
            for proc in procs:
                record[_get_name(proc)] = {
                    'cpu': proc.cpu_percent(),
                    'memory': proc.memory_info(),
                    'threads': proc.num_threads()}

            out.write('%s\n' % json.dumps(record))

            if step >= SYNC:
                step = 0
                out.flush()
            step += 1
            time.sleep(delay)
        except KeyboardInterrupt:
            break
        except StopSampling:
            break


def _main(opts, pids):
    vdsm = psutil.Process(pids['vdsm'][0])
    procs = [psutil.Process(pids['libvirtd'][0]),
             vdsm]

    if len(pids['vdsm']) > 1:
        vdsm_sampler = psutil.Process(pids['vdsm'][1])
        if vdsm_sampler.ppid() == vdsm.pid:
            procs.append(vdsm_sampler)
    elif 'vmon' in pids:
        procs.append(psutil.Process(pids['vmon'][0]))

    if 'momd' in pids:
        procs.append(psutil.Process(pids['momd'][0]))

    if '-p' in opts:
        write_pid_file(opts['-p'])

    for proc in procs:
        logging.info('tracking: %s pid=%i ppid=%i',
                     _get_name(proc), proc.pid, proc.ppid())

    start = time.time()
    logging.info('begin sampling at %f', start)

    with open(opts.get('-o', '/dev/null'), 'wt') as out:
        sampler(procs, out)

    stop = time.time()
    logging.info('end sampling at %f' % stop)
    logging.info('sampled for %i seconds' % int(stop - start))


def usage():
    print '-h      this message'
    print '-D      became daemon'
    print '-o file saves output stats to <file> [/dev/null]'
    print '-p file saves pid to <file> [/dev/null]'


if __name__ == "__main__":
    optlist, args = getopt.getopt(sys.argv[1:], 'Dho:p:')
    opts = dict(optlist)

    if '-h' in opts:
        usage()
        sys.exit(0)

    logging.basicConfig(level=logging.DEBUG)

    try:
        pids = find_pids()
    except Exception as exc:
        logging.error('failed to find PIDs: %s', str(exc))
        sys.exit(2)
    else:
        if '-D' in opts:
            signal.signal(signal.SIGTERM, handler)
            signal.signal(signal.SIGINT, handler)
            signal.signal(signal.SIGUSR1, handler)
            with daemon.DaemonContext():
                _main(opts, pids)
        else:
            logging.info('found pids:')
            for n, ps in pids.iteritems():
                logging.info(' %s: %s',
                             n,
                             ','.join('%i' % p for p in  ps))
            _main(opts, pids)
