import glob
import mypyslha     # own basic version of mypyslha: much faster
import sys,os
import tempfile
from slurpTable import slurpTable   # own module to read in simple tables in txt format


# usage
usage = """
#######################
#   slha2tree
#######################

a script to ntuplize sets of slha files

usage:

"""
usage += "   python {0} SLHADIR OFILE [options]\n".format(sys.argv[0])
usage += """
   SLHADIR: directory with slha files to be ntuplized
   OFILE:   output file containing ntuplized slha files in root TTree format

options:

   --storeId FILE1,FILE2,... : store per slha file an id number, specified in txt format in FILE1,FILE2,...
   --storeId 'FILE*'         : store per slha file an id number, specified in txt format in FILE1,File2,...
                               where FILE1,FILE2, ... have the following sturcure:
   --nentries=N only store info for first N slha files in tree
--------
id\tfile
1\t/path/to/slhaFile1
2\t/path/to/slhaFile2
5\t/path/to/slhaFile5
...
--------
                               slha files for wich no id is available get default id -9999
"""

# parse command line
from optparse import OptionParser
parser = OptionParser(usage=usage)
parser.add_option("--storeId",type="string",help="store slha id numbers as stored in FILE1,FILE2,FILE3,... (wildcard allowd if parentheses are used)",metavar="FILE")
parser.add_option("--nentries",type="int",help="use N first slha files only",metavar="N")
(options, args) = parser.parse_args()
if not len(args) >= 2:
    print "ERROR, expecting at least 2 arguments, use --help option for more info"
    sys.exit()
slhadir = sys.argv[1]
ofile = sys.argv[2]

# load root in batch mode
sys.argv.append("-b")
import ROOT as rt

# list slha files
slhafiles = sorted(glob.glob(slhadir + "/*"))
if options.nentries and options.nentries < len(slhafiles):
    slhafiles = slhafiles[0:options.nentries]

# read in ids
idfiles = []
slhaIdDict = None
if options.storeId:
    _idfiles = options.storeId.split(",")
    for f in range(0,len(_idfiles)):
        idfiles.extend(glob.glob(_idfiles[f]))
    slhaIdDict = slurpTable(",".join(idfiles),dictMode=True,keyColumns="file")


# read first slha file to extract structure
blocks,decays = mypyslha.parseSLHAFile(slhafiles[0])
print blocks,decays
print slhafiles[0]

###################
# create c++ struct to interface the tree
###################
print "creating c++ struct to interface the tree..."
struct_str = "struct MyData {\n"
# path to slha file
struct_str +="   int ID;\n"
struct_str +="   char slhapath[256];\n" 
# block information
for blockname in sorted(blocks.keys()):
    block = blocks[blockname]
    struct_str += "   // BLOCK {0}\n".format(blockname)
    # Q
    if block.Q is not None:
        struct_str += "   double {0}_Q;\n".format(blockname.lower())
    # entries
    for key,val in block.entries.iteritems():
        _key = ""
        if type(key) is tuple:
            _key = "_" + "_".join([str(x) for x in list(key)])
        elif key!= "":
            _key = "_" + str(key)
        branchname = blockname.lower() + _key
        struct_str += "   double " + branchname + ";\n"
# decay information
for pdgId in sorted(decays.keys()):
    branchnamebase = "decay_" + str(pdgId)
    struct_str +="   // DECAY {0}\n".format(pdgId) 
    struct_str +="   double " + branchnamebase + "_tw;\n"    # total width
    struct_str +="   int "    + branchnamebase + "_ndc;\n"     # number of decay channels
    struct_str +="   double " + branchnamebase + "_br[200];\n"       # branching ratio per channel
    struct_str +="   int "    + branchnamebase + "_ndp[200];\n"      # number of decay products per channel
    struct_str +="   int " + branchnamebase + "_id1[200];\n"   # pdgid of 1st decay product
    struct_str +="   int " + branchnamebase + "_id2[200];\n"   # pdgid of 2nd decay product
    struct_str +="   int " + branchnamebase + "_id3[200];\n"   # pdgid of 3rd decay product
    struct_str +="   int " + branchnamebase + "_id4[200];\n"   # pdgid of 4th decay product
struct_str += "};"

#FILE = open("temp.C","w")
#FILE.write(struct_str)
#FILE.close()

# write struct to temporary file
TEMPFILE = tempfile.NamedTemporaryFile()
TEMPFILE.write(struct_str)
TEMPFILE.flush()
# load it into root
tempfileName = TEMPFILE.name
rt.gROOT.ProcessLine(".L " + tempfileName);
# create an instance
myData = rt.MyData();

####################
# define python function to fill the c++ struct with slha info
####################
print "creating python function to fill the c++ struct.."
func_str = ""
func_str += "def updateMyData(myData,slhafile,slhaId):\n"
func_str += "   blocks,decays = mypyslha.parseSLHAFile(slhafile)\n"
func_str += "   myData.slhapath = slhafile\n"
func_str += "   myData.ID = slhaId\n"
# block information
for blockname in sorted(blocks.keys()):
    block = blocks[blockname]
    func_str += "   # BLOCK {0}\n".format(blockname)
    # Q
    if block.Q is not None:
        func_str += "   myData.{0}_Q = blocks[\"{1}\"].Q\n".format(blockname.lower(),blockname)
    # entries
    for key,val in block.entries.iteritems():
        _key = ""
        if type(key) is tuple:
            _key = "_" + "_".join([str(x) for x in list(key)])
        elif key!= "":
            _key = "_" + str(key)
        branchname = blockname.lower() + _key
        if key == "":
            key = "\"{0}\"".format(key)
        func_str += "   myData.{0}{1} = blocks[\"{2}\"].entries[{3}]\n".format(blockname.lower(),_key,blockname,key)
