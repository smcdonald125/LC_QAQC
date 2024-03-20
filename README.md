# LCC_QAQC
This repo holds methods to improve the efficiency of the QAQC process the Land Cover Change (LCC) data.

## Overview
This repo utilizes the Land Cover Change (LCC) Raster Attribute Tables (RATs) to identify area per LC transition
for each change period (T1-T2 and T2-T3) and each version (2022ed and 2024ed) in the form of change matrices,
or pivot tables. The mapped LC transitions that are unlikely are highlighted in yellow, and the mapped 
transitions that should be corrected are highlighted in red. 

For the change period available in both versions of data, they are differenced (2024 edition - 2022 edition), and 
normalized by total change area from the 2024 edition. 

The total mapped area of each land cover class from each change raster for both versions are calculated and
recorded.

## Requirements
### Python Packages
The code is completely open source. In a conda environment, install the below packages via "conda install", or
create the environment "LCC_QAQC" using the environment.yml file via "conda env create -f environment.yml".
- pandas
- geopandas
- openpyxl
- toml

### Folder Structure
The code requires a consistent folder structure which can exist in any user-defined directory. The structure is:
- Main directory (user-defined)
  - countyfips
    - input
      - countyfips_landcoverchange_year1_year2.tif.vat.dbf
      
where,

- countyfips = first 4-letters of the county, followed by an underscore and the 5-digit county fips. (Ex: Sussex,
  DE 10005 = suss_10005)
- year1 = the year of the early date (Ex: 2013).
- year2 = the year of the late date (Ex: 2018).

## How to Run
### Configuration File
The config.toml file is the only file that should be edited by a user. The variables to fill out are:

  - landuse_24ed = parent folder containing cf folders of the new 2024 edition data
  - landuse_22ed = parent folder containing cf folders of the published 2022 edition data
  - qaqc = folder to write results to
  - logging = path to folder to write log file
  - lcchange = path to LC change raster lookup (2024 edition), titled lcchange_lookup_2024ed.csv in 
    cic/landuse/lookup_tables
  - lc_dates = path to table with t1, t2, and t3 mapped years by cofips, titled landcover_dates.csv in 
    cic/landuse/lookup_tables

### Command Line Interface (CLI)
  --cfs COFIPS identifier for the jurisdiction(s) to be processed. If passing more than one, separate by only 
  a comma (no spaces). For example, to pass caro_51033 and balt_24005, pass caro_51033,balt_24005

  --cofips-lookup Path to CSV table containing a column of cofips to QA. Requires --column-name to be passed.
  
  --column-name Name of column in cofips-lookup containing cofips to QA. Requires --cofips-lookup to be passed.

### Example Run
Using the --cfs CLI argument:
  - python LCC_QAQC.py --cfs=suss_10005

Using a CSV:
  - python LCC_QAQC.py --cofips-lookup=/path/to/lookup.csv --column-name=cf_column_name

## Interpreting Results
### Land Cover Abbreviations
WATR = Water

EMWT = Emergent Wetlands

TREE = Tree Canopy

SHRU = Shrubland

LVEG = Low Vegetation

BARR = Barren

IMPS = Impervious Structures

IMPO = Other Impervious

ROAD = Impervious Roads

TCIS = Tree Canopy Over Impervious Structures

TCIO = Tree Canopy Over Other Impervious

TCIR = Tree Canopy Over Impervious Roads

ABPG = Aberdeen Proving Ground

### File Description
Each county will produce an excel workbook named cofips_LCC_QA.xlsx, where cofips is the cofips of the county. 
The workbook will have 5 sheets. 

The first three sheets represent change matrices of land cover change in acres, named in the format
####-####-version, where the first #### is the early year, the second #### is the later year, and version is 
either the 2022 or 2024 edition. For example, 2014-2018-2024ed is the 2024 edition of the 2014-2018 change period.
The three sheets are the T1-T3 change period for the 2022 edition, and the T1-T2 and T2-T3 change period for the
2024 edition.

The fourth sheet represents the difference between the 2022 edition and 2024 edition of the T1-T2 change period.
This sheet is named ####-####_2024ed-2022ed, where the first #### is the t1 year and the second #### is the t2 
year. These data are percentages, calculated (2024 edition change - 2022 edition change) / total 2024 edition 
change.

The fifth sheet, LC_Totals, contains the total acres of each land cover class from each change dataset from both 
versions of data. The columns in this sheet are named in the format year_####_version, where year is the year, #### 
is the last 2-digits of the change period (2014-2018 is 1418, etc.), and version is 2022 edition or 2024 edition. 

### What Do I Look For?
#### Illogical Transitions
For the 2024 edition change matrices, illogical transitions will be highlighted in yellow and invalid transitions 
in red. 

Yellow means the transitions are unlikely, but not impossible. Take into account the total amount of area. Compare 
the illogical transition area to the total area in the county from the LC_totals tab. Is this significant compared 
to the county size? If yes, or even maybe, visually QA the change data for this transition. Is this a persistent 
error or is it real?

Transitions that are highlighted in red should not exist. If any cells are highlighted in red, note that as a 
required fix. This is not a reason to halt the QA of the county.

#### Versioning Errors
Another perspective to QA change is by comparing the change from the 2024 version with the 2022 version for the T1-T2 change period. 
Looking at this tab, since it is already normalized to the amount of change, we can quickly see if there are any significant differences. 

TBD- are any of these that we'd expect? Check with UVM? For example, lveg-shrub
