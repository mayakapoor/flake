#!/usr/bin/env python

import setuptools
import shutil

if __name__ == "__main__":
    setuptools.setup()
    shutil.copyfile("src/flake/flake.ini", "/etc/flake.ini")
