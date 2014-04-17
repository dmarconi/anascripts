
#!/usr/bin/env python

usage = """
######################################

3 ARGUMENTS ARE REQUIRED

1st argument : analyzers to run,
  each analyzer is an executable in the directory $MYPROJECT/analyzers/
  (can be changed with command line)
  it is assumed that each analyzer takes as only argument the list of files to process

2nd argument : filelists to run over
  path to txt file that lists all files to be processed
  paths are assumed relative to $MYPROJECT/data/filelists
  
3rd argument : output directory
  path to directory were output is stored
  by default, paths are assumed relative to $MYPROJECTDIR
  instead, if the option --useSE is applied,
  paths are assumed relative to $SEHOME

MORE OPTIONAL ARGUMENTS

--merge N
  each job processes N input files
  if not used in combination with --fullmerge:
  each input file is processed separately
  and output is stored for each input file separately
--fullmerge
  to be used with --merge N
  in each job, all N input file are processed in one go
  and the output is produced for the N input files together
  use this option for large mc samples,
  do not use it for signal scans
--localcp
  make a local copy of the input files before running
  speeds up things if running multiple analyses simultaneously
  and if using a +/- slow file server 
--useSE
  store output on storage element
--njobs N
  run only first N jobs 

DOCUMENTATION OPTIONS

can be used without obligatory options

--usage
  print this message
--listanalzyers
  list all valid analyzers
--listfilelists
  list all valid filelists

######################################
"""

#########################
# retrieve input from commandline
# retrieve input from environment
#########################

import sys,glob,os,time
from optparse import OptionParser

# retrieve vars from environment
MYPROJECT = os.environ['MYPROJECT']
MYPROJECTDIR = os.environ['MYPROJECTDIR']
#MYPROJECTSCRATCH = os.environ['MYPROJECTSCRATCH']
ENVSCRIPT = os.environ['ENVSCRIPT']

# bookkeep the options
FILE = open("runanalyzer_batch_command.txt","w")
FILE.write("python ".join(sys.argv))
FILE.close()

# parse options
parser = OptionParser()
parser.add_option("--merge",dest="merge",type="int",help="number of files to process per job",default=1,metavar="N")
parser.add_option("--fullmerge",dest="fullmerge",action="store_true",help="use with --merge, output is merged per job",default=False)
parser.add_option("--localcp",dest="localcp",action="store_true",help="make a local copy at the beginning of each job",default=False)
parser.add_option("--wtime",dest="wtime",action="store",help="time requested on batch system",default="00:20:00",metavar="HH:MM:SS")
parser.add_option("--anadir",dest="anadir",action="store",help="directory with analyzer executables, default: $MYPROJECTDIR/analyzers/",default=MYPROJECTDIR + "/analyzers",metavar="path/to/analyzer_dir/")
#parser.add_option("--useSE",dest="useSE",action="store_true",help="store output on SE",default=False)
#parser.add_option("--njobs",dest="njobs",type="int",help="run first N jobs only",default=-1,metavar="N")

parser.add_option("--usage",dest="usage",action="store_true",help="print detailed usage")
parser.add_option("--listanalyzers",dest="listanalyzers",action="store_true",help="list all available analyzers")
parser.add_option("--listfilelists",dest="listfilelists",action="store_true",help="list all available filelists")
(options,args) = parser.parse_args()

# apply documentation options
if options.usage:
    print usage
    sys.exit()

# list all valid analyzers and filelists
allanalyzers = glob.glob(options.anadir + "/*")
for a in reversed(range(0,len(allanalyzers))):
    if not os.access(allanalyzers[a],os.X_OK):
        del allanalyzers[a]
        continue
    if allanalyzers[a].find("~") == len(allanalyzers[a])-1:
        del allanalyzers[a]
        continue 
    allanalyzers[a] = os.path.split(allanalyzers[a])[1]#.replace("analyzer_","")

allfilelists = []
for dir in sorted(glob.glob(MYPROJECTDIR + "/data/filelists/*")):
    _filelists = glob.glob(dir + "/*")
    for a in range(0,len(_filelists)):
        _filelists[a] = _filelists[a].replace(os.path.split(dir)[0] + "/","").replace(".txt","")
    _filelists.sort()
    allfilelists.extend(_filelists)

# apply documentation options
if options.listanalyzers:
    print "available analyzers:"
    print " - " + "\n - ".join(sorted(allanalyzers))

if options.listfilelists:
    print "available filelists:"
    print " - " + "\n - ".join(sorted(allfilelists))

if options.listfilelists or options.listanalyzers:
    sys.exit()

# store the obligatory options
if len(args) < 2:
    print "ERROR: wrong number of arguments"
    sys.exit()
analyzers = args[0].split(",")
#analyzers = [analyzer.replace("analyzer_","") for analyzer in analyzers]
filelists = args[1].split(",")

# check validity of options
if options.fullmerge and not options.merge:
    print "the option --fullmerge can only be used in combination with --merge"
    sys.exit()
for analyzer in analyzers:
    if not analyzer in allanalyzers:
        print "ERROR: unknown analyzer, " + analyzer
        print "available analyzers:"
        print " - " + "\n - ".join(sorted(allanalyzers))
        sys.exit()
for filelist in filelists:
    if not filelist in allfilelists:
        print "ERROR: unknow filelist, " + filelist
        print "available filelists:"
        print " - " + "\n - ".join(sorted(allfilelists))
        sys.exit()

##########################
# create directory structure for output
##########################
for analyzer in analyzers:
    for filelist in filelists:
        os.makedirs("results/" + analyzer + "/" + filelist)


##########################
# create local copy of executable
##########################
for analyzer in analyzers:
    os.system("cp " + options.anadir + "/" + analyzer + " " + analyzer) 

