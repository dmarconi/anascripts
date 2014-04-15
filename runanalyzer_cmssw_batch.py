#!/usr/bin/env python

#########################
# retrieve input from commandline
# retrieve input from environment
#########################

import sys,glob,os,time,commands
from optparse import OptionParser

usage = sys.argv[0] + " path/to/cmssw_cfg.py path/to/filelist output_file_names"


# retrieve vars from environment
MYPROJECT = os.environ['MYPROJECT']
MYPROJECTDIR = os.environ['MYPROJECTDIR']
ENVSCRIPT = os.environ['ENVSCRIPT']

# bookkeep the options
FILE = open("runanalyzer_batch_command.txt","w")
FILE.write(" ".join(sys.argv))
FILE.close()

# parse options
parser = OptionParser()
parser.add_option("--merge",dest="merge",type="int",help="number of files to process per job",default=1,metavar="N")
parser.add_option("--wtime",dest="wtime",action="store",help="time requested on batch system",default="00:20:00",metavar="HH:MM:SS")
parser.add_option("--usage",dest="usage",action="store_true",help="print detailed usage")
parser.add_option("--listfilelists",dest="listfilelists",action="store_true",help="list all available filelists")
parser.add_option("--resdir",dest="resdir",action="store",type="string",help="where to store results",default="results")
parser.add_option("--conservefilename",dest="conservefilename",action="store_true",help="name input file = name output file")
(options,args) = parser.parse_args()

# apply documentation options
if options.usage:
    print usage
    sys.exit()

# list all valid filelists
allfilelists = []
for dir in sorted(glob.glob(MYPROJECTDIR + "/data/filelists/*")):
    _filelists = glob.glob(dir + "/*")
    for a in range(0,len(_filelists)):
        _filelists[a] = _filelists[a].replace(os.path.split(dir)[0] + "/","").replace(".txt","")
    _filelists.sort()
    allfilelists.extend(_filelists)

if options.listfilelists:
    print "available filelists:"
    print " - " + "\n - ".join(sorted(allfilelists))

if options.listfilelists:
    sys.exit()

# store the obligatory options
if len(args) < 2:
    print "ERROR: wrong number of arguments"
    sys.exit()
analyzer = args[0]
filelist = args[1]
ofilenames = args[2]

# check validity of options
if not filelist in allfilelists:
    print "ERROR: unknow filelist, " + filelist
    print "available filelists:"
    print " - " + "\n - ".join(sorted(allfilelists))
    sys.exit()

##########################
# create directory structure for output
##########################
def mymakedir(dir):
    if options.resdir.find("/pnfs/") == 0:
        _stdout = commands.getoutput("dcmkdir " + options.resdir)
        #if not len(_stdout) == 0:
        #    print _stdout
        #    sys.exit()
    else:
        os.mkdir(options.resdir)

##########################
# create parameter.txt
##########################
pFILE = open("parameters.txt","w")
pFILE.write("\"IFILES\"")
if options.conservefilename:
    pFILE.write(",\"OUTPUT_FILENAME\"")
pFILE.write("\n")
    
iFILE = open(MYPROJECTDIR + "/data/filelists/" + filelist + ".txt")
files = iFILE.readlines()
iFILE.close()
files = [file.strip() for file in files]

start = 0
stop = options.merge
while start < len(files):
    stop = min(stop,len(files))
    pFILE.write("\"" + "';'".join(files[start:stop]) + "\"")
    if options.conservefilename:
        pFILE.write(",\"" + os.path.split(files[start])[1] + "\"")
    pFILE.write("\n")
    start = start + options.merge
    stop = stop + options.merge
pFILE.close()

##########################
# creat the cmssw python config
##########################
iFILE = open(analyzer)
content = iFILE.read()
iFILE.close()

oFILE = open(os.path.split(analyzer)[1],"w")
oFILE.write(content)
oFILE.write("""
_filenames = "__IFILES__".split(';')
_filenames = [filename.strip(\"\\\'\") for filename in _filenames]
print process.source.fileNames
process.source.fileNames = _filenames
print process.source.fileNames
process.maxEvents.input = -1
""")
oFILE.close()
analyzer = os.path.split(analyzer)[1]

##########################
# create job.cfg
##########################
CFG = open("job.cfg","w")
CFGcontent = ("""[global]
module     = CMSSW
backend    = local
    
[jobs]
jobs       = -1
memory     = 4000
in flight  = 500
wall time  = __WTIMEDUMMY__
max retry  = 0

[parameters]
parameters = <mylist>
mylist type = cvs
mylist source = parameters.txt

[CMSSW]
project area = __PROJECT_AREA_DUMMY__
config file = __CONFIG_FILE_DUMMY__

[storage]
se path = __SE_PATH_DUMMY__
se output files = __SE_OUTPUT_FILES_DUMMY__
se output pattern = __SE_OUTPUT_PATTERN_DUMMY__

[local]
wms = SGE

[SGE]
site = hh
""")
CFGcontent = CFGcontent.replace("__PROJECT_AREA_DUMMY__",os.environ["CMSSW_BASE"])
CFGcontent = CFGcontent.replace("__CONFIG_FILE_DUMMY__",os.path.abspath(analyzer))
CFGcontent = CFGcontent.replace("__WTIMEDUMMY__",options.wtime)
CFGcontent = CFGcontent.replace("__SE_OUTPUT_FILES_DUMMY__",ofilenames)
_se_dir = "dir://" + os.path.abspath(options.resdir)
if options.resdir.find("/pnfs/") == 0:
    _se_dir = "srm://dcache-se-cms.desy.de:8443//srm/managerv2?SFN=/" + options.resdir
CFGcontent = CFGcontent.replace("__SE_PATH_DUMMY__",_se_dir)
if not options.conservefilename:
    CFGcontent = CFGcontent.replace("__SE_OUTPUT_PATTERN_DUMMY__","job_@MY_JOBID@_@X@")
else:
    CFGcontent = CFGcontent.replace("__SE_OUTPUT_PATTERN_DUMMY__","__OUTPUT_FILENAME__")
CFG.write(CFGcontent)
CFG.close()


            
