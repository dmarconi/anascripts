#!/usr/bin/env python

import  json, sys, glob
from xml.etree.ElementTree import ElementTree

fjrdir = sys.argv[1].rstrip("/")
datasetPath = sys.argv[2]     #example - /SMS-T1ttttProtoScan_Mgluino-350to1200_mLSP-0to400_8TeV-Pythia6Z/StoreResults-PU_START52_V5_FullSim-v1/USER
versionNumber = sys.argv[3]   #example - 1
globalTag = sys.argv[4]       #example - START52_V9::All
appFam = sys.argv[5]          #example - FastSim
CMSSWVer = sys.argv[6]        #example - CMSSW_5_2_4_patch1
location = sys.argv[7]        #example - cmssrm.fnal.gov
accEra = sys.argv[8]          #example - Spring12
outputFileName = sys.argv[9]  #example - T1tttt.json

fjrFileNames = glob.glob(fjrdir + '/*fjr*xml') #location of your fjr files. May need to change the 'fjr*xml' to match whatever pattern you fjr follow.

array = []
id = 1

array = []

for fjrFileName in fjrFileNames:
    print fjrFileName

    tree = ElementTree()
    tree.parse(fjrFileName)

    lfn = tree.findtext("LFN").strip()
    #cksum = tree.findtext("Checksums").strip().rstrip("}").lstrip("{")
    #if not len(cksum) == 0:
    #    cksum = cksum.split(":")[1].strip("'")
    #else:
    #    cksum = "NotSet" 
    size = tree.findtext("Size").strip()
    events = tree.findtext("TotalEvents").strip()
    runs = tree.findall("Runs/Run")
    rundict = {}
    for run in runs:
        runId = run.get("ID")
        lumis = run.findall("LumiSection")
        lumilist = []
        for lumi in lumis:
            lumilist.append(lumi.get("ID"))
        rundict.update([[runId,lumilist]])
        
    array.append(
        { "status": "NOTUPLOADED",
          "globalTag": globalTag,
          "appName": "cmsRun",
          "appFam": appFam,
          "lfn":lfn,
          "locations": [location],
          "psetHash": "GIBBERISH",
          #"checksums": {"cksum":cksum},
          "checksums": {"cksum":"NotSet"},
          "id": id,
          "size": size,
          "runInfo": rundict,
          "appVer": CMSSWVer,
          "processing_ver": "v" + versionNumber,
          "acquisition_era": accEra,
          "events": events,
          "datasetPath": datasetPath}
        )
    id+=1


    
toPublish = {
    datasetPath : array
    }
    
    
file = open(outputFileName, 'w')
json.dump(toPublish, file)
file.close()
    
