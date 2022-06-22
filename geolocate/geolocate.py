import os
import shutil
from glob import glob
from os.path import join, basename, dirname
import warnings
import numpy as np
import rasterio as rio
from osgeo import gdal
from uavsar_pytools.convert.tiff_conversion import read_annotation

import sys
sys.path.append('/Users/zachkeskinen/Documents/uavsar_snow/functions')
from geocoding import geocodeUsingGdalWarp

def geolocate_uavsar(in_fp, ann_fp, out_dir, llh_fp):
    """
    Geolocates an image using an array of latitudes and longitudes.
    in_fp: file path of file to geolocate
    ann_fp: file path to annotation file
    out_dir: directory to save geolocated files
    llh_fp: file path to UAVSAR lat, long, elev files for georeferencing
    
    Future thoughts: expand to accept any of the other files in the SLC zip.
    Reduce scope to avoid parsing files within as much as possible.
    """

    desc = read_annotation(ann_fp)
    ext = basename(in_fp).split('.')[-1]

    tmp_dir = join(out_dir, 'tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    nrows = desc[f'llh_1_2x8.set_rows']['value']
    ncols = desc[f'llh_1_2x8.set_cols']['value']
    dt = np.dtype('<f')

    arr = np.fromfile(llh_fp, dtype = dt)
    res = {}
    res[f'llh.lat'] = arr[::3].reshape(nrows, ncols)
    res[f'llh.long'] = arr[1::3].reshape(nrows, ncols)
    res[f'llh.dem'] = arr[2::3].reshape(nrows, ncols)

    profile = {
    'driver': 'GTiff',
    'interleave': 'band',
    'tiled': False,
    'nodata': 0,
    'width': ncols,
    'height':nrows,
    'count':1,
    'dtype':'float32'
    }
    
    # Save out tifs
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Dataset has no geotransform, gcps, or rpcs. The identity matrix be returned.")
        for name, arr in res.items():
            with rio.open(join(tmp_dir, name + '.tif'), 'w', **profile) as dst:
                dst.write(arr.astype(arr.dtype), 1)

    # Add VRT file for each tif
    tifs = glob(join(tmp_dir, '*.tif')) # list all .llh files
    for tiff in tifs: # loop to open and translate .llh to .vrt, and save .vrt using gdal
        raster_dataset = gdal.Open(tiff, gdal.GA_ReadOnly) # read in rasters
        raster = gdal.Translate(join(tmp_dir, basename(tiff).replace('.tif','.vrt')), raster_dataset, format = 'VRT', outputType = gdal.GDT_Float32)
    raster_dataset = None

    vrts = glob(join(tmp_dir, '*.vrt'))
    latf = [f for f in vrts if basename(f) == 'llh.lat.vrt'][0]
    longf = [f for f in vrts if basename(f) == 'llh.long.vrt'][0]
    # for f in vrts:
    #     geocodeUsingGdalWarp(infile = f,
    #                     latfile = latf,
    #                     lonfile = longf,
    #                     outfile = join(out_dir, basename(f).replace('vrt','tif')),
    #                     spacing=[.00005556,.00005556])

    profile = {
        'driver': 'GTiff',
        'interleave': 'band',
        'tiled': False,
        'nodata': 0,
        'width': ncols,
        'height':nrows,
        'count':1,
        'dtype':'float32'
        }

    if ext == 'slc':
        os.makedirs(tmp_dir, exist_ok=True)
        spacing = in_fp.replace(f'.{ext}','')[-3:]
        dtype = desc['slc bytes per pixel']['value']
        nrows = desc[f'slc_1_{spacing} rows']['value']
        ncols = desc[f'slc_1_{spacing} columns']['value']
        if dtype == 8:
            dtype = np.complex64
        if dtype == 16:
            dtype = np.complex128
        arr = np.fromfile(in_fp, dtype = dtype).reshape(nrows, ncols)
        
        d_arrs = {}
        d_arrs['real'] = arr.real
        d_arrs['imag'] = arr.real


         # Save out tifs
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Dataset has no geotransform, gcps, or rpcs. The identity matrix be returned.")
            for name, arr in d_arrs.items():
                with rio.open(join(tmp_dir, basename(in_fp) + f'.{name}.tif'), 'w', **profile) as dst:
                    dst.write(arr.astype(arr.dtype), 1)
        
        tifs = glob(join(tmp_dir, f'*{ext}*.tif')) # list all .ext files
        for tiff in tifs: # loop to open and translate .ext to .vrt, and save .vrt using gdal
            raster_dataset = gdal.Open(tiff, gdal.GA_ReadOnly) # read in rasters
            raster = gdal.Translate(join(tmp_dir, basename(tiff).replace('.tif','.vrt')), raster_dataset, format = 'VRT', outputType = gdal.GDT_Float64)
        raster_dataset = None

        vrts = glob(join(tmp_dir, f'*{ext}*.vrt'))
        for f in vrts:
            print(f)
            geocodeUsingGdalWarp(infile = f,
                                latfile = latf,
                                lonfile = longf,
                                outfile = join(out_dir, basename(f).replace('vrt','tif')),
                                spacing=[.00005556,.00005556])

    if ext == 'lkv':
        spacing = in_fp.replace(f'.{ext}','')[-3:]
        tmp_dir = join(out_dir, 'tmp')
        os.makedirs(tmp_dir, exist_ok=True)
        nrows = desc[f'{ext}_1_{spacing}.set_rows']['value']
        ncols = desc[f'{ext}_1_{spacing}.set_cols']['value']
        dt = np.dtype('<f')

        arr = np.fromfile(in_fp, dtype = dt)
        res = {}
        res[f'{ext}.y'] = arr[::3].reshape(nrows, ncols)
        res[f'{ext}.x'] = arr[1::3].reshape(nrows, ncols)
        res[f'{ext}.z'] = arr[2::3].reshape(nrows, ncols)
        
        # Save out tifs
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Dataset has no geotransform, gcps, or rpcs. The identity matrix be returned.")
            for name, arr in res.items():
                tmp_tiff_fp = join(tmp_dir, name + '.tif')
                with rio.open(tmp_tiff_fp, 'w', **profile) as dst:
                    dst.write(arr.astype(arr.dtype), 1)

        # Add VRT file for each tif
        tifs = glob(join(tmp_dir, f'{ext}*.tif')) # list all .ext files
        for tiff in tifs: # loop to open and translate .ext to .vrt, and save .vrt using gdal
            raster_dataset = gdal.Open(tiff, gdal.GA_ReadOnly) # read in rasters
            raster = gdal.Translate(join(tmp_dir, basename(tiff).replace('.tif','.vrt')), raster_dataset, format = 'VRT', outputType = gdal.GDT_Float32)
        raster_dataset = None

        vrts = glob(join(tmp_dir, f'{ext}*.vrt'))
        for f in vrts:
            geocodeUsingGdalWarp(infile = f,
                            latfile = latf,
                            lonfile = longf,
                            outfile = join(out_dir, basename(f).replace('vrt','tif')),
                            spacing=[.00005556,.00005556])
        
    shutil.rmtree(tmp_dir)

        