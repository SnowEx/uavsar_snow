
# november 10th, 2021
# jack tarricone
# almost done

####
# using the function cgrad, from the insol package
# calculate the 3d (x,y,z) unit vector for a valle grande crop of the lidar dem
# then add? not sur yet, to make surface normal vector

library(terra)
library(raster)
library(insol) # https://rdrr.io/cran/insol/man/cgrad.html


# notes from meeting with HP October 25th

### creating new incidence angle raster from CZO LiDAR data
# will be used for SWE inversion of UAVSAR data

## steps
# 1.create slope, aspect rasters from filtered DEM
# 2.reproject and resample lidar data products to UAVSAR projection (wsg-84, lat/lon)
# 3.use these resampled products to create new .inc file

# function to calculate "gradient" of LiDAR raster (vector)
# three component vector (easting, northing, 3 component vector)
# calculate dot product and calculate the angle
# dot product of gradient from lidar raster and path length vector (n1*n2+e1*e2+up1*up2)
# cos^-1((n1*n2+e1*e2+up1*up2)/(distance calc through atm for each vector))

# packages in r or python for calculating gradients and surface normals



#########################################################################

  
  
# bring in lidar dem with raster not terra
# switched back to using the raster package bc cgrad can injest only rasters not SpatRasters!
lidar_dem <-raster("/Users/jacktarricone/ch1_jemez_data/jemez_lidar/valles_elev_filt.img")
plot(lidar_dem, col = terrain.colors(3000)) # test plot

# crop down
crop_ext <-extent(359000, 374000, 3965000, 3980000) # set vg UTM extent for raster
crop_ext_sr <-ext(359000, 374000, 3965000, 3980000) # for spatrast
lidar_crop <-crop(lidar_dem, crop_ext)
plot(lidar_crop, col = terrain.colors(3000)) # test, good

# plv <-rast("/Volumes/JT/projects/uavsar/jemez/look_vector/plv_km_good.tif")
# 
# lidar_sp <-rast(lidar_crop)
# test_resamp <-resample(lidar_sp, plv, method = "bilinear")
# plot(plv)
# plot(test_resamp, add = TRUE)

########
# calculate the gradient in all three dimensions
# this function create a matrix for the x,y,z competent of a unit vector
########

grad_mat <-cgrad(lidar_crop, 1, 1, cArea = FALSE)

# make individual raster layer for each competent
# and geocode back to original crop extent
# switch back to terra

## x
x_comp <-rast(grad_mat[,,1], crs = crs(lidar_crop))
ext(x_comp) <-ext(crop_ext_sr)
plot(x_comp)

## y
y_comp <-rast(grad_mat[,,2], crs = crs(lidar_crop))
ext(y_comp) <-ext(crop_ext_sr)
plot(y_comp)

## z
z_comp <-rast(grad_mat[,,3], crs = crs(lidar_crop))
ext(z_comp) <-ext(crop_ext_sr)
plot(z_comp)


#################################
# bring in path length vector data
#################################

# final radar path length file
plv_km <-rast("/Users/jacktarricone/ch1_jemez_data/gpr_rasters_ryan/plv_km.tif")
plot(plv_km)
plv_m <-plv_km*1000

# east
radar_east_raw <-rast("/Users/jacktarricone/ch1_jemez_data/feb12-19_slc/BU/geocoded_east.tif")
values(radar_east_raw)[values(radar_east_raw) == 0] = NA # 0 to NaN
plot(radar_east_raw)

# north
radar_north_raw <-rast("/Users/jacktarricone/ch1_jemez_data/feb12-19_slc/BU/geocoded_north.tif")
values(radar_north_raw)[values(radar_north_raw) == 0] = NA # 0 to NaN
plot(radar_north_raw)

# up
radar_up_raw <-rast("/Users/jacktarricone/ch1_jemez_data/feb12-19_slc/BU/geocoded_up.tif")
values(radar_up_raw )[values(radar_up_raw) == 0] = NA # 0 to NaN
plot(radar_up_raw)

#####
# resample radar vector components up to 5.6m
#####

radar_east <-resample(radar_east_raw, plv_m, method = "bilinear")
# writeRaster(radar_east, "/Volumes/JT/projects/uavsar/jemez/new_inc/radar_east_5.6.tif")
radar_north <-resample(radar_north_raw, plv_m, method = "bilinear")
# writeRaster(radar_north, "/Volumes/JT/projects/uavsar/jemez/new_inc/radar_north_5.6.tif")
radar_up <-resample(radar_up_raw, plv_m, method = "bilinear")
# writeRaster(radar_up, "/Volumes/JT/projects/uavsar/jemez/new_inc/radar_up_5.6.tif")

######
# resample surface vector components up to 5.6m
######

x_rs <-resample(x_comp, plv_m, method = "bilinear")
# writeRaster(x_rs, "/Volumes/JT/projects/uavsar/jemez/new_inc/surface_x_5.6.tif")
y_rs <-resample(y_comp, plv_m, method = "bilinear")
# writeRaster(y_rs, "/Volumes/JT/projects/uavsar/jemez/new_inc/surface_y_5.6.tif")
z_rs <-resample(z_comp, plv_m, method = "bilinear")
# writeRaster(z_rs, "/Volumes/JT/projects/uavsar/jemez/new_inc/surface_z_5.6.tif")



# cos^-1((y_rs*radar_north+x_rs*radar_east+z_rs*radar_up)/(distance calc through atm for each vector))

# calculate surface normal
surf_norm <-(y_rs*radar_north + x_rs*radar_east + z_rs*radar_up)
plot(surf_norm)

# compute the dot product to get a inc. angle in radians
# make sure to put the negative sign!
inc_ang_rad <-(acos)(-surf_norm/(plv_km*1000))
plot(inc_ang_rad)
inc_ang_deg <-inc_ang_rad*(180/pi)
plot(inc_ang_deg)
writeRaster(inc_ang_deg, "/Users/jacktarricone/ch1_jemez_data/gpr_rasters_ryan/lidar_inc_deg.tif")
writeRaster(inc_ang_rad, "/Users/jacktarricone/ch1_jemez_data/gpr_rasters_ryan/lidar_inc_rad.tif")

















