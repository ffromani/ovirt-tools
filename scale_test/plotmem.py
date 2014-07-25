#!/usr/bin/env python

import csv
import matplotlib.pyplot as plt
import sys

def times(seq):
    return range(len(seq))

def getdata(source):
    with open(source, 'rt') as src:
        feed = csv.reader(src)
        libvirt, vdsm = [], []
        for row in feed:
            libvirt.append((float(row[2]), float(row[3])))
            vdsm.append((float(row[5]), float(row[6])))
        return libvirt, vdsm

def splitmem(mem):
    rss, vsz = [], []
    for sample in mem:
        rss.append(sample[0] / (1024. * 1024.))
        vsz.append(sample[1] / (1024. * 1024.))
    return rss, vsz

def draw(source, title):
    libvirt, vdsm = getdata(source)

    plt.figure(1)
    plt.subplot(211)
    t = times(libvirt)
    r, v = splitmem(libvirt)
    plt.plot(#t, v, 'b',
             t, r, 'r')
    plt.ylabel('libvirt memory (MiB)')
    plt.xlabel('time in secs')
    plt.title(title)
    plt.grid(True)

    plt.subplot(212)
    t = times(vdsm)
    r, v = splitmem(vdsm)
    plt.plot(#t, v, 'b',
             t, r, 'r')
    plt.ylabel('VDSM menory (MiB)')
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
