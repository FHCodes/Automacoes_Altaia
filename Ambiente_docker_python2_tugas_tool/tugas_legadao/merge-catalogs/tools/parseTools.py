#!/usr/bin/env python

__doc__ = \
    '''
'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Joao Pio <joao-t-pio@telecom.pt>"
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
