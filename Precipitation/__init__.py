#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  8 15:26:09 2018
@author: varr3316
"""

from bs4 import BeautifulSoup
import urllib
import gzip
import rasterio
import os
import geopandas as gpd
import rasterio.mask
from shapely.ops import cascaded_union
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Reads a list of precipitation files from the CHIRPS web-page
def get_file_list(date, daily_file_path):
    year = date[0:4]
    # The daily precip rasters are stored in folders according to year.
    # Here we add the year of interest to the url string. 
    url = 'ftp://ftp.chg.ucsb.edu/pub/org/chg/products/CHIRPS-2.0/africa_daily/tifs/p05/' + year + '/'
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req)
    the_page = response.read()
    page = str(BeautifulSoup(the_page, features="lxml"))
    response.close()
    firstsplit = page.split('\r\n')
    secondsplit = [x.split(' ') for x in firstsplit]
    flatlist = [item for sublist in secondsplit for item in sublist]
    #We then subset the list of daily files for only those that include the dates of interest.
    chirpsfiles = [x for x in flatlist if 'chirps-v2.0.' + date in x]
    # Calls the function to download the rasters
    # We feed the list of files that we want to download to the download_files functions
    download_files(chirpsfiles, year, daily_file_path)

# Download the CHIRP precipitation files
def download_files(chirpsfiles, year, daily_file_path):
    base = 'ftp://ftp.chg.ucsb.edu/pub/org/chg/products/CHIRPS-2.0/africa_daily/tifs/p05/' + year + '/'
    for file_name in chirpsfiles:
        chirps_file = os.path.join(daily_file_path + file_name)
        try:
            with urllib.request.urlopen(base + file_name) as response:
                open(chirps_file, 'wb').write(response.read())
        except urllib.error.URLError:
            return download_files(chirpsfiles, year)
        # We used to have to use the unzip function because the chirps files were stored in compressed folders.
        # Starting in May, the files are no longer compressed, so we skip straight to the crop_tif function.
       # unzip_tiff(chirps_file)
        crop_tif(chirps_file)

# The files are compressed so we need to unzip them
def unzip_tiff(chirps_file):
    unzip = gzip.open(chirps_file, 'rb')
    unziptiff = open(chirps_file.split('.gz')[0], 'wb')
    unziptiff.write(unzip.read())
    unzip.close()
    unziptiff.close()
    os.remove(chirps_file)
    # Call the cropping function
    crop_tif(chirps_file.split('.gz')[0])

# Crop the files to the desired area, given a shapefile and the path to such file
def crop_tif(rast):
    #Provide a path to the West Africa Shapefile
    shape_path='/WAfricaSF/'
    shapes=gpd.read_file(shape_path+'foc.shp')
    shapes_df=shapes['geometry']
    shapes_df=shapes.buffer(0.0001) 
    # Taking a union of the geometries makes it so we have one continuous shape to crop to.
    # Otherwise, we will crop country boundary lines into our rasters.
    res_union = gpd.GeoSeries(cascaded_union(shapes_df))
    with rasterio.open(rast) as src:
        out_image, out_transform = rasterio.mask.mask(src, res_union[0], crop=True, nodata=-9999, all_touched=True)
        out_image = out_image.astype('float32')
        out_meta = src.meta.copy()
        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform,
                         "nodata": -9999,
                         "dtype": 'float32'})
        with rasterio.open(rast, "w", **out_meta) as dst:
            dst.write(out_image)

# Create a tiff w/ the monthly averaged precipitation            
def monthly_average(date, file_path, monthly_file_path):
    file_repo = os.listdir(file_path)
    files = [f for f in file_repo if 'chirps-v2.0.' + date in f]
    data_list = []
    for i in range(0, len(files)):
        raster = rasterio.open(file_path + files[i])
        data = raster.read(1).astype('float32')
        data[data < 0] = np.nan
        data_list.append(data)
    mean_data = np.nanmean(data_list, axis=0)
    mean_data[np.isnan(mean_data)] = -9999
    new_file = 'chirps-v2.0.' + date + '.01.tif'
    with rasterio.open(file_path + files[0]) as src:
        out_meta = src.meta.copy()
        with rasterio.open(monthly_file_path + new_file, "w", **out_meta) as dst:
            dst.write(mean_data, 1)

if __name__ == "__main__":
    # Path where the daily files will be solved
    daily_path = ""
    # Path where the monthly averaged precip is saved
    monthly_path = ""
    # Provide the date and month for the precip that you want
    get_file_list('2020.08', daily_path)
    # Run the monthly average function if you want raster that is the monhtly average precip
    monthly_average('2020.08', daily_path, monthly_path)
            
            
