#!/usr/bin/env python3
############################################################
# Program to run unwrap.                                   #
# Copyright (c) 2020, Talib Oliver                         #
# Author: Talib Oliver, 2020                               #
############################################################

import isce
import isceobj
import sys
import os
import argparse
import glob
import pickle
import shelve
import numpy as np
import gdal


def create_parser():
	EXAMPLE = """example:
	  run_wlc_unwrp.py -i Igrams_dir -s SLC_dir -al 12 -rl 3 
	"""
	parser = argparse.ArgumentParser(description='Script to run SNAPHU unwrap.',
                                         formatter_class=argparse.RawTextHelpFormatter,
                                         epilog=EXAMPLE)

	parser.add_argument('-i', '--ifg_dir', dest='ifg_dir', type=str, required=True,
            help='Directory containing interferograms')
	parser.add_argument('-s', '--slc_dir', dest='slc_dir', type=str, required=True,
            help='Directory containing SLCs')
	parser.add_argument('-al', '--az_looks', dest='azlooks', type=str, default='12',
            help='Looks aplied in azimuth to the interferograms')
	parser.add_argument('-rl', '--rg_looks', dest='rglooks', type=str, default='3',
            help='Looks aplied in range to the interferograms')

	return parser

def cmd_line_parse(iargs=None):
    parser = create_parser()
    inps = parser.parse_args(args=iargs)

    return inps

def getShape(file):
    dataset = gdal.Open(file, gdal.GA_ReadOnly)

    return dataset.RasterXSize , dataset.RasterYSize #(width, length)

def main(iargs=None):
    inps = cmd_line_parse(iargs)
    ifg_dir = (os.path.join(inps.ifg_dir, '')).replace('/','')
    in_folder = glob.glob(inps.ifg_dir + '/20*')
    slc_dir = (os.path.join(inps.slc_dir, '')).replace('/','')
    print ('ifgram dir =', ifg_dir)
    print ('slc_dir =', slc_dir)
    print ('interferograms folder = ', in_folder)

    for dirs in in_folder:
        date = os.path.basename(dirs)
        cmd = "cp {b}/int.json {b}/{a}/".format(a=date, b=ifg_dir)
        print (cmd)
        os.system(cmd)
        cmd = "python3 /usr/local/opt/isce/share/stripmapStack/additional_scripts/unwrap_wlc.py {b}/{a}/".format(a=date, b=ifg_dir)
        print (cmd)
        os.system(cmd)
        cmd = " mv {b}/{a}/{a}.int.pre.unw.conncomp {b}/{a}/{a}.unw.conncomp".format(a=date, b=ifg_dir)
        print (cmd)
        os.system(cmd)
        cmd = " mv {b}/{a}/{a}.int.pre.unw.conf {b}/{a}/{a}.unw.conf".format(a=date, b=ifg_dir)
        print (cmd)
        os.system(cmd)
        cmd = " rm {b}/{a}/*.pre*".format(a=date, b=ifg_dir)
        print (cmd)
        os.system (cmd)
        ### Create VRT and XML
        unwrapFile = "{b}/{a}/{a}.unw".format(a=date, b=ifg_dir)
        int_file = "{b}/{a}/{a}.int".format(a=date, b=ifg_dir)
        width, length = getShape(int_file)
        print ('width, length =', width, length)
        master = slc_dir + '/{a}'.format(a=date[0:13])
        igram_info = [width, length, unwrapFile, int_file, master, inps.rglooks, inps.azlooks]

        ## Amplitude layer, taken from the interferogram
        ds = gdal.Open(int_file, gdal.GA_ReadOnly)
        igram = ds.GetRasterBand(1).ReadAsArray()
        ds = None
        amp = np.abs(igram) # Compute amplitude from ifg

        # add amp file to unwrapped ifgram
        f1 = unwrapFile
        X1 = np.memmap(f1, dtype=np.float32)
        igram_unw = X1.reshape((length,width))
        unw_pha = igram_unw

        ## Generate 2 band unw product
        new_unw = unwrapFile
        unw_data = np.array(np.hstack((amp, unw_pha)), dtype=np.float32)
        unw_data.tofile(new_unw)

        def extractInfoFromPickle(pckfile, igram_info):
            '''
            Extract required information from pickle file.
            '''
            from isceobj.Planet.Planet import Planet
            from isceobj.Util.geo.ellipsoid import Ellipsoid

            with shelve.open(pckfile,flag='r') as db:
                # frame = db['swath']
                burst = db['frame']

                #burst = frame.bursts[0]
                planet = Planet(pname='Earth')
                elp = Ellipsoid(planet.ellipsoid.a, planet.ellipsoid.e2, 'WGS84')

                data = {}
                data['wavelength'] = burst.radarWavelegth

                sv = burst.orbit.interpolateOrbit(burst.sensingMid, method='hermite')
                pos = sv.getPosition()
                llh = elp.ECEF(pos[0], pos[1], pos[2]).llh()
                data['altitude'] = llh.hgt

                hdg = burst.orbit.getHeading()
                data['earthRadius'] = elp.local_radius_of_curvature(llh.lat, hdg)

                #azspacing  = burst.azimuthTimeInterval * sv.getScalarVelocity()
                azres = 20.0 

                #data['corrlooks'] = inps.rglooks * inps.azlooks * azspacing / azres
                data['rglooks'] = igram_info[5]
                data['azlooks'] = igram_info[6]

                return data

        interferogramDir = os.path.dirname(int_file)
        masterShelveDir = os.path.join(interferogramDir , 'masterShelve')
        if not os.path.exists(masterShelveDir):
            os.makedirs(masterShelveDir)

        master = os.path.dirname(igram_info[4])
        cpCmd='cp ' + os.path.join(igram_info[4], 'data*') +' '+masterShelveDir
        os.system(cpCmd)
        pckfile = os.path.join(masterShelveDir,'data')
        print(pckfile)
        metadata = extractInfoFromPickle(pckfile, igram_info)

        ######Render XML
        outImage = isceobj.Image.createUnwImage()
        outImage.setFilename(unwrapFile)
        outImage.setWidth(width)
        #outImage.setLength(length)
        outImage.bands = 2
        #outImage.dataType = 'FLOAT'
        outImage.setAccessMode('read')
        outImage.renderHdr()
        outImage.renderVRT()

        #####Check if connected components was created
        connImage = isceobj.Image.createImage()
        connImage.setFilename(unwrapFile+'.conncomp')
        #At least one can query for the name used
        #self.insar.connectedComponentsFilename = unwrapName+'.conncomp'
        connImage.setWidth(width)
        connImage.setAccessMode('read')
        connImage.setDataType('BYTE')
        connImage.renderHdr()
        connImage.renderVRT()

###################
if __name__ == "__main__":
    main(sys.argv[1:])
