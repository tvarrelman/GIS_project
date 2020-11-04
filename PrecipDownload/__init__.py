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
import pandas as pd
import argparse
import warnings

# Reads a list of precipitation files from the CHIRPS web-page
def get_file_list(date, daily_file_path):
    year = date[0:4]
    # The daily precip rasters are stored in folders according to year.
    # Here we add the year of interest to the url string. 
    url = 'https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_daily/tifs/p05/' + year + '/'
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req)
    page = response.read()
    pretty_page = BeautifulSoup(page, features="lxml")
    response.close()
    link_list = []
    # Find all of the links on the page
    for link in pretty_page.find_all('a', href=True):
        link_list.append(link['href'])
    # We then subset the link list to only inlcude links with the chirps filename.
    chirpsfiles = [x for x in link_list if 'chirps-v2.0.' + date in x]
    # Calls the function to download the rasters
    # We feed the list of files that we want to download to the download_files functions
    download_files(chirpsfiles, year, daily_file_path)

# Download the CHIRP precipitation files
def download_files(chirpsfiles, year, daily_file_path):
    url = 'https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_daily/tifs/p05/' + year + '/'
    for file_name in chirpsfiles:
        chirps_file = os.path.join(daily_file_path + file_name)
        try:
            with urllib.request.urlopen(url + file_name) as response:
                open(chirps_file, 'wb').write(response.read())
        except urllib.error.URLError:
            return download_files(chirpsfiles, year)
        # If the raster file is zipped, we call the unzip_tiff function.
        # Else, we crop the downloaded raster file.
        if chirps_file.endswith('.gz'):
            unzip_tiff(chirps_file)
        else:
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
    # Provide a path to the West Africa Shapefile
    shape_path= '../WAfricaSF/'
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
    for rast_file in files:
        raster = rasterio.open(file_path + rast_file)
        data = raster.read(1).astype('float32')
        data[data < 0] = np.nan
        data_list.append(data)
    # Catch RuntimeWarnings triggered by averaging empty slices.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        mean_data = np.nanmean(data_list, axis=0)
    mean_data[np.isnan(mean_data)] = -9999
    new_file = 'chirps-v2.0.' + date + '.01.tif'
    with rasterio.open(file_path + files[0]) as src:
        out_meta = src.meta.copy()
        with rasterio.open(monthly_file_path + new_file, "w", **out_meta) as dst:
            dst.write(mean_data, 1)

parser = argparse.ArgumentParser(description='Parameters required to run the PrecipDownload program')
parser.add_argument('-dfp', '--daily_file_path', required=True, help='directory where daily precip rasters will be stored')
parser.add_argument('-mfp', '--monthly_file_path', required=True, help='directpry where a monthly avg. precip raster will be stored')
parser.add_argument('-y', '--year', required=True, help='year for data request')
parser.add_argument('-m', '--month', required=True, help='month for data request')
args = parser.parse_args()

try:
    daily_path = args.daily_file_path
    monthly_path = args.monthly_file_path
    year = args.year
    month = args.month
    date = year + '.' + month
except IOError as ioe:
    print(ioe)

if __name__ == "__main__":
    # Running this function will download and crop daily precip rasters
    get_file_list(date, daily_path)
    # Run the monthly average function if you want raster that is the monhtly average precip
    monthly_average(date, daily_path, monthly_path)
            
            
