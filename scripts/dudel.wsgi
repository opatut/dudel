#!/usr/bin/env python3
import sys, os, datetime

path = os.path.dirname(os.path.abspath(__file__))

# Activate the virtual environment to load the library.
# TODO: change this if your virtual environment is not located at ./env
activate_this = os.path.join(path, "env", "bin", "activate_this.py")
execfile(activate_this, dict(__file__ = activate_this))

sys.path.insert(0, path)
os.chdir(path)
from dudel import app as application
