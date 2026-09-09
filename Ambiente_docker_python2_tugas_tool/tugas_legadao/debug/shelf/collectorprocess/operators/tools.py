#!/usr/bin/env python

__doc__ = \
    '''
'''

__version__ = '1.0'

__authors__ = [
    "Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>",
    "Version 1.0: Joao Pio <joao-t-pio@alticelabs.com>"
]

import os
import fnmatch


def getFiles(search_path, search_file_patterns):
    """
     Looks for the files recursively in a given folder and returns a list of all the files found
     that satisfy the given pattern OR accepts a file path and checks if it
     """
    file_list = []

    # Check if provided path was a file or a folder
    if os.path.isdir(search_path):
        # Guarantee the last slash in the provided path
        search_path = os.path.join(search_path, "")

        # Check if there are several patterns or a single one
        if not isinstance(search_file_patterns, list):
            search_file_patterns = [search_file_patterns]

        for root, dirnames, filenames in os.walk(search_path):
            for searchFilePattern in search_file_patterns:
                for filename in fnmatch.filter(filenames, searchFilePattern):
                    file_list.append(os.path.join(root, filename))

        if file_list:
            file_list = list(set(file_list))

    else:
        try:
            # Check if there are several patterns or a single one
            if not isinstance(search_file_patterns, list):
                search_file_patterns = [search_file_patterns]

            filename = os.path.basename(search_path)
            for searchFilePattern in search_file_patterns:
                if fnmatch.fnmatch(filename, searchFilePattern):
                    return [search_path]
        except Exception as e:
            pass

    return file_list
