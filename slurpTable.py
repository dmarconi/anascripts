#!/usr/bin/env python

import sys,glob,os

# slurp a table from txt file
def slurpTable(filenames,keyColumns=None,splitCharacter=None,dictMode=False):
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
    keyColumnIndices = None
    if not keyColumns is None:
        keyColumns = keyColumns.split(",")
        keyColumnIndices = []
    colNames = None
    data = []
    if not keyColumns is None:
        data = dict()
    # loop over all files
    for filename in filenames:
        # read file into memory
        FILE = open(filename)
        lines = FILE.read().strip().split("\n")
        FILE.close()
        # parse header line
        _colNames = lines[0].split(splitCharacter)
        if colNames is None:
            colNames = _colNames
            # check if keyColumns are there
            if not keyColumns is None:
                for col in keyColumns:
                    if not col in colNames:
                        print "ERROR: given keyColumn '{0}' is no column name in file '{1}'".format(col,filename)
                        print "       available columnn names: {0}".format(",".join(colNames))
                        sys.exit()
                    else:
                        keyColumnIndices.append(colNames.index(col))
            # creat the columnIndex dictionary
            if not dictMode:
                for n in range(len(colNames)):
                    columnIndex.update([[colNames[n],n]])
            # check column length
            goodFile = len(colNames)==len(_colNames)
            if goodFile:
                for n in range(len(colNames)):
                    if not colNames[n] == _colNames[n]:
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
            if not len(elements) == len(colNames):
                print "ERROR: inconsistent number of columns in", filename, "line",l+1
                print "       found",len(elements),"columns, expected",len(colNames)
                sys.exit()
            _entry = []
            for e in range(len(elements)):
                var = elements[e]
                try:
                    var = float(elements[e])
                except ValueError:
                    pass
                _entry.append(var)
            entry = _entry
            if dictMode:
               entry = dict()
               for e in range(len(_entry)):
                   entry.update([[colNames[e],_entry[e]]])
            if keyColumns is None:
                data.append(entry)
            elif len(keyColumns) == 1:
                data.update([[_entry[keyColumnIndices[0]],entry]])
            else:
                data.update([[tuple([_entry[i] for i in keyColumnIndices]),entry]])
    if dictMode:
        return data
    else:
        return data,columnIndex
