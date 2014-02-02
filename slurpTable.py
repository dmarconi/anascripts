#!/usr/bin/env python

import sys,glob,os

# slurp a table from txt file
def slurptable(filenames,dictMode=False,splitCharacter=" "):
    filenames = filenames.split(",")
    # expand regular expressions
    _filenames = []
    for _name in filenames:
        _filenames.extend(glob.glob(_name))
        if len(_filenames) == 0:
            print "ERROR: no such files:",_name
            sys.exit()

    filenames = _filenames
    columnIndex = dict()
    rownames = None
    data = []
    if dictMode:
        data = dict()
    # loop over all files
    for filename in filenames:
        # read file into memory
        FILE = open(filename)
        lines = FILE.read().strip().split("\n")
        FILE.close()
        # parse header line
        _rownames = lines[0].split(splitCharacter)
        if rownames is None:
            rownames = _rownames
            for n in range(len(rownames)):
                if dictMode:
                    if n==0:
                        continue
                    columnIndex.update([[rownames[n],n-1]])
                else:
                    columnIndex.update([[rownames[n],n]])
            goodFile = len(rownames)==len(_rownames)
            if goodFile:
                for n in range(len(rownames)):
                    if not rownames[n] == _rownames[n]:
                        goodFile = False
                        break
            if not goodFile:
                print "ERROR: inconsistency between headers in different parameter files"
                sys.exit()
        # parse data
        for l in range(1,len(lines)):
            line = lines[l]
            if line.find("#")==0: continue
            elements = line.split(splitCharacter)
            if not len(elements) == len(rownames):
                print "ERROR: inconsistent number of columns in", filename, "line",l+1
                print "       found",len(elements),"columns, expected",len(rownames)
                sys.exit()
            entry = []
            for element in elements:
                var = element
                try:
                    var = float(element)
                except ValueError:
                    pass
                entry.append(var)
            if dictMode:
                data.update([[entry[0],entry[1:]]])
            else:
                data.append(entry)
    return columnIndex,data
