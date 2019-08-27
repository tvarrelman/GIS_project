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


# Reads a list of precipitation files from the CHIRPS web-page
# (original source https://github.com/datamission/WFP/blob/master/Datasets/CHIRPS/get_chirps.py)

def get_file_list(date, daily_file_path):
    year = date[0:4]
    url = 'ftp://ftp.chg.ucsb.edu/pub/org/chg/products/CHIRPS-2.0/africa_daily/tifs/p05/' + year + '/'
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req)
    the_page = response.read()
    page = str(BeautifulSoup(the_page, features="lxml"))
    response.close()
    firstsplit = page.split('\r\n')
    secondsplit = [x.split(' ') for x in firstsplit]
    flatlist = [item for sublist in secondsplit for item in sublist]
    chirpsfiles = [x for x in flatlist if 'chirps-v2.0.' + date in x]
    # Calls the function to download the rasters
    download_files(chirpsfiles, year, daily_file_path)


# Download the CHIRP precipitation files
# (original source https://github.com/datamission/WFP/blob/master/Datasets/CHIRPS/get_chirps.py)

def download_files(chirpsfiles, year, daily_file_path):
    base = 'ftp://ftp.chg.ucsb.edu/pub/org/chg/products/CHIRPS-2.0/africa_daily/tifs/p05/' + year + '/'
    for file_name in chirpsfiles:
        chirps_file = os.path.join(daily_file_path + file_name)
        try:
            with urllib.request.urlopen(base + file_name) as response:
                open(chirps_file, 'wb').write(response.read())
        except urllib.error.URLError:
            return download_files(chirpsfiles, year)
        unzip_tiff(chirps_file)


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

    # Include the path to the shapefile & the shapefile name
    
    shape_path = ""
    shape_file_name = ''
    shape_file = os.path.join(shape_path, shape_file_name)
    shapes = gpd.read_file(shape_file)
    polygons = np.array(shapes['geometry'])
    res_union = gpd.GeoSeries(cascaded_union(polygons))
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


# Path to the folder where the daily precip will be saved

daily_path = ""

# Path to the folder where the monthly averaged precip will be saved

monthly_path = ""

get_file_list('2019.07', daily_path)
monthly_average('2019.07', daily_path, monthly_path)
