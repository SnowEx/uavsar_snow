library(terra)

# bring in fabdem naheem got from GEE
fabdem <-rast("/Users/jacktarricone/ch1_jemez_data/new_py_inc/jemez_fabdem.tif")
fabdem
plot(fabdem)

# bring in plv
plv_km <-rast("/Users/jacktarricone/ch1_jemez_data/new_py_inc/lkv.x.tif")
values(plv_km)[values(plv_km) == 0] = NA # 0 to NaN
plv_km
plot(plv_km, add = TRUE)

# crop
fabdem_v1 <-crop(fabdem, ext(plv_km))
plot(fabdem_v1)

# resample
fabdem_v2 <-resample(fabdem_v1, plv_km)
fabdem_v2
plot(fabdem_v2)

# mask
fabdem_v3 <-mask(fabdem_v2, plv_km)
plot(fabdem_v3)
