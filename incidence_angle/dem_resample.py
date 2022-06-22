import numpy as np
import rasterio as rio
from rasterio.enums import Resampling
import matplotlib.pyplot as plt
import rioxarray as rxr # for the extension to load
import xarray as xr


def reample_to_uavsar_dem(path_uavsar_dem, path_new_dem):
    """
    Resamples a new dem to the same extent and resolution as the UAVSAR DEM

    Parameters
    ----------
    path_uavsar_dem, path_new_dem : str
        File path to .tifs
    Returns
    -------
    dem_resamp : np.array
        Resampled DEM
    """  

    # import dem from the geolocation function
    uavsar_dem_raw =rxr.open_rasterio(path_uavsar_dem)
    uavsar_dem = uavsar_dem_raw.where(uavsar_dem_raw != 0) # 0 to np.nan

    # import fabdem naheem downloaded from gee
    fabdem = rxr.open_rasterio(path_new_dem)

    # uavsar_dem lat lon bounds
    bounds = uavsar_dem.rio.bounds()

    # define for cropping
    min_lon = bounds[0]
    min_lat = bounds[1]
    max_lon = bounds[2]
    max_lat = bounds[3]

    # crop fabdem to uavsar extent
    fabdem_crop = fabdem.rio.clip_box(minx=min_lon, miny=min_lat, maxx=max_lon, maxy=max_lat)
    # *bounds

    # resample cropped fabdem down to uavsar resolution
    fabdem_resamp = fabdem_crop.rio.reproject_match(uavsar_dem)

    # mask fabdem by NaNs in uavsar dem, convert to np.array
    fabdem_resamp.data[np.isnan(uavsar_dem.data)] = np.nan
    dem_resamp = fabdem_resamp.data[0]

    return dem_resamp