##########################
# create parameter.txt
##########################
pFILE = open("parameters.txt","w")
pFILE.write("\"INPUT\"\n")
for filelist in filelists:    
    iFILE = open(MYPROJECTDIR + "/data/filelists/" + filelist + ".txt")
    files = iFILE.readlines()
    iFILE.close()
    start = 0
    stop = options.merge
    while start < len(files):
        stop = min(stop,len(files))
        pFILE.write("\"" + filelist + "[" + str(start) + ":" + str(stop) + "]\"\n")
        start = start + options.merge
        stop = stop + options.merge
pFILE.close()

##########################
# creat the script
##########################

# a wrapper, to set the environment right
SCRIPT = open("run_script.sh","w")
SCRIPT.write("#!/bin/bash\n")
SCRIPT.write("source __ENVSCRIPT__\n")
SCRIPT.write("python " + os.path.abspath("script.py") + " $1\n")
SCRIPT.close()

# the header
SCRIPT = open("script.py","w")
SCRIPT.write("""#!/usr/bin/env python

import sys,os,glob

##################################
# read command line arguments and environment
##################################

MYPROJECTDIR = os.environ['MYPROJECTDIR']
INPUT = sys.argv[1]
print 'input:',INPUT
""")
SCRIPT.write("WORKDIR=\"" + os.environ["PWD"] + "\"\n")
SCRIPT.write("ANALYZERS=[\"" + "\",\"".join(analyzers) + "\"]\n")
SCRIPT.write("ODIR=\"" + os.environ["PWD"] + "/results\"\n")

# list all files to run over
SCRIPT.write("""
##################################
# list all input files
##################################
pos = INPUT.find('[')
# get the name of the filelist
INPUT_name = INPUT
if pos >= 0:
    INPUT_name = INPUT_name[0:pos]
# the range of files to be processed
INPUT_start = 0
INPUT_stop = -1
if pos >= 0:
    INPUT_range = INPUT.replace(INPUT_name,"")
    [INPUT_start,INPUT_stop] = [int(x.strip('[').strip(']')) for x in INPUT_range.split(':')]
# read the files in
FILE = open(MYPROJECTDIR + '/data/filelists/' + INPUT_name + '.txt')
ifiles = FILE.read().split('\\n')
FILE.close()
if INPUT_stop < 0:
    ifiles = len(ifiles) -1
ifiles = ifiles[INPUT_start:INPUT_stop]
# print file list
print 'all input files:'
for ifile in ifiles:
    print ' - ' + ifile
""")

# copy all input files to local disc
if options.localcp:
    SCRIPT.write("""
##################################
# make a local copy of input files
##################################
os.mkdir('data')
for f in range(0,len(ifiles)):
    _ifile = 'data/' + os.path.split(ifiles[f])[1]
    if ifiles[f].find('/pnfs') >= 0:
        start = ifiles[f].find('/pnfs')
        ifiles[f] = ifiles[f][start:len(ifile)]
        command = 'dcget ' + ifiles[f] + ' ' + _ifile
        print command
        os.system(command)
    else:
        command = 'cp ' + tocp + ' data/' + os.path.split(tocp)[1]
        print command
        os.system(command)
    ifiles[f] = _ifile
""")

# create the local filelist(s)
SCRIPT.write("""
##################################
# create local filelist(s)
##################################
os.mkdir('filelists')
filelists = []
""")
if not options.fullmerge:
    SCRIPT.write("""
for ifile in ifiles:
    filelists.append('filelists/' + os.path.split(ifile)[1].replace('.root','.txt'))
    FILE = open(filelists[-1],'w')
    FILE.write(ifile + '\\n')
    FILE.close()
""")
else:
    SCRIPT.write("""
filelists.append('filelists/' + os.path.split(ifiles[0])[1].replace('.root','.txt'))
FILE = open(filelists[0],'w')
for ifile in ifiles:
    FILE.write(ifile + '\\n')
FILE.close()
""")

SCRIPT.write("sys.stdout.flush()\n")

# run each analyzer on each filelist
content = ("""
##################################
# run analyzers and copy output
##################################
for analyzer in ANALYZERS:
    output = 'results/' + analyzer + '/' + INPUT_name
    os.makedirs(output)
    for filelist in filelists:
        output = 'results/' + analyzer + '/' + INPUT_name + '/' + os.path.split(filelist)[1].replace('.txt','')
        command = WORKDIR + '/' + analyzer + ' ' + filelist + ' ' + output
        print command
        os.system(command)
        ofiles = glob.glob(output + '*')
        print 'copy output'
        for ofile in ofiles:
            command = 'cp ' + ofile + ' ' + ODIR + '/' + analyzer + '/' + INPUT_name  
            print command
            os.system(command)
""")
SCRIPT.write(content)
SCRIPT.close()

##########################
# create job.cfg
##########################
CFG = open("job.cfg","w")
CFGcontent = ("""[global]
module     = UserMod
backend    = local
    
[jobs]
jobs       = -1
memory     = 4000
in flight  = 500
wall time  = __WTIMEDUMMY__
max retry  = 0

[parameters]
parameters = <mylist>
mylist type = csv
mylist source = parameters.txt

[UserMod]
executable  = run_script.sh
arguments   = __INPUT__
constants   = ENVSCRIPT
ENVSCRIPT   = __ENVSCRIPTDUMMY__
subst files = run_script.sh

[local]
wms = SGE

[SGE]
site = hh
""")
CFGcontent = CFGcontent.replace("__ENVSCRIPTDUMMY__",os.environ["ENVSCRIPT"])
CFGcontent = CFGcontent.replace("__WTIMEDUMMY__",options.wtime)
CFG.write(CFGcontent)
CFG.close()
