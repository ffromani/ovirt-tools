#!/usr/bin/env python3.4

import sys
from statistics import mean, stdev

def parse(path):
    with open(path) as src:
        res = {}
        for line in src:
            items = line.strip().split('\t')
            vm = items.pop(0)
            res[vm] = [ float(v) for v in items ]
        return res

def show(src, res):
    tot = []
    for run in zip(*res.values()):
        run = sorted(run)
        x = (mean(run), run[0], run[-1], sum(run))
        tot.append(x)
    data = list(zip(*tot))
    desc = ('mean', 'best', 'worst', 'total')
    print("%s:" % src)
    for x, d in zip(data, desc):
        m = mean(x)
        v = stdev(x)
        p = 100 * v/m
        print('%s:\t%.3fs sd=%.3fs (%.1f%%)' % (d, m, v, p))


if __name__ == '__main__':
    for src in sys.argv[1:]:
        show(src, parse(src))
