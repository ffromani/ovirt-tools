#!/usr/bin/env python

import csv
import matplotlib.pyplot as plt
import sys

def avg(seq):
    return len(seq) * [sum(seq)/float(len(seq))]

def times(seq):
    return range(len(seq))

def cap(seq, cap=120.0):
    for i in seq:
        yield min(i, cap)


def getdata(source):
    with open(source, 'rt') as src:
        feed = csv.reader(src)
        libvirt, vdsm, cpus = [], [], []
        for row in feed:
            libvirt.append(float(row[1]))
            vdsm.append(float(row[4]))
            cpus.append(tuple(float(x) for x in row[7:]))
        return libvirt, vdsm, cpus

def percpu(cpus, i):
    return (cpu[i] for cpu in cpus)

def cpuusage(cpus):
    for sample in cpus:
        yield sum(sample)/float(len(sample))


def draw(source, title):
    libvirt, vdsm, cpus = getdata(source)

    plt.figure(1)
    plt.subplot(311)
    t = times(libvirt)
    a = avg(libvirt)
    plt.plot(t, libvirt, 'g', t, a, 'k')
    plt.ylabel('libvirt cpu % - 100% is one core')
    plt.xlabel('time in secs')
    plt.title(title)
    plt.grid(True)

    plt.subplot(312)
    t = times(vdsm)
    a = avg(vdsm)
    plt.plot(t, list(cap(vdsm)), 'r', t, a, 'k')
    plt.ylabel('VDSM cpu % - 100% is one core')
    plt.xlabel('time in secs')
    plt.grid(True)

    plt.subplot(313)
    t = times(cpus)
    u = list(cpuusage(cpus))
    a = avg(u)
    plt.plot(t, u, 'b', t, a, 'k')
    plt.ylabel('host cpu % - 100% is all cores')
    plt.xlabel('time in secs')
    plt.grid(True)

    plt.show()

def _main():
    args = sys.argv[1:]
    if len(args) != 2:
        print 'usage: plot data.csv title'
        sys.exit(1)
    draw(args[0], args[1])

if __name__ == "__main__":
    _main()
