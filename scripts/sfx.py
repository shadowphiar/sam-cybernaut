#!/usr/bin/env python

import sys, os, getopt, gzip
from os import path


input = sys.stdin.read()

for sample in range(32):
    if ord(input[363*sample]) > 0:
        data = []
        for d in xrange(363):
            data.append(str(ord(input[363*sample+d])))
    
    
        print "sfx"+str(sample)+": DEFB " + ','.join(data[0:3])
        print "    DEFB " + ','.join(data[3:3*int(data[0])+3])



