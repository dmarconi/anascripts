#!/usr/bin/env python

import sys,os

# 1 command line argument:
# the path to the project directory to be created
if not len(sys.argv) == 2 and not len(sys.argv) == 3:
    print """ERROR: provid 1 or 2 arguments:
    1. path to the project directory to be created
    2. (optional) path to the project scratch directory to be created
       (used to store data and grid-control work directories for the project)
    """
    sys.exit()

# check the project directory
myprojectdir = os.path.abspath(sys.argv[1]).rstrip("/")
myproject = os.path.split(myprojectdir)[1]
if os.path.exists(myprojectdir):
    print "ERROR: project directory \"" + myprojectdir + "\" already exists"
    sys.exit()

# check the project scratch directory
myscratchdir = None
if len(sys.argv) == 3:
    myscratchdir = os.path.abspath(sys.argv[2]).rstrip("/")
    if os.path.exists(myscratchdir):
        print "ERROR: project directory \"" + myscratchdir + "\" already exists"
        sys.exit()
    
# check that the environment is setup
if not "CMSSW_BASE" in os.environ or not "SCRAM_ARCH" in os.environ:
    print "ERROR: no variable $CMSSW_BASE or $SCRAM_ARCH in the environment"
    print "       please setup the environment for the CMSSW area you want to associate to this new project"
    sys.exit()
CMSSW_BASE = os.environ["CMSSW_BASE"]
SCRAM_ARCH = os.environ["SCRAM_ARCH"]

# create the setenv file
setenv_str  = "#!/bin/bash\n"
setenv_str += "\n"
setenv_str += "# environment for dcach access\n"
setenv_str += "eval `/usr/share/NAF_profiles/ini.pl glite`\n"
setenv_str += "eval `/usr/share/NAF_profiles/ini.pl dctools`\n"
setenv_str += "export X509_USER_PROXY=$HOME/k5-ca-proxy.pem\n"
setenv_str += "export SEHOME=/pnfs/desy.de/cms/tier2/store/user/$USER/ # handy, but not required by anything\n"
setenv_str += "\n"
setenv_str += "# CMSSW environment\n"
setenv_str += "eval `/usr/share/NAF_profiles/ini.pl cmssw`\n"
setenv_str += "export SCRAM_ARCH=" + SCRAM_ARCH + "\n"
setenv_str += "pwd=$PWD\n"
setenv_str += "cd " + CMSSW_BASE + "/src\n"
setenv_str += "eval `scram runtime -sh`;\n"
setenv_str += "cd $pwd\n"
setenv_str += "\n"
setenv_str += "# environment for the analysis tools\n"
setenv_str += "export ANASCRIPTS=" + os.path.split(os.path.abspath(sys.argv[0]))[0] + "\n"
setenv_str += "export MYPROJECT=" + myproject + "\n" 
setenv_str += "export MYPROJECTDIR=" + myprojectdir + "\n"
setenv_str += "export ENVSCRIPT=" + myprojectdir + "/setenv.sh\n"

# create the README file
readme_str = """
----------------------------
 set up the environment
----------------------------
$ source __MYPROJECTDIR__/setenv.sh

----------------------------
 set up the ntuple analyzer
----------------------------
your directory with analyzers should be $MYPROJECTDIR/analyzers
move the content of your current directory with analyzers to $MYPROJECTDIR/analyzers,
or replace $MYPROJECTDIR/analyzers with a soft link to your directory with analyzers

----------------------------
 define sample sets
----------------------------
inside $MYPROJECTDIR/data/samples, create a text file
$MYPROJECTDIR/data/samples/<sample set name>.txt
with sample set name e.g. ntuple_V1
add one line per sample of ntuples, e.g.
--
sampleName1 /path/to/dir/with/ntuples/for/sampleName1
sampleName2 /path/to/dir/with/ntuples/for/sampleName2,/path/to/otherDir/with/ntuples/for/sampleName2
...
--
the first element in each line is used as sample name,
the second element in each line lists the directories with ntuples for the respective sample
directories can be ordinary or dcache (storage element) directories
syntax for dcache directories: /pnfs/.../your/dir/

----------------------------
  create filelists for the ntuple files
----------------------------
$ $ANASCRIPTS/updatefilelist.sh
the filelists are stored in the directory
$MYPROJECTDIR/data/filelists/<sample set name>
one filelist is created for each sample in the sample set
$MYPROJECTDIR/data/filelists/<sample set name>/<sample name>.txt

if you have several sample sets defined and only want to update one of them, do
$ $ANASCRIPTS/updatefilelist.sh <sample set name>

----------------------------
  prepare to run your analyzer with grid-control
----------------------------
e.g
cd $MYPROJECTDIR/workdir
mkdir runanalyzer
cd runanalyzer
$ $ANASCRIPTS/runanalyzer_batch.py  susyanalysis1,susyanalysis2 ntuple/fastsim,ntuple/fullsim_stau250 --wtime 00:15:00 --merge 20
first argument:
   analyzers to run, comma-separated
   these must be executables in $MYPROJECTDIR/analyzer
second argument:
   samples to run over, comma-separated
   these are specified as follows: <sample set name>/<sample name>
some useful options
   --usage: print detailed usage
   --wtime hh:mm:ss : cpu time to request per job
   --merge N: number of files to process per job

files created:
  job.cfg : config file for grid-control
  run_script.sh,script.py: scripts to be run on the batch nodes
  parameters.txt: parameters for run_script.sh
  results: output directory
  runanalyzer_batch_command.txt: stores your command (just have a look)

----------------------------
  run grid-control
----------------------------
$ <YOUR>/<GRID-CONTROL>/go.py job.cfg -icG

this setup is know to work with r950 of grid-control,
and is know not to work with the latest releases
(will be fixes with some edits to runanalyzer_batch.py)
"""
readme_str = readme_str.replace("__MYPROJECTDIR__",myprojectdir)

os.mkdir(myprojectdir)
print "created project directory \"" + myprojectdir + "\""
if myscratchdir != None: 
    os.mkdir(myscratchdir)
    print "created project scratch directory \"" + myscratchdir + "\""
    os.mkdir(myscratchdir + "/data")
    os.mkdir(myscratchdir + "/data/samples")
    os.mkdir(myscratchdir + "/data/filelists")
    os.symlink(myscratchdir + "/data",myprojectdir + "/data")
    os.mkdir(myscratchdir + "/workdir")
    os.symlink(myscratchdir + "/workdir",myprojectdir + "/workdir")
else:
    os.mkdir(myprojectdir + "/data")
    os.mkdir(myprojectdir + "/data/samples")
    os.mkdir(myprojectdir + "/data/filelists")
    os.mkdir(myprojectdir + "/workdir")

os.mkdir(myprojectdir + "/analyzers")
os.mkdir(myprojectdir + "/scripts")
print "created project directory structure"
FILE = open(myprojectdir + "/setenv.sh","w")
FILE.write(setenv_str)
FILE.close()
print "created script to set environment:",myprojectdir + "/setenv.sh"
FILE = open(myprojectdir + "/README","w")
FILE.write(readme_str)
FILE.close()
print "created README:",myprojectdir + "/README"
