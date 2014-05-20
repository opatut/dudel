#!/usr/bin/env python2
import sys, os, datetime
from os.path import *

# Activate the virtual environment to load the library.
path = dirname(abspath(__file__))
activate_this = join(path, "env", "bin", "activate_this.py")
execfile(activate_this, dict(__file__ = activate_this))

sys.path.insert(0, path)
os.chdir(path)
from dudel import app as application
