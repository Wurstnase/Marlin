#!/usr/bin/env python

""" Generate the stepper delay lookup table for pyMarlin firmware. """

import argparse


__author__ = "Nico Tonnhofer <tonnhofer@gmail.com>"
__copyright__ = "Copyright 2015, Nico Tonnhofer"
__license__ = "GPL"

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-f', '--cpu-freq', type=int, default=84, help='CPU clockrate in MHz (default=16)')
parser.add_argument('-d', '--divider', type=int, default=8, help='Timer/counter pre-scale divider (default=8)')
args = parser.parse_args()

cpu_freq = args.cpu_freq * 1000000
timer_freq = cpu_freq / args.divider

# print('#ifndef SPEED_LOOKUPTABLE_H')
# print('#define SPEED_LOOKUPTABLE_H')
# print('')
# print('#include "Marlin.h"')
# print('')

fileLookupTable = open('lookupTable.py', 'w')

fileLookupTable.write('speed_lookuptable_fast = [\n')
a = [int(timer_freq / ((i*256)+(args.cpu_freq*2))) for i in range(256)]
b = [a[i] - a[i+1] for i in range(255)]
b.append(b[-1])
for i in range(32):
    fileLookupTable.write('    ')
    for j in range(8):
        fileLookupTable.write('[%d, %d], ' % ((a[8*i+j]), (b[8*i+j])))
    fileLookupTable.write('\n')
fileLookupTable.write(']')
fileLookupTable.write('\n')

fileLookupTable.write('speed_lookuptable_slow = [\n')
a = [int(timer_freq / ((i*8)+(args.cpu_freq*2))) for i in range(256)]
b = [a[i] - a[i+1] for i in range(255)]
b.append(b[-1])
for i in range(32):
    fileLookupTable.write("    ")
    for j in range(8):
        fileLookupTable.write('[%d, %d], ' % ((a[8*i+j]), (b[8*i+j])))
    fileLookupTable.write('\n')
fileLookupTable.write(']')
fileLookupTable.write('\n')

print('finished')
fileLookupTable.close()

# print('#endif')
