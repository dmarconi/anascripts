#!/usr/bin/env python

import sys,os,glob,shutil
    
# check the environment
if not "ANASCRIPTS" in os.environ:
    print "ERROR: no environmental variable $ANASCRIPTS available"
    print "       did you set the environment?"
    sys.exit()
if not "MYPROJECT" in os.environ:
    print "ERROR: no environmental variable $MYPROJECT available"
    print "       did you set the environment?"
    sys.exit()
if not "MYPROJECTDIR" in os.environ:
    print "ERROR: no environmental variable $MYPROJECTDIR available"
    print "       did you set the environment?"
    sys.exit()


MYPROJECT = os.environ["MYPROJECT"]
MYPROJECTDIR = os.environ["MYPROJECTDIR"]


validsamplelists = sorted(glob.glob(MYPROJECTDIR + "/data/samples/*.txt"))
for i in range(0,len(validsamplelists)):
    validsamplelists[i] = os.path.split(validsamplelists[i])[1].replace(".txt","")

# first optional argument is the samplelist for which to update the filelists
samplelists = []
if len(sys.argv) == 2:
    elements = sys.argv[1].split(",")
    for ele in elements:
        if not ele in validsamplelists:
            print "ERROR: invalid option"
            print "     : choose from " + ",".join(validsamplelists)
        samplelists.append(ele)
# else, just update all filelists
else:
    samplelists = validsamplelists
    
# find/create the main directory with filelists
filelistdir = MYPROJECTDIR + "/data/filelists/"
if not os.path.isdir(filelistdir):
    os.mkdir(filelistdir)

# loop over samplelists
for samplelist in samplelists:
    # directory with filelists
    _filelistdir  = filelistdir + "/" + samplelist
    # remove the directory with old filelists
    if os.path.isdir(_filelistdir):
        shutil.rmtree(_filelistdir)
    # create a new one
    os.mkdir(_filelistdir)

    # read samples from list
    samplelistname = MYPROJECTDIR + "/data/samples/" + samplelist + ".txt"
    SAMPLES = open(samplelistname)
    samples = SAMPLES.readlines()
    SAMPLES.close()

    # create file lists
    for sample in samples:
        # strip off newlines
        sample = sample.strip("\n")
        # strip off commands
        sample = sample.split("#",1)[0]
        # strip off spaces
        sample.strip()
        # skipp empty lines
        if len(sample) == 0:
            continue
        # get the nickname and the directories for the samples
        elements = sample.split(" ")
        if not len(elements)==2:
            print "ERROR: wrong formatting of " + samplelistname
            sys.exit()
        nickname = elements[0]
        dirs     = elements[1]
        # make the filelist
        filelistname = _filelistdir + "/" + nickname + ".txt"
        print "listing for " + samplelist + ":" + nickname + " \t (" + filelistname + ")"
        command = "$ANASCRIPTS/mkfilelist.py " + dirs + " " + filelistname
        os.system(command)
    

