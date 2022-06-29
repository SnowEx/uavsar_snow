#!/usr/bin/env python3

import os, imp, sys, glob
import numpy as np
import argparse
import isce
import isceobj
from mroipac.baseline.Baseline import Baseline
from isceobj.Planet.Planet import Planet
import datetime
import shelve

parser = argparse.ArgumentParser( description='Generate offset field between two acquisitions')
parser.add_argument('-w', type=str, dest='work_dir', required=True,
        help='Project directory')
parser.add_argument('-b', type=str, dest='baselineDir', required=True,
        help='Baseline directory')
parser.add_argument('-m', '--master_date', dest='masterDate', type=str, default=None,
            help='Directory with master acquisition')
args = parser.parse_args()
work_dir = args.work_dir
baselineDir = args.baselineDir
masterDate = args.masterDate
if not os.path.isdir(work_dir):
    print('Home directory path is incorrect or does not exist')
    sys.exit()
if not os.path.isdir(baselineDir):
    print('Baseline directory path is incorrect or does not exist')
    sys.exit()
#work_dir = os.path.expanduser("/Users/cabrera/Documents/Projects/Deltax/Processing/DeltaTest")
#baselineDir = os.path.expanduser("/Users/cabrera/Documents/Projects/Deltax/Processing/DeltaTest/baselines")
#masterDate = []

print(work_dir)
print(baselineDir)
print(masterDate)

dirs = glob.glob(work_dir+'/SLC/*')
slclist = glob.glob(work_dir+'/SLC/*/*.slc')
acquisitionDates = []
for dir in dirs:
    acquisitionDates.append(os.path.basename(dir))
acquisitionDates.sort()
if masterDate not in acquisitionDates:
    print ('master date was not found. The first acquisition will be considered as the stack master date.')
if masterDate is None or masterDate not in acuisitionDates:
    masterDate = acquisitionDates[0]
slaveDates = acquisitionDates.copy()
slaveDates.remove(masterDate)
print(acquisitionDates)
print(masterDate)
print(slaveDates)

## baseline pair
for slave in slaveDates:
    sl = os.path.join(work_dir + '/SLC',slave)
    mt = os.path.join(work_dir + '/SLC',masterDate)
    print(mt)
    print(sl)
    
    try:
            mdb = shelve.open( os.path.join(mt, 'raw'), flag='r')
            sdb = shelve.open( os.path.join(sl, 'raw'), flag='r')
    except:
            mdb = shelve.open( os.path.join(mt, 'data'), flag='r')
            sdb = shelve.open( os.path.join(sl, 'data'), flag='r')

    mFrame = mdb['frame']
    sFrame = sdb['frame']


    bObj = Baseline()
    bObj.configure()
    bObj.wireInputPort(name='masterFrame', object=mFrame)
    bObj.wireInputPort(name='slaveFrame', object=sFrame)
    bObj.baseline()
    baselineOutName = os.path.basename(mt) + "_" + os.path.basename(sl) + ".txt"
    f = open(os.path.join(baselineDir, baselineOutName) , 'w')
    f.write("PERP_BASELINE_BOTTOM " + str(bObj.pBaselineBottom) + '\n')
    f.write("PERP_BASELINE_TOP " + str(bObj.pBaselineTop) + '\n')
    f.close()
    print('Baseline at top/bottom: %f %f'%(bObj.pBaselineTop,bObj.pBaselineBottom))
    print((bObj.pBaselineTop+bObj.pBaselineBottom)/2.)
    mdb.close()
    sdb.close()
