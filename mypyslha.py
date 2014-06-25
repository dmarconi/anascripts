#!/usr/bin/env python

_blockType = 0
_decayType = 1

class MyBlock:
    def __init__(self,el):
        self.type = _blockType
        self.name = el[1]
        self.Q = None
        if len(el) == 4:
            self.Q = float(el[3])
        self.entries = dict()
        
    def addEntry(self,el):
        key = el[0:-1]
        key = [int(x) for x in key]
        if len(key) == 0:
            key = ""
        elif len(key) == 1:
            key = key[0]
        else:
            key = tuple(key)
        val = float(el[-1])
        self.entries.update([[key,val]])
        
    def __str__(self):
        _str = "name:{0} Q:{1}\n".format(self.name,self.Q)
        for key,val in self.entries.iteritems():
            _str += "   {0}:{1}\n".format(str(key),str(val))
        return _str

class MyDecay:
    def __init__(self,el):
        self.type = _decayType
        self.pdgId = int(el[1])    # pdg id
        self.tw = float(el[2])     # total width
        self.br = []               # list of branching ratios, one entry per decay channel
        self.dp = []               # list of decay products, one list per decay channel
        
    def addEntry(self,el):
        self.br.append(float(el[0]))
        self.dp.append([])
        ndp = int(el[1])
        for i in range(0,ndp):
            self.dp[-1].append(int(el[2+i]))

    def __str__(self):
        _str = "tw:{0} id:{1}\n".format(self.tw,self.pdgId)
        for d in range(0,len(self.br)):
            _str+= "   br:{0} dp:{1}\n".format(self.br[d],",".join([str(x) for x in self.dp[d]]))        
        return _str



# remove comments from line and chop
def parseSLHALine(line):
    cpos = line.find("#")
    if cpos >= 0:
        line = line[0:cpos]
    if len(line) == 0:
        return []
    el = line.split()
    return el

# read the slha file and put the content in dictionaries
def parseSLHAFile(path):

    FILE = open(path)
    lines = FILE.read().split("\n")
    FILE.close()
    
    blocks = dict()
    decays = dict()

    curobj = None
    
    for l in range(0,len(lines)):
        el = parseSLHALine(lines[l])
        if len(el)==0:
            continue

        # before entering a new block or decay table, store the previous one
        if el[0] == "BLOCK" or el[0] == "DECAY":
            if curobj is not None:
                if curobj.type == _blockType:
                    blocks.update([[curobj.name,curobj]])
                elif curobj.type == _decayType:
                    decays.update([[curobj.pdgId,curobj]])
            curobj = None

        # start parsing a new block
        if el[0] == "BLOCK":
            # skipp the meta data
            if el[1].find("INFO") >= 0:
                continue
            # init the block
            curobj = MyBlock(el)

        # start parsing a new decay table
        elif el[0] == "DECAY":
            curobj = MyDecay(el)
                
        # do not parse the block before the block start was found
        elif curobj is None:
            continue

        # parse the block entry
        else:
            curobj.addEntry(el)

    # put the last obj in the dictionaries
    if curobj is not None:
        if curobj.type == _blockType:
            blocks.update([[curobj.name,curobj]])
        elif curobj.type == _decayType:
            decays.update([[curobj.pdgId,curobj]])
        curobj = None

    # return the dictionaries
    return blocks,decays

