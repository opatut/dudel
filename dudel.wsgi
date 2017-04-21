#!/usr/bin/env python2
import sys, os, datetime

# this file might be symlinked somewhere (e.g. apache2 needs .wsgi files
# in an accessible location like webroot), so we need to find the actual
# path for the rest of the code
path = os.path.dirname(os.path.realpath(__file__))

# Activate the virtual environment to load the library.
# TODO: change this if your virtual environment is not located at ./env
activate_this = os.path.join(path, "env", "bin", "activate_this.py")
execfile(activate_this, dict(__file__ = activate_this))

sys.path.insert(0, path)
os.chdir(path)
from dudel import app as application
