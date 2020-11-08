# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 13:06:28 2019

@author: tannervarrelman
"""

import numpy as np
from osgeo import gdal
import os
import rasterio
import geopandas as gpd
from shapely.ops import cascaded_union
import rasterio.mask
from rasterio.warp import calculate_default_transform, reproject
import urllib
from bs4 import BeautifulSoup
import http.cookiejar as cookie
import datetime
from datetime import datetime
import pandas as pd
import time


def tile_list(date):
    try:
        url = 'https://e4ftl01.cr.usgs.gov/MOLT/MOD13C2.006/'+date+'/'
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req)
        the_page = response.read()
        page = BeautifulSoup(the_page, 'html.parser')
        response.close()
    except Exception as e:
        if str(e) == 'HTTP Error 404: Not Found':
            print('Data outage?',' ', 'Date:', date)
            return
        
    full_file_list=[]
    for a in page.find_all('a', href=True):
        full_file_list.append(a['href'])
        hdflist=[file for file in full_file_list if '.hdf' and not '.jpg' in file]
        hdflist2=[file for file in hdflist if 'MOD13C2' and not '.xml' in file]
        final_list=hdflist2[7:]

    if len(final_list) > 1:
        print(final_list)
        return
    link_list=[]
    hdf_list=[]
    link=os.path.join(url,final_list[0])
    link_list.append(link)
    hdf_list.append(link.split('/')[6])
    Download_Files(link)


def Download_Files(link2): 

    username = ''
    password = ''
    try:
        password_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(None, "https://urs.earthdata.nasa.gov", 
                                  username, password) 
        cookie_jar = cookie.CookieJar()
        opener = urllib.request.build_opener(
                urllib.request.HTTPBasicAuthHandler(password_manager),
                urllib.request.HTTPCookieProcessor(cookie_jar))
        urllib.request.install_opener(opener)
        request = urllib.request.Request(link2)
        response = urllib.request.urlopen(request)

        open(LST_path+link2.split('/')[6], 'wb').write(response.read())

    except Exception as e:
        print(e)
        Download_Files(link2)
    crop_raster(link2.split('/')[6])
        
def crop_raster(file):
    ds=gdal.Open(LST_path+file)
    subdata_list=ds.GetSubDatasets()
    proper_file=subdata_list[0][0]
    gdal.BuildVRT("/vsimem/temp.vrt", subdata_list[0][0])
    with rasterio.open("/vsimem/temp.vrt") as src:
        dst_crs = 'EPSG:4326'
        transform, width, height = calculate_default_transform(
                                    src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
                        'crs': dst_crs,
                        'transform': transform,
                        'width': width,
                        'height': height,
                        'driver': 'GTiff'
                    })
        band=src.read(1)
        dest = np.empty(shape=(height, width),dtype='int16')
        with rasterio.open("/vsimem/crs_repro.tif", 'w', **kwargs) as dst:
            reproject(
                    source=band,
                    destination=dest,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=rasterio.warp.Resampling.bilinear)
            dst.write(dest,1)
    #Then crop the raster to the Africa shapefile    
    with rasterio.open("/vsimem/crs_repro.tif") as src:
        out_image, out_transform = rasterio.mask.mask(src, res_union[0],
                                                      crop=True,all_touched=True, nodata=-3000)
        out_image=out_image.astype('float32')
        out_image=(out_image*0.0001)
        out_image[out_image<0]=-9999
        out_meta = src.meta.copy()
        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform,
                         "nodata":-9999,
                         "dtype":'float32'})
        new_name='MOD13C2.006_monthly_'+file_date+'.tif'
        with rasterio.open(daily_path+new_name, "w", **out_meta) as dst:
            dst.write(out_image)


#date='2001.01.01'
LST_path=''
daily_path=''
shape_path=''
shapes=gpd.read_file(shape_path+'foc.shp')
shapes_df=shapes['geometry']
shapes_df=shapes.buffer(0.0001) 
res_union = gpd.GeoSeries(cascaded_union(shapes_df))

date='2020.09.01'
file_date='2020_09_01'
tile_list(date)

















