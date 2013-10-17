#!/usr/bin/env python

import sys,subprocess

# check the command line input
if not len(sys.argv) == 3:
    print "ERROR: wrong number of arguments:"
    print "USAGE: " + sys.argv[0] + " PATH/TO/DIR/WITH/FILES PATH/TO/FILELIST.TXT"
    sys.exit()

# 1st argument: the list of directories from which we list the files
idirs = sys.argv[1].split(",");
for i in range(0,len(idirs)):
    idirs[i] = idirs[i].rstrip("/")
# 2nd argument: wher to store the list of files
ofile = sys.argv[2];

files = []
for idir in idirs:
    # determine which listing tool to use
    if idir.find("/pnfs")==0:
        listcommand = "dcls"
    else:
        listcommand = "ls"

    # create the list command, execute and retrieve output
    command = listcommand + " " + idir + " | grep root"
    p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (stdout,stderr) = p.communicate()
    lines = stdout.split("\n")
    if len(stderr)!=0:
        print "WARNING: directory",idir," not properly listed"
        print "---"
        print stderr
        print "---"

    # store listed files
    for line in lines:
        # strip off newlines
        line = line.strip("\n")
        # strip off comments
        line = line.split("#",1)[0]
        # strip off spaces
        line.strip()
        # skipp empty lines
        if len(line) == 0:
            continue
        # create the list entry
        prefix = "file:"
        if listcommand == "dcls":
            prefix = "dcap://dcache-cms-dcap.desy.de:22125/"
        files.append(prefix + idir + "/" + line)

# write the listed files to the outputfile
files.sort()
FILE = open(ofile,"w")
for file in files:
    FILE.write(file + "\n")
FILE.close()
