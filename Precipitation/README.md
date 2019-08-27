# Precipitation download and processing scripts

The \textbf{download_crop_avg_CHIRPS.py} scipt is meant to be a comprehensive script that handles most of your data processing needs. The code contains the following functions:

\textbf{1. get_file_list():} This function scrapes the CHIRPS ftp page, and retrieves a list of daily rasters given a certain year and month. This code was originally obtained from (https://github.com/datamission/WFP/blob/master/Datasets/CHIRPS/get_chirps.py)

\textbf{2. download_files():} Takes the file list retrieved from the get_file_list function, and downloads the files. This code was originally obtained from (original source https://github.com/datamission/WFP/blob/master/Datasets/CHIRPS/get_chirps.py), however modified to be able to handle a large number of url requests.

\textbf{3. unzip_tif():} The download_files() function downloads the rasters in compressed form, so this function unzips the files, and writes the .tif files.

\textbf{4. crop_tif():} Crops the precipitation raster that covers all of Africa down to a smaller region and saves the new raster to the place of the original raster.

\textvf{5. monthly_average():} Takes the daily precipitation rasters for a given month (given they have been downloaded), and creates a raster that is a monthly average.

The code required that the user inputs their desired shapefile, the paths to the folders where the daily and monthly rasters should be saved, as well as the month and year that the user wishes to download data for. 
