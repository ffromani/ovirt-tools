#!/usr/bin/env python3.4

import sys
from statistics import mean, variance

def parse(src):
    res = {}
    for line in src:
        items = line.strip().split('\t')
        vm = items.pop(0)
        res[vm] = [ float(v) for v in items ]
    return res

def show(res):
    tot = []
    for run in zip(*res.values()):
        run = sorted(run)
        x = (mean(run), run[0], run[-1])
        tot.append(x)
        print('%.3f\t%.3f\t%.3f' % x)
    print('-' * 24)
    data = list(zip(*tot))
    for i, x in enumerate(data):
        m = mean(x)
        v = variance(x, m)
        p = 100 * v/m
        print('%s%.3fs +/- %.3fs (%.1f%%)' % ('\t' * i, m, v, p))


if __name__ == '__main__':
    show(parse(sys.stdin))
