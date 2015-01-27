#!/usr/bin/env python

import argparse
import csv
import json
import os
import os.path
import sys

import matplotlib.pyplot as plt


_COLORS = ('r', 'b', 'g', 'k', 'm', 'y')


def getdata(source):
    if source.endswith('csv'):
        return get_data_csv(source)
    elif source.endswith('json'):
        return get_data_json(source)
    else:
        raise RuntimeError('unsupported data source: %s' % source)


def get_data_csv(source):
    with open(source, 'rt') as src:
        feed = csv.reader(src)
        libvirt, vdsm, cpus = [], [], []
        for row in feed:
            libvirt.append(float(row[1]))
            vdsm.append(float(row[4]))
            cpus.append(float(row[-1]))
        return libvirt, vdsm, cpus, [], []


def get_data_json(source):
    with open(source, 'rt') as src:
        libvirt, vdsm, cpus, sampler, mom = [], [], [], [], []
        for line in src:
            feed = json.loads(line)
            libvirt.append(feed["libvirtd"]["cpu"])
            vdsm.append(feed["vdsm_main"]["cpu"])
            cpus.append(feed["host"]["cpu"])
            if "vdsm_sampler" in feed:
                sampler.append(feed["vdsm_sampler"]["cpu"])
            elif "vmon" in feed:
                sampler.append(feed["vmon"]["cpu"])
            if "momd" in feed:
                mom.append(feed["momd"]["cpu"])
            elif "python" in feed:  # ugly bug, ugly fix
                mom.append(feed["python"]["cpu"])
        return libvirt, vdsm, cpus, sampler, mom


def subdraw(plot, ylabel, xlabel, sort_values, worst_values, *args):
    L = list(sorted(len(seq) for seq in args))
    seqs = []
    for seq in args:
        if seq:
            seqs.append(seq)
        else:
            seqs.append([0] * L[-1])

    N  = min(len(seq) for seq in seqs)
    W = 0.2
    skip = int(N * (1 - W))
    nv = N - skip
    if worst_values:
        t  = [i + skip for i in xrange(nv)]
    else:
        t = range(N)

    plt.subplot(plot)
    for color, seq in zip(_COLORS, seqs):
        if worst_values:
            dataset = list(sorted(seq[:N]))[N-nv:]
        elif sort_values:
            dataset = list(sorted(seq[:N]))
        else:
            dataset = seq[:N]
        plt.plot(t, dataset, color)

    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.grid(True)


def draw(sort_values, worst_values, out_file, *data):
    if worst_values:
        sort_values = True

    title  = ' VS '.join(
        '%s (%s)' % (os.path.basename(datafile), color)
        for color, datafile in zip(_COLORS, data))

    data = [getdata(datafile) for datafile in data]
    libvirt, vdsm, cpus, sampler, mom = zip(*data)

    plt.figure(1)
    plt.suptitle(title)

    ax = plt.subplot(321 if any(sampler) else 411)
    xticks = ['libvirt', 'vdsm', 'host']
    ext = False
    if any(sampler):
        xticks.append('sampler')
        ext = True
    if any(mom):
        xticks.append('mom')
        ext = True

    ax.set_xticks([0.2 + i for i in xrange(len(xticks))])
    ax.set_xticklabels(xticks)

    w = 0.1
    for idx, (color, l, v, c) in enumerate(zip(_COLORS, libvirt, vdsm, cpus)):
        dataset = [sum(v) for v in (l, v, c)]
        pos = [idx * w + j for j in xrange(3)]
        ax = plt.bar(pos, dataset, width=w, color=color)
    plt.ylabel('resource usage %')
    plt.xlabel('component')
    plt.grid(True)

    xlabel = 'sample #' if sort_values else 'time in secs'

    subdraw(323 if ext else 412,
            'libvirt cpu %',
            xlabel,
            sort_values,
            worst_values,
            *libvirt)

    subdraw(324 if ext else 413,
            'VDSM cpu %',
            xlabel,
            sort_values,
            worst_values,
            *vdsm)

    subdraw(322 if ext else 414,
            'host cpu %',
            xlabel,
            sort_values,
            worst_values,
            *cpus)

    if any(sampler):
        subdraw(325,
                'sampler cpu %',
                xlabel,
                sort_values,
                worst_values,
                *sampler)

    if any(mom):
        subdraw(326,
                'mom cpu %',
                xlabel,
                sort_values,
                worst_values,
                *mom)

    if out_file:
        fig = plt.gcf()
        fig.set_size_inches(18.5, 10.5)
        fig.savefig(out_file, dpi=800)
        plt.savefig(out_file)
    else:
        plt.show()


def _main():
    parser = argparse.ArgumentParser(description="simplistic VDSM bench plot")
    parser.add_argument('datafiles', metavar='data.csv', type=str, nargs='+',
                        help='VDSM benchmark dataset (CSV)')
    parser.add_argument('--sort', dest='sort_values', action='store_true',
                        default=False,
                        help='sort the samples')
    parser.add_argument('--worst', dest='worst_values', action='store_true',
                        default=False,
                        help='show only worst 20% of samples')
    parser.add_argument('--out', dest='out_file', type=str,
                        help='save to file')

    args = parser.parse_args()

    draw(args.sort_values, args.worst_values, args.out_file, *args.datafiles)


if __name__ == "__main__":
    _main()
