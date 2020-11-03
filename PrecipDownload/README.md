# Precipitation download and processing scripts

The **DownloadPrecip/__init__.py** scipt was developed to download daily and monthly precipitation rasters spanning West Africa. To this end, the program retrieves daily precipitation rasters from the CHIRPS precipitation data set (https://www.chc.ucsb.edu/data/chirps), crops those rasters to a specified region, and then creates an averaged raster based on the daily rasters from a particular month. The code contains the following functions:

**1. get_file_list():** This function scrapes the CHIRPS data set and retrieves a list of daily rasters for a specified year and month.

**2. download_files():** Takes the file list retrieved from the get_file_list function, and downloads the files.

**3. unzip_tif():** Older files in the CHIRPS data set are compressed, so this function unzips the files and writes the .tif to memory.

**4. crop_tif():** Crops the precipitation raster that covers all of Africa down to a smaller region and saves the new raster to the place of the original raster.

**5. monthly_average():** Takes the daily precipitation rasters for a given month (given they have been downloaded), and creates a raster that is a monthly average.

The code requires that the user input the paths to where the files will be saved, as well as the year and month that the user wishes to download data for. 
