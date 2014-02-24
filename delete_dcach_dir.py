#!/usr/bin/env python

import sys,os,subprocess

dir = sys.argv[1].rstrip("/")


p = subprocess.Popen(["dcls",dir],stdout=subprocess.PIPE)
stdout,stderr = p.communicate() 

for line in stdout.split():
    line = line.strip()
    command = ["dcdel",dir + "/" + line]
    print " ".join(command)
    subprocess.call(command)
command = ["dcrmdir",dir]
print " ".join(command)
subprocess.call(command)

