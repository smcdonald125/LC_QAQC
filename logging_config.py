from pathlib import Path
import logging
import traceback
import os
import subprocess

LOG_NAME = 'progress.log'
FILE_LOG_LEVEL = 'INFO'
FILE_MODE = 'a'

def log_uncaught_exception(*exc_info):
    """Sends uncaught exceptions to root logger.
    To implement, set `sys.excepthook` as this function:
    `sys.excepthook = log_uncaught_exception`
    """
    
    text = "".join(traceback.format_exception(*exc_info))
    logging.exception(f"Unhandled exception {text}")


def get_git_hash():
    """If file is being run from a git-enabled directory, this function returns the
    hash of the active git commit and directs it to the log"""
    base_dir = BASE_DIR = Path(__file__).resolve().parent

    try:
        output = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=base_dir)
        git_hash = str(output, 'utf-8').strip()

    except Exception as e:
        # Directory is not git enabled, git is not installed, or some other error occured
        git_hash = ''
        print(e)

    return git_hash

def get_log_config(
    level='INFO',
    log_file_path='.',
    log_file_name=LOG_NAME):
        
    log_file = os.path.join(log_file_path, log_file_name)

    git_hash = get_git_hash()
    git_hash_text = f'|{git_hash}|' if git_hash else '|'

    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': f'%(asctime)s|%(levelname)s|%(name)s|%(lineno)d{git_hash_text}%(message)s',
                'datefmt': "%Y-%m-%d %H:%M:%S",
            }
        },
        'handlers': {
            'console': {
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
            'file': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.FileHandler',
                'filename': log_file,
                'encoding': 'utf8',
                'mode':FILE_MODE,
            }
        },
        'loggers': {
            # Root logger, captures all script logs
            '': {
                'handlers': ['console','file'],
                'level': level,
            },
            # Extra loggers to reduce messages coming from third-party modules
            'rasterio': {
                'handlers': ['console','file'],
                'level': 'WARNING',
                },
            'pyogrio': {
                'handlers': ['console','file'],
                'level': 'WARNING',
                },
            'pyproj': {
                'handlers': ['console', 'file'],
                'level': 'WARNING',
            },
        }

    }

    return log_config


