#!/usr/bin/env python

__doc__ = \
    '''
'''

__version__ = '0.1'

__authors__ = [
    "Version 1.0: Joao Pio <joao-t-pio@telecom.pt>"
]

import argparse
import os


def is_r_dir(dirname):
    """Checks if a path is an actual directory"""
    if not os.path.isdir(dirname):
        raise argparse.ArgumentTypeError("{0} is not a directory".format(dirname))
    elif not os.access(dirname, os.R_OK):
        raise argparse.ArgumentTypeError("{0} is not a readable directory".format(dirname))
    else:
        return dirname


def is_w_dir(dirname):
    """Checks if a path is an actual directory"""
    if not os.path.isdir(dirname):
        raise argparse.ArgumentTypeError("{0} is not a directory".format(dirname))
    elif not os.access(dirname, os.W_OK):
        raise argparse.ArgumentTypeError("{0} is not a writable directory".format(dirname))
    else:
        return dirname


def exists(path):
    # Checks if path exists and is a file or directory
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError("file {0} does not exist".format(path))
    else:
        return path
