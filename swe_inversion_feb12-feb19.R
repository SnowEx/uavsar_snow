# SWE inversion for 2/12-2/19


# path length corrected unwrapped phase data
# lidar incidence angle raster
# use change in HQ met SWE as 0 point

# jack tarricone
# feb23, 2021

# update march 7th using pit location!
# systematically extract values from 8 points around cell pit

library(terra)
library(ggplot2)

# set home folder
setwd("/Users/jacktarricone/ch1_jemez_data/gpr_rasters_ryan/")
list.files() #pwd

# import corrected unwrapped phase data
unw_raw <-rast("unw_corrected_feb12-19.tif")
unw_raw
plot(unw_raw)

# import i_angle raster and resample to unw grid bc of slight extent difference
lidar_inc_raw <-rast("lidar_inc_deg.tif")
lidar_inc_v1 <-resample(lidar_inc_raw, unw_raw)

# set crop extent and crop for better visualization
crop_ext <-ext(-106.57, -106.38, 35.81, 35.96) 
lidar_inc <-crop(lidar_inc_v1, crop_ext)

# mask and crop unwrapped phase data down to extent on new inc angle raster
unw_crop <-crop(unw_raw, crop_ext)
unw <-mask(unw_crop, lidar_inc)

# plot results
plot(lidar_inc)
plot(unw)

####################################
###### bring in fsca layers ########
####################################

# fsca
fsca_raw <-rast("landsat_fsca_2-18.tif")

# crop to .inc angle extent and mask
fsca_crop <-crop(fsca_raw, ext(lidar_inc))
fsca <-mask(fsca_crop, lidar_inc)
plot(fsca)

# create snow mask
snow_mask <-fsca
values(snow_mask)[values(snow_mask) > 1] = 1
plot(snow_mask)
# writeRaster(snow_mask,"02_18_2020_snow_mask.tif")

# masked the unwrapped phase with snow mask
unw_snow_mask <- mask(unw, snow_mask, maskvalue = NA)
plot(unw)
plot(unw_snow_mask)

########################################################
######### converting phase change to SWE ##############
########################################################

#######################################################################
# don't pick denisty and di_elec value
# pick a density and LWC (from ryans equations and field measurements)
# vary density and LWC over range over measured values
########################################################################

# table ryan sent over
pit_info <-read.csv("/Users/jacktarricone/ch1_jemez_data/pit_data/perm_pits.csv")

# ## define static information from pits
# # calculate density
# mean_density_feb12 <- pit_info$mean_density[1]
# mean_density_feb20 <- pit_info$mean_density[2]
# 
# # mean density between two flights
# mean_density_feb12_20 <-(mean_density_feb12 + mean_density_feb20)/2

# dielctric constant k
k_feb12 <- pit_info$mean_k[1]
k_feb20 <- pit_info$mean_k[2]

# mean k between two flights
mean_k_feb12_20 <-(k_feb12+k_feb20)/2

#######################
#### swe inversion ####
#######################

# first step, define function for insar constant

# inc = incidence angle raster [deg]
# wL = sensor save length [cm]
# k = dielectric permittivty 

# radar wave length from uavsar annotation file
uavsar_wL <- 23.8403545

insar_constant <-function(inc, wL, k){
  (-(4*pi)/wL)*(cos(inc) - sqrt(k - sin((inc)^2)))
  }

# create the insar constant raster
# because of the variation of .inc angle, this value you will change on pixelwise basis
insar_constant_rast <-insar_constant(inc = lidar_inc, wL = uavsar_wL, k = mean_k_feb12_20)
hist(insar_constant_rast, breaks = 100)
plot(insar_constant_rast)

#do swe change calc with masked unwrapped phase data
dswe_raw <-insar_constant_rast*unw_snow_mask
plot(dswe_raw)
hist(dswe_raw, breaks = 100)
# writeRaster(dswe_raw,"./final_swe_change/raw_dswe_feb12_19.tif")


#######################################
### calculating absolute SWE change ###
#######################################

# using swe change from the pit as "known" change point

# extent around gpr transect
gpr <-ext(-106.5255, -106.521, 35.856, 35.8594)
dswe_crop <-crop(dswe_raw, gpr)
plot(dswe_crop)

# pull out location info into separate df
loc <-data.frame(lat = pit_info$lat[1],
                 lon = pit_info$lon[1])

# plot pit location using terra vector funcitonality
pit_point <-vect(loc, geom = c("lon","lat"), crs = crs(unw))
points(pit_point, cex = 1)

# extract cell number from pit lat/lon point
pit_cell_v1 <-cells(dswe_raw, pit_point)
cell_number <-pit_cell_v1[1,2]
cell_number

# define neighboring cells by number and create a vector
neighbor_cells <-c(adjacent(dswe_raw, cells = cell_number, directions ="8"))

# add orginal cell back to vector
cell_vector <-c(cell_number, neighbor_cells)

# extract using that vector
nine_cell_dswe <-terra::extract(dswe_raw, cell_vector,  cells = TRUE, xy = TRUE)
nine_cell_dswe

# mean of 9 swe changes around
mean_pit_dswe <-mean(nine_cell_dswe[1:9,1])
mean_pit_dswe

# subtract average swe change value to great absolute swe change
# therefor pixels around the pit will show no swe change
# which is consistent with what was observed on the ground
dswe_abs <-dswe_raw - mean_pit_dswe
plot(dswe_abs)
hist(dswe_abs, breaks = 100)

# save
writeRaster(dswe_abs,"./final_swe_change/dswe_feb12-19.tif")


