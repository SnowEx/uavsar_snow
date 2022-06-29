# uavsar_snow
Code for using UAVSAR InSAR and PolSAR data for snow applications.

Contributors: Zachary Keskinen (Boise State University), Naheem Adebisi (Boise State University), Ross Palomaki (Montana State University), Jack Tarricone (University of Nevada, Reno). \
\
Questions? zacharykeskinen@u.boisestate.edu

## Directory Explanation:
- Geolocate: Geolocate, crop, and resample UAVSAR SLCs to ground projection.
- Incidence Angle: Calculate path lengths for UAVSAR images and incidence angles from arbitrary DEM
- PolSAR: Calculate alpha angle, entropy, anisotropy for UAVSAR polsar images
- SWE Inversion: Standardized function to invert SWE from phase changes
