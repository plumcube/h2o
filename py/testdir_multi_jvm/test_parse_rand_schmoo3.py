import os, json, unittest, time, shutil, sys
sys.path.extend(['.','..','py'])

import h2o, h2o_cmd
import h2o_browse as h2b
import random

# trial # 29 with num rows: 4829 parse end on  syn_prostate.csv took 5.05665111542 seconds
# 4457
# ERROR
# Exception in thread "TCP Receiver" java.lang.AssertionError: Still NOPTask #11841 class water.NOPTask
#     at water.H2ONode.remove_task_tracking(H2ONode.java:216)
#     at water.UDPAckAck.call(UDPAckAck.java:14)
#     at water.TCPReceiverThread.run(TCPReceiverThread.java:61)

def write_syn_dataset(csvPathname, rowCount, headerData, rowData):
    dsf = open(csvPathname, "w+")
    
    dsf.write(headerData + "\n")
    for i in range(rowCount):
        dsf.write(rowData + "\n")
    dsf.close()

# append!
def append_syn_dataset(csvPathname, rowData, num):
    with open(csvPathname, "a") as dsf:
        for i in range(num):
            dsf.write(rowData + "\n")

def rand_rowData():
    # UPDATE: maybe because of byte buffer boundary issues, single byte
    # data is best? if we put all 0s or 1, then I guess it will be bits?
    rowData = str(random.uniform(0,7))
    for i in range(8):
        rowData = rowData + "," + str(random.uniform(-1e59,1e59))
    return rowData

class parse_rand_schmoo(unittest.TestCase):
    def tearDown(self):
        h2o.check_sandbox_for_errors()

    @classmethod
    def setUpClass(cls):
        localhost = h2o.decide_if_localhost()
        if (localhost):
            h2o.build_cloud(2,java_heap_GB=10,use_flatfile=True)
        else:
            import h2o_hosts
            h2o_hosts.build_cloud_with_hosts()
        h2b.browseTheCloud()

    @classmethod
    def tearDownClass(cls):
        if not h2o.browse_disable:
            # time.sleep(500000)
            pass

        h2o.tear_down_cloud(h2o.nodes)
    
    def test_sort_of_prostate_with_row_schmoo(self):
        SEED = random.randint(0, sys.maxint)
        # if you have to force to redo a test
        # SEED = 
        random.seed(SEED)
        print "\nUsing random seed:", SEED

        SYNDATASETS_DIR = h2o.make_syn_dir()
        csvFilename = "syn_prostate.csv"
        csvPathname = SYNDATASETS_DIR + '/' + csvFilename

        headerData = "ID,CAPSULE,AGE,RACE,DPROS,DCAPS,PSA,VOL,GLEASON"

        rowData = rand_rowData()
        print "Hold on, creating a large base file, that we then append rows to"
        # heap was 1GB for these
        # fail 29
        # write_syn_dataset(csvPathname, 1000000, headerData, rowData)
        # fail 29
        # write_syn_dataset(csvPathname, 1080000, headerData, rowData)
        # pass
        # write_syn_dataset(csvPathname, 10000, headerData, rowData)

        # hangs on put file 2nd time. about 300MB file, 2M rows.
        # is it because the heap is just 1GB?
        totalRows = 1000000
        write_syn_dataset(csvPathname, totalRows, headerData, rowData)

        print "This is the same format/data file used by test_same_parse, but the non-gzed version"
        print "\nSchmoo the # of rows"
        for trial in range (75):
            rowData = rand_rowData()
            num = random.randint(4096, 5096)
            append_syn_dataset(csvPathname, rowData, num)
            totalRows += num
            start = time.time()

            # make sure all key names are unique, when we re-put and re-parse (h2o caching issues)
            key = csvFilename + "_" + str(trial)
            key2 = csvFilename + "_" + str(trial) + ".hex"
            # needs a big polling timeout, for the later iterations?
            key = h2o_cmd.parseFile(csvPathname=csvPathname, key=key, key2=key2, 
                timeoutSecs=150, pollTimeoutSecs=150, noPoll=True)
            print "trial #", trial, "totalRows:", totalRows, "num:", num, "parse end on ", csvFilename, \
                'took', time.time() - start, 'seconds'
            ### h2o_cmd.runInspect(key=key2)
            ### h2b.browseJsonHistoryAsUrlLastMatch("Inspect")
            h2o.check_sandbox_for_errors()


if __name__ == '__main__':
    h2o.unit_main()
