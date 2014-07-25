#!/usr/bin/env python

import getopt
import logging
import os
import os.path
import signal
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


_RUNDIR = '/var/run'


class StopSampling(Exception):
    """Stop sampling right now"""


def handler(signum, frame):
    logging.info('Signal handler called with signal %i', signum)
    raise StopSampling


def slurp(path):
    with open(path, 'rt') as src:
        return src.read()


def read_pid_file(path, basedir=_RUNDIR):
    return int(slurp(basedir + '/' + path).strip())


def find_pids():
    return (read_pid_file('libvirtd.pid'),
            read_pid_file('vdsm/vdsmd.pid'))


def write_pid_file(pidfile):
    try:
        with open(pidfile, 'wt') as out:
            out.write('%i' % os.getpid())
    except IOError as exc:
        logging.error('savepid(%s) failed: %s', pidfile, str(exc))


def sampler(libvirtd, vdsm, delay=0.5):
    # see psutil docs. Discard the first one
    libvirtd.cpu_percent()
    vdsm.cpu_percent()

    ts = 0.0
    while True:
        try:
            yield (time.time(),
                   libvirtd.cpu_percent()) + \
                   libvirtd.memory_info() + \
                   (vdsm.cpu_percent(),) + \
                   vdsm.memory_info() + tuple(
                   psutil.cpu_percent(percpu=True))
            time.sleep(delay)
            ts += delay
        except KeyboardInterrupt:
            break
        except StopSampling:
            break


def _main(opts, libvirtd_pid, vdsm_pid):
    libvirtd = psutil.Process(libvirtd_pid)
    vdsm = psutil.Process(vdsm_pid)

    if '-p' in opts:
        write_pid_file(opts['-p'])

    start = time.time()
    logging.info('begin sampling at %f', start)

    samples = list(sampler(libvirtd, vdsm))

    stop = time.time()
    logging.info('end sampling at %f' % stop)
    logging.info('sampled for %i seconds' % int(stop - start))

    with open(opts.get('-o', '/dev/null'), 'wt') as out:
        for sp in samples:
            out.write('%s\n' % ','.join(str(val) for val in sp))


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
        libvirtd_pid, vdsm_pid = find_pids()
    except Exception as exc:
        logging.error('failed to find PIDs: %s', str(exc))
        sys.exit(2)
    else:
        if '-D' in opts:
            signal.signal(signal.SIGTERM, handler)
            signal.signal(signal.SIGINT, handler)
            signal.signal(signal.SIGUSR1, handler)
            with daemon.DaemonContext():
                _main(opts, libvirtd_pid, vdsm_pid)
        else:
            logging.info('found pids: libvirt=%i vdsm=%i', libvirtd_pid, vdsm_pid)
            _main(opts, libvirtd_pid, vdsm_pid)
