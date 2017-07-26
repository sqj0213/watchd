#!/bin/env python

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--ip", type=str, default="10.210.238.147", help="please input ip" )
parser.add_argument("--alertFailedRate", type=float, default="0.30", help="please input http failed alert rate(!200/200)" )
args = parser.parse_args()

import sys
print  "%s OK"%(args.ip,sys.argv[2])
