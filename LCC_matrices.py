"""
Script: LCC_matrices.py
Purpose: This script utilizes the Land Cover Change (LCC) Raster Attribute Tables (RATs) to identify area per LC transition.
        This information is converted to to a change matrix, where the rows are the early date and columns are the late date.
        The mapped LC transitions that are unlikely are highlighted in yellow, and the mapped transitions that should be corrected
        are highlighted in red. The results of the code are written to an excel document in a new folder called QAQC, which
        exists in the county input folder. 
Requirements: The code expects a CSV that crosswalks LCC raster values (Value) with the name of the transition in the form
              "LC to LC" (LCChange). This CSV is expected to exist in the same directory as LCC_matrices.py.
Folder Structure: The script expects the county change rasters to have a RAT and to be stored in the below format:
        /main_folder/cf/input/cf_landcoverchange_year1_year2.tif.vat.dbf
User arguments: The script expects at least 2 command line arguments from the user:
        1. the folder path (main_folder from example above)
        2. cf of county of interest. To run multiple counties at once, enter all cfs separated by a space.
Example: To run all 3 Delaware counties (suss_10005, newc_10003, kent_10001) whose folders exist in C:/landcover and the script lives
         in C:/code, type the following in the conda command prompt and hit enter:
            python C:/code/LCC_matrices.py C:/landcover suss_10005, newc_10003, kent_10001

        - The results will exist in C:/landcover/cf/input/QAQC/cf_LC_matrices.xlsx
        - ANY cells in red need correction.
        - All cells in yellow should be reviewed for potential correction.
Author: Sarah McDonald, Geographer, U.S. Geological Survey, Chesapeake Bay Program
Contact: smcdonald@chesapeakebay.net
"""

import os
import sys
import pandas as pd 
import geopandas as gpd 
import openpyxl
from openpyxl.styles.colors import Color
from openpyxl.styles import PatternFill

def read_commandLine() -> tuple:
    """
    read_commandLine This method validates user input and verifies the county folder paths exist.

    Returns
    -------
    tuple
        folder : str
            string path to main folder that contains the county folders.
        cfs : list
            list of county_fips (AKA cofips AKA cfs)
    """
    # read command line arguments
    args = sys.argv
    if len(args) >= 3:
        folder = args[1]
        cfs = args[2:]
        if not os.path.isdir(folder):
            print(f"Folder Path does not exist: {folder}")
            sys.exit()
        for cf in cfs:
            if not os.path.isdir(f"{folder}/{cf}"):
                print(f"Invalid cofips: {cf}")
                sys.exit()
    else:
        print(f"Missing arguments. Expected:\n\t1. folder path containing cf folder.\n\t2. cofips (cf). Can provide more than one at once, separated by a space")
        sys.exit()
    return folder, cfs

def addStyle(path:str, sheets:list):
    """
    addStyle This method identifies cells in the matrices that are unlikely and need verification (yellow) and incorrect
             transitions (red) and color codes them.

    Parameters
    ----------
    path : str
        path to excel workbook containing LCC matrices.
    sheets : list
        list of excel sheet names.
    """
    # add hex codes for colors and transitions to be colored that way
    colors = {
        "red"       : {
            'hex': "FF1300",
            'transitions'   : [['Emergent Wetlands', 'Low Vegetation'], 
                                ['Low Vegetation', 'Emergent Wetlands']],
        },
        "yellow"    : {
            'hex'   : "EDFF00",
            'transitions'   : [ [x, y] for x in ['Impervious Roads', 'Impervious Structures', 'Other Impervious'] for y in ['Barren', 'Low Vegetation', 'Emergent Wetlands', 'Scrub\Shrub', 'Tree Canopy']],
        }
    }

    # excel
    worksheet = openpyxl.load_workbook(path)
    for i in range(len(sheets)):
        cur_sheet = worksheet[sheets[i]]

        for color in colors:
            # pattern to fill 
            fmtFillPattern = PatternFill(start_color=colors[color]['hex'],fill_type='solid')

            # iterate transitions
            xy = []
            for t in colors[color]['transitions']:
                x, y = classes.index(t[0])+2, classes.index(t[1])+2
                xy.append((x,y))

            # Apply fill
            for row in cur_sheet.iter_rows(cur_sheet.min_row,cur_sheet.max_row):
                for cell in row:
                    if (cell.row, cell.col_idx) in xy:
                        if cell.value > 0:
                            cell.fill = fmtFillPattern

        # adjust column size
        for col in cur_sheet.columns:
            max_length = 0
            column = col[0].column_letter # Get the column name
            for cell in col:
                try: # Necessary to avoid error on empty cells
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2) * 1.2
            cur_sheet.column_dimensions[column].width = adjusted_width

    # save formatting
    worksheet.save(path)
    worksheet.close()


