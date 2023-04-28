# LC_QAQC
This repo holds information to improve the efficiency of the QAQC process the Land Cover (LC) Change data.

## Overview
This script utilizes the Land Cover Change (LCC) Raster Attribute Tables (RATs) to identify area per LC transition.
This information is converted to to a change matrix, where the rows are the early date and columns are the late date.
The mapped LC transitions that are unlikely are highlighted in yellow, and the mapped transitions that should be corrected
are highlighted in red. The results of the code are written to an excel document in a new folder called QAQC, which
exists in the county input folder. 

## Requirements
### Python Packages
The code is completely open source. In a conda environment, install the below packages via "conda install"
- pandas
- geopandas
- openpyxl

### Files
The code requires a CSV which relates the LCC raster values to their descriptive land cover class names. This file is expected 
to be saved in the same directory as the script and is named "LCChange_cw_2022ed.csv".

### Folder Structure
The code requires a consistent folder structure which can exist in any user-defined directory. The structure is:
- Main directory (user-defined)
  - countyfips
    - input
      - countyfips_landcoverchange_year1_year2.tif.vat.dbf
where,

- countyfips = first 4-letters of the county, followed by an underscore and the 5-digit county fips. (Ex: Sussex, DE 10005 = suss_10005)
- year1 = the year of the early date (Ex: 2013).
- year2 = the year of the late date (Ex: 2018).

## How to Run
The code requires at least 2 user arguments from the command line:
1. path to the main directory
2. countyfips AKA cofips AKA cf. The user can enter as many cofips as they'd like, separated by a space, to run multiple counties at once.

### Example Run
To run the script from C:/code directory for Sussex, DE (suss_10005) where the main data directory containing the county folder is is C:/data
- python C:/code/LCC_matrices.py C:/data suss_10005