# decay information
for pdgId in sorted(decays.keys()):
    func_str +="   # DECAY {0}\n".format(pdgId)
    branchnamebase = "decay_{0}".format(pdgId)
    # set default values
    func_str +="   myData.{0}_tw = -1e-9\n".format(branchnamebase)
    func_str +="   myData.{0}_ndc = 0\n".format(branchnamebase)
    func_str +="   decay = decays[{0}]\n".format(pdgId)
    func_str +="   if decay.tw != None:\n"
    func_str +="      myData.{0}_tw = decay.tw\n".format(branchnamebase)
    func_str +="      myData.{0}_ndc = len(decay.dp)\n".format(branchnamebase)
    func_str +="      for d in range(0,len(decay.br)):\n"
    func_str +="         myData.{0}_br[d] = decay.br[d]\n".format(branchnamebase)
    func_str +="         ndp = len(decay.dp[d])\n"
    func_str +="         myData.{0}_ndp[d] = ndp\n".format(branchnamebase)
    func_str +="         myData.{0}_id1[d] = -1e-9\n".format(branchnamebase)
    func_str +="         myData.{0}_id2[d] = -1e-9\n".format(branchnamebase)
    func_str +="         myData.{0}_id3[d] = -1e-9\n".format(branchnamebase)
    func_str +="         myData.{0}_id4[d] = -1e-9\n".format(branchnamebase)
    func_str +="         if ndp > 0:\n"
    func_str +="            myData.{0}_id1[d] = decay.dp[d][0]\n".format(branchnamebase)
    func_str +="         if ndp > 1:\n"
    func_str +="            myData.{0}_id2[d] = decay.dp[d][1]\n".format(branchnamebase)
    func_str +="         if ndp > 2:\n"
    func_str +="            myData.{0}_id3[d] = decay.dp[d][2]\n".format(branchnamebase)
    func_str +="         if ndp > 3:\n"
    func_str +="            myData.{0}_id4[d] = decay.dp[d][3]\n".format(branchnamebase)

FILE = open("temp.py","w")
FILE.write(func_str)
FILE.close()

exec(func_str)

###################
# define tree
###################
print "defining the tree..."
tf = rt.TFile.Open(ofile,"RECREATE")
tt = rt.TTree("slha","slha")
# add pointName
tt.Branch("slhapath",rt.AddressOf(myData,"slhapath"),"slhapath/C")
tt.Branch("ID",rt.AddressOf(myData,"ID"),"ID/I")
# add the blocks
for blockname in sorted(blocks.keys()):
    block = blocks[blockname]
    if block.Q is not None:
        branchname = "{0}_Q".format(blockname.lower())
        tt.Branch(branchname,rt.AddressOf(myData,branchname),branchname + "/D")
    for key,val in block.entries.iteritems():
        _key = ""
        if type(key) is tuple:
            _key = "_" + "_".join([str(x) for x in list(key)])
        elif key!= "":
            _key = "_" + str(key)
        branchname = blockname.lower() + _key
        tt.Branch(branchname,rt.AddressOf(myData,branchname),branchname + "/D")
# add the decays
for pdgId in sorted(decays.keys()):
    branchnamebase = "decay_" + str(pdgId)
    varname = branchnamebase + "_tw"
    tt.Branch(varname,rt.AddressOf(myData,varname),varname + "/D")
    ncvarname = branchnamebase + "_ndc"
    tt.Branch(ncvarname,rt.AddressOf(myData,ncvarname),ncvarname + "/I")
    varname = branchnamebase + "_br"
    tt.Branch(varname,rt.AddressOf(myData,varname),varname + "[" + ncvarname + "]/D")
    varname = branchnamebase + "_ndp"
    tt.Branch(varname,rt.AddressOf(myData,varname),varname + "[" + ncvarname + "]/I")
    varname = branchnamebase + "_id1"
    tt.Branch(varname,rt.AddressOf(myData,varname),varname + "[" + ncvarname + "]/I")
    varname = branchnamebase + "_id2"
    tt.Branch(varname,rt.AddressOf(myData,varname),varname + "[" + ncvarname + "]/I")
    varname = branchnamebase + "_id3"
    tt.Branch(varname,rt.AddressOf(myData,varname),varname + "[" + ncvarname + "]/I")
    varname = branchnamebase + "_id4"
    tt.Branch(varname,rt.AddressOf(myData,varname),varname + "[" + ncvarname + "]/I")

#####################
# run over slha files
# fill tree
#####################
print "filling the tree..."
nfiles = len(slhafiles)
for e in range(0,nfiles):
    slhafile = slhafiles[e]
    id = -9999
    if slhaIdDict != None and os.path.abspath(slhafile) in slhaIdDict:
        id = int(slhaIdDict[os.path.abspath(slhafile)]["id"])
    #print slhafile
    if e%100 == 0:
        print "processing entry",e,"of",nfiles
    # fill c++ struct
    updateMyData(myData,slhafile,id)
    # fill tree
    tt.Fill()

#####################
# write tree
#####################
tt.Write()
tf.Close()

# DONE
