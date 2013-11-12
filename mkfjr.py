#!/usr/bin/env python

import os, sys, subprocess, json

#################################
#  command line options
#################################

IFILE = sys.argv[1]
OFILE = sys.argv[2]

# optional
LUMIS = None
lumis = None
if len(sys.argv) > 3:
    LUMIS = sys.argv[3]
    lumis = json.loads(LUMIS)

#################################
#  retrieve path to cmssw file
#################################
# if input file is text file, read CMSSW file from text file
if IFILE.find(".txt") == len(IFILE)-4:
    FILE = open(IFILE)
    IFILE = FILE.readline().strip()
    FILE.close()
print "processing file:",IFILE

#################################
#   set the extension of the fjr file right
#################################
# make sure the _fjr.xml extension is there
if not OFILE.find("_fjr.xml") == len(OFILE)-4:
    OFILE = OFILE + "_fjr.xml"
print "saving fjr as:",OFILE

##################################
# find the lfn of the CMSSW file
# CMSSW FILE MUST BE ON STORAGE ELEMENT
# THIS PARSING MIGHT NOT WORK FOR ALL SITES
##################################
lfn_start = IFILE.find("/store/")
if not lfn_start >= 0:
    print "ERROR: cannot deduce lfn from: ",IFILE
    sys.exit()
lfn = IFILE[lfn_start:len(IFILE)]    
print "LFN:",lfn

##################################
# read CMSSW file properties
##################################
if LUMIS == None:
    edmFileCommandStr = "edmFileUtil -e " + IFILE
else:
    edmFileCommandStr = "edmFileUtil " + IFILE

edmFileCommand = subprocess.Popen(edmFileCommandStr,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
stdout,stderr = edmFileCommand.communicate()
# if error, stop
if len(stderr) != 0:
    print stderr
    sys.exit()
lines = stdout.split("\n")

##################################
# parse main properties
##################################
info = lines[1].lstrip(")").rstrip(")").split(",")
events = info[2].replace('events', '').strip()
size = info[3].replace('bytes', '').strip()
#cksum = info[4].replace('adler32sum','').strip()

##################################
# read lumi sections from file
##################################
if LUMIS == None:
    lumis = dict()
    for line in lines[0:10]:
        line = line.strip()
        if len(line)==0:
            continue
        els = line.split()
        if not len(els)==4:
            continue
        [runId,lumiId,eventId,entry]=els
        if not runId in lumis:
            lumis.update([[runId,[]]])
        if not lumiId in lumis[runId]:
            lumis[runId].append(lumiId)

##################################
# write to xml file
##################################
fjr = open(OFILE, 'w')
fjr.write("<FrameworkJobReport>\n")
fjr.write("<TotalEvents>\n")
fjr.write("\t" + events + "\n")
fjr.write("</TotalEvents>\n")
fjr.write("<Size>\n")
fjr.write("\t" + size + "\n")
fjr.write("</Size>\n" )
fjr.write("<Checksums>\n")
#fjr.write("\t" + "{'adler32':'" + cksum + "'}\n")
fjr.write("\t" + "{}\n")
fjr.write("</Checksums>\n")
fjr.write("<LFN>\n")
fjr.write("\t" + lfn + "\n")
fjr.write("</LFN>\n")
fjr.write('<Runs>\n')
for runId,lumiIDs in lumis.iteritems():
    fjr.write('\t<Run ID="' + str(runId) + '">\n')
    for lumi in lumiIDs:
        fjr.write('\t\t<LumiSection ID="' + str(lumi) + '"/>\n')
    fjr.write('\t</Run>\n')
fjr.write('</Runs>\n')
fjr.write("</FrameworkJobReport>\n")
fjr.close()

