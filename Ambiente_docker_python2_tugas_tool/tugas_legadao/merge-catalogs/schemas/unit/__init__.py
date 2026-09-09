from os.path import dirname, basename, isfile

import glob

#List all py files in the folder
modules = glob.glob(dirname(__file__)+"/*.py")

#Import all the modules
__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]