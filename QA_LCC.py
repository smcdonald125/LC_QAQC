import os
from pathlib import Path
import argparse
import toml
import pandas as pd

# Set up logging
import logging
import logging.config
from logging_config import (
    get_log_config,
    log_uncaught_exception,
)

from LCC_matrices import (
    createMatrices,
    difference_matrices,
    write_static_totals
)

# Capture warnings to logging
logging.captureWarnings(True)

# Create logger
logger = logging.getLogger(__name__)

if __name__=="__main__":

    # add CLI
    parser = argparse.ArgumentParser(
        description="Interface for running automated Land Cover Change QAQC. Default expects any number of cofips, separated by a space. An optional alternative is to pass a path to a table with a list of cofips.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--cfs',
        type=str,
        help='COFIPS identifier for the jurisdiction(s) to be processed. If passing more than one, separate by only a comma (no spaces). For example, to pass caro_51033 and balt_24005, pass caro_51033,balt_24005'
    )

    parser.add_argument(
        '--cofips-lookup',
        type=str,
        default=None,
        help="Path to CSV table containing a column of cofips to QA. Requires --column-name to be passed."
    )

    parser.add_argument(
        '--column-name',
        type=str,
        default=None,
        help="Name of column in cofips-lookup containing cofips to QA. Requires --cofips-lookup to be passed."
    )

    # parse arguments
    args = parser.parse_args()

    # CLI arguments
    cfs = args.cfs
    cofips_lookup = args.cofips_lookup
    column_name = args.column_name

    # determine unique list of cofips
    if cofips_lookup and column_name:   
        if os.path.isfile(cofips_lookup):
            if Path(cofips_lookup).ext == '.csv':
                try:
                    cfs = pd.read_csv(cofips_lookup)[column_name].tolist()
                except Exception as e:
                    raise (e)

    elif cfs:
        cfs = cfs.split(',')
    else:
        raise Exception(f"Expecting either --cfs OR --cofips-lookup and --column-name to be passed.")

    # read in configuration TOML
    code_dir = (
        Path(__file__)
        .parent
        .resolve()
    )
    config = toml.load(f"{code_dir}/config.toml")

    # Set up logging configuration based on CLI args
    LOG_CONFIG = get_log_config(
        log_file_path=config['folders']['logging'],
        log_file_name=config['logging']['name'])
    logging.config.dictConfig(LOG_CONFIG)

    logger.info(f"--------------------Starting Run-----------------------")
    logger.info(f"Cofips to QA: {cfs}")

    # read in lookup tables
    lc_dates = (
        pd.read_csv(config['lookup']['lc_dates'])
        .set_index('co_fips')
    )

    lcc_lookup = (
        pd.read_csv(config['lookup']['lcchange'])
        .set_index('value')
        .filter(items=['class'])
    )

    # separate into early and late lc
    lcc_lookup[['early','late']] = lcc_lookup['class'].str.split(' to ', n=1, expand=True)
    lcc_lookup.drop('class', axis=1, inplace=True)

    # iterate cofips
    for i, cf in enumerate(cfs):
        logger.info(f"Starting {cf}")

        # get mapped years for county
        years = lc_dates.loc[cf, ['T1','T2','T3']].tolist()
        output_path = f"{config['folders']['qaqc']}/{cf}_LCC_QA.xlsx"

        # replace transitions with abbreviations
        #   Only needs to run for the first iteration of the loop
        #    since we are overwriting a global configuration
        if (config['colors'] is not None) and (i > 0):
            for col in config['colors']:
                trans = config['colors'][col]['transitions']
                new_trans = []
                for tr in trans:
                    t = []
                    for lc in tr:
                        t.append(config['LC_abbrev'][lc])
                    new_trans.append(t.copy())
                
                config['colors'][col]['transitions'] = new_trans.copy()

        # create matrices for new data
        logger.info(f"{cf} Creating matrices for 2024 edition")
        total_df24 = createMatrices(
                data_folder=config['folders']['landuse_24ed'],
                qaqc_path=output_path,
                cf=cf,
                years=years,
                version='2024ed',
                lcc_lookup=lcc_lookup,
                colors=config['colors'],
                lc_abbrev=config['LC_abbrev'])
        
        # create matrix for old data
        logger.info(f"{cf} Creating matrices for 2022 edition")
        total_df22 = createMatrices(
                data_folder=config['folders']['landuse_22ed'],
                qaqc_path=output_path,
                cf=cf,
                years=years[0:2],
                version='2022ed',
                lcc_lookup=lcc_lookup,
                colors=config['colors'],
                lc_abbrev=config['LC_abbrev'])
        
        # difference T1-T2 matrices between versions
        logger.info(f"{cf} Differecing matrices for T1-T2")
        difference_matrices(
                qaqc_path=output_path,
                year1=years[0],
                year2=years[1],
                versions=['2024ed', '2022ed'])
        
        # write total LC acres per class from each dataset and version
        logger.info(f"{cf} Write LC totals")       
        write_static_totals(
            df24=total_df24,
            df22=total_df22,
            qaqc_path=output_path
        )