def createMatrices(folder:str, cfs:list):
    """
    createMatrices This method locates the LCC raster attribute tables, converts them to change matrices, and
                   calls the addStyle method to color-code unlikely transitions. The values are in acres and 
                   are not rounded to allow for identification of very small (including single-pixel) transitions.

    Parameters
    ----------
    folder : str
        path to folder containing cf folders.
    cfs : list
        list of county_fips AKA cofips AKA cfs
    """
    # loop through cofips
    for cf in cfs:
        print(f"Starting: {cf}")
        # locate LC change paths
        input_folder = f"{folder}/{cf}/input"

        # create qaqc folder where results will be stored
        qaqc_folder = f"{input_folder}/QAQC"
        if not os.path.isdir(qaqc_folder):
            os.mkdir(qaqc_folder)

        # get state
        st = cf.split('_')[-1][0:2]

        # determine mapped years based on state
        # TODO: verify dates
        years = []
        if st in['10', '24']:
            years = [2013, 2018, 2021]
        elif st in ['51', '54']:
            years = [2014, 2018, 2021]
        elif st in ['11', '36', '42']:
            years = [2013, 2017, 2022]
        else:
            print(f"Invalid state from cofips: {st}, {cf}")
            sys.exit()

        # read in change raster RATs and convert to change matrix
        matrices = []
        for i in range(len(years)-1):
            # read in RAT
            p = f"{input_folder}/{cf}_landcoverchange_{years[i]}_{years[i+1]}.tif.vat.dbf"
            if not os.path.isfile(p):
                print(f"\tLand Cover Raster Attribute Table does not exist. Verify path and mapped dates. \n\t{p}\n\tSkipping.")
                continue
            df = gpd.read_file(p)
            df.drop('geometry', axis=1, inplace=True)
            df = df.set_index('Value')

            # add LC names
            for idx, row in df.iterrows():
                lcc = cw.loc[idx, 'LCChange']
                if ' to ' not in lcc:
                    continue
                early, late = lcc.split(' to ')
                df.loc[idx, f"{years[i]}"] = early
                df.loc[idx, f"{years[i+1]}"] = late

            # convert count (square meters) to acres
            df.loc[:, "Acres"] = df['Count'] / 4046.86

            # drop cols
            df = df[[f"{years[i]}", f"{years[i+1]}", "Acres"]]

            # create pivot table
            matrix = pd.pivot_table(df, values='Acres', index=f"{years[i]}", columns=f"{years[i+1]}")

            # validate all classes are present
            for c in classes:
                if c not in matrix.columns:
                    matrix.loc[:, c] = 0
                if c not in matrix.index:
                    matrix.loc[c, :] = 0
            
            # change class order
            matrix = matrix.reindex(classes)
            matrix = matrix[classes]
            matrix = matrix.fillna(0)

            # totals
            matrix.loc[:, 'Decrease'] = matrix[classes].sum(axis=1)
            matrix.loc['Increase'] = matrix[classes].sum(axis=0)

            # store results
            matrices.append(matrix.copy())

        if len(matrices) > 0:
            # write matrices
            output_path = f"{qaqc_folder}/{cf}_LC_matrices.xlsx"
            sheets = []
            with pd.ExcelWriter(output_path) as writer:
                for i in range(len(matrices)):
                    matrices[i].to_excel(writer, sheet_name=f"{years[i]}-{years[i+1]}", index=True)
                    sheets.append(f"{years[i]}-{years[i+1]}")

            # highlight cells that need double checking
            addStyle(output_path, sheets)

if __name__=="__main__":
    # user variables
    folder, cfs = read_commandLine()

    # read in table crosswalking values to lc change classes
    workingDir = os.path.realpath(os.path.dirname(__file__))
    cw = pd.read_csv(f"{workingDir}/LCChange_cw_2022ed.csv")
    classes = list(cw[cw['Value'] <= 12]['LCChange'])
    cw = cw.set_index('Value')

    # for each county, create LC change matrices for T1-T2 and T2-T3
    createMatrices(folder, cfs)
