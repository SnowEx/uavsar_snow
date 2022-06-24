# create path length raster
# redoing jan 27

library(terra)

setwd("/Users/jacktarricone/ch1_jemez_data/gpr_rasters_ryan") 

###########################################################
##### read in look vector new geotiffs from python code ###
###########################################################

# LKV file (.lkv): look vector at the target pointing from the aircraft to the ground, 
# in ENU (east, north, up) components.

# up in meters
up <-rast("/Users/jacktarricone/ch1_jemez_data/feb12-19_slc/BU/geocoded_up.tif")
up
plot(up)

# north in meters
north <-rast("/Users/jacktarricone/ch1_jemez_data/feb12-19_slc/BU/geocoded_north.tif")
north
plot(north)

# east in meters
east <-rast("/Users/jacktarricone/ch1_jemez_data/feb12-19_slc/BU/geocoded_east.tif")
east
plot(east)

# function triangulate distance to plane from up and east rasters
plv_km_convert <-function(east_rast, up_rast, north_rast){
  
plv_m <-((east_rast^2)+(up_rast^2)+(north_rast^2))^.5
plot(plv_m)
plv_km <-plv_m/1000
return(plv_km)

}

# convert
plv_km <-plv_km_convert(east,up,north)
values(plv_km)[values(plv_km) == 0] = NA
plot(plv_km)
plv_km
# writeRaster(plv_km, "plv_km_good.tif")

