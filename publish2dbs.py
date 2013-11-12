import sys,json

from DBSAPI.dbsApi        import DbsApi
from DBSAPI.dbsPrimaryDataset       import DbsPrimaryDataset
from DBSAPI.dbsAlgorithm             import DbsAlgorithm
from DBSAPI.dbsProcessedDataset      import DbsProcessedDataset
from DBSAPI.dbsQueryableParameterSet import DbsQueryableParameterSet
from DBSAPI.dbsRun                   import DbsRun
from DBSAPI.dbsLumiSection           import DbsLumiSection
from DBSAPI.dbsFile                  import DbsFile

def decodeAsString(a):

    import types
    newDict = {}
    
    for key, value in a.iteritems():
        if type(key) == types.UnicodeType:
            key = str(key)
        if type(value) == types.UnicodeType:
            value = str(value)
        newDict.update({key : value})
            
    return newDict


def badDataSetPath(datasetPath):
    print "ERROR: bad dataset path"
    print "       dataset path format is /<PRIMARY DATASET>/<PROCESSED DATASET>/<TIER>"
    print "       e.g. : /Monopoles/Monopole200GeV_DY_526patch1/AODSIM"
    sys.exit()
    

if __name__ == "__main__":

    inputFileName = sys.argv[1]
    blockSize = int(sys.argv[2])

    dbsURL   = 'https://cmsdbsprod.cern.ch:8443/cms_dbs_ph_analysis_02_writer/servlet/DBSServlet'
    dbsApi   = DbsApi({'url' : dbsURL,   'version' : 'DBS_2_0_9', 'mode' : 'POST'})

    jsonFile = open(inputFileName)
    toPublish = json.load(jsonFile, object_hook=decodeAsString)

    for datasetPath, files in toPublish.iteritems():
        print "#################################################################################################"
        print "# insert dataset " + datasetPath
        print "#################################################################################################"
        appName = files[0]["appName"]
        appVer  = files[0]["appVer"]
        appFam  = files[0]["appFam"]
        seName  = str(files[0]["locations"][0])
        names = datasetPath.strip("/").split('/')
        if not len(names) == 3:
            badDataSetPath(datasetPath)
        primName, procName, tier = names
        if len(primName)==0 or len(procName)==0 or len(tier) == 0:
            badDataSetPath(badDataSetPath)
        print "primary dataset name:   ", primName
        print "processed dataset name: ", procName
        print "tier name:              ", tier 
        print "application name:       ", appName
        print "application version:    ", appVer
        print "se:                     ", seName
        print "#################################################################################################"

        # ------------------
        # primary dataset
        print "inserting new primary dataset..."
        primary = DbsPrimaryDataset (Name = primName, Type='test')
        if len(dbsApi.listPrimaryDatasets(primName)) == 0:
            dbsApi.insertPrimaryDataset (primary)
            print "...done"
        else:
            print "...primary dataset exists already"

        # ------------------
        # processed data set
        print "inserting processed dataset..."
        # algorithm
        psetId = DbsQueryableParameterSet(Hash = "NO_PSET_HASH2",
                                          Content = "")
        algo = DbsAlgorithm(ExecutableName = appName,
                            ApplicationVersion = appVer,
                            ApplicationFamily = appFam,
                            ParameterSetID = psetId)
        print "... created algorithm"
        dbsApi.insertAlgorithm(algo)
        print "... inserted algorithm"
        
        # processed data set
        processed = DbsProcessedDataset(PrimaryDataset = primary,
                                        AlgoList=[algo],
                                        Name = procName,
                                        TierList = tier.split("-"),
                                        ParentList = [],
                                        PhysicsGroup = "NoGroup",
                                        Status = "VALID",
                                        GlobalTag = "" )
        print "... created processed dataset"
        if len(dbsApi.listProcessedDatasets(patternPrim=primName, patternProc=procName)) != 0:
            print "... processed dataset exists already"
        else:
            dbsApi.insertProcessedDataset(processed)
            print "... inserted processed dataset"
        print "... done"


        # ------------------
        # which files are already there?
        nFilesTot = len(files)
        print "filtering out already published files..."
        publishedDbsFiles = dbsApi.listFiles(path=datasetPath)
        publishedLfn = [x['LogicalFileName'] for x in publishedDbsFiles]
        nPublishedFiles = len(publishedDbsFiles)
        for f in reversed(range(0,len(files))):
            if files[f]["lfn"] in publishedLfn:
                del files[f]
        nFiles = len(files)
        print "...done"

        print "#################################################################################################"
        print " # files in json:           ",nFilesTot
        print " # files already published: ",nPublishedFiles
        print " # new files:               ",nFiles
        print "#################################################################################################"
            
        #--------------------
        # loop over files
        count = 0
        while count < len(files):

            # ------------------
            # insert block
            print "inserting block..."
            blockName = dbsApi.insertBlock(datasetPath, None ,
                                           storage_element_list = [seName])
            block = dbsApi.listBlocks(datasetPath,
                                       block_name = blockName,
                                       storage_element_name = seName)[0]
            print "...block inserted (name: ",blockName,")"

            #--------------------
            # loop over files
            start = count
            stop = min(count+blockSize,len(files))
            _files = files[start:stop]

            dbsFiles = []

            print "preparing files for 1 block..."
            
            for file in _files:

                # the lumi list
                lumiList = []
                for runId, lumiIds in file.get("runInfo", {}).iteritems():
                    run = DbsRun (RunNumber=long(runId),
                                  NumberOfEvents=long(100),
                                  NumberOfLumiSections=long(20),
                                  TotalLuminosity=long(2222),
                                  StoreNumber=long(123),
                                  StartOfRun=long(1234),
                                  EndOfRun=long(2345))
                    dbsApi.insertRun(run)
                    for lumiId in lumiIds:
                        lumi = DbsLumiSection(LumiSectionNumber = long(lumiId),
                                              StartEventNumber = 0,
                                              EndEventNumber = 0,
                                              LumiStartTime = 0,
                                              LumiEndTime = 0,
                                              RunNumber = long(runId) )
                        lumiList.append(lumi)

                # the dbs file
                dbsFile = DbsFile(NumberOfEvents = file['events'],
                                  LogicalFileName = file['lfn'],
                                  FileSize = int(file['size']),
                                  Status = "VALID",
                                  ValidationStatus = 'VALID',
                                  FileType = 'EDM',
                                  Dataset = processed,
                                  Checksum = "NotSet",
                                  TierList = processed['TierList'],
                                  AlgoList = processed['AlgoList'],
                                  LumiList = lumiList,
                                  ParentList = [] )
                
                dbsFiles.append(dbsFile)

            # insert dbsfiles
            print "... inserting",len(dbsFiles),"files"
            dbsApi.insertFiles(datasetPath,dbsFiles, block)
            print "done"
            
            dbsApi.closeBlock(block)
            count = stop
