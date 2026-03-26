#! /usr/bin/env python3
"""Grok codec wrapper module"""

import os
import sys
import subprocess as sub
from . import shared

class Grok:
    """Grok class"""

    def __init__(self):
        """initialise Grok class instance"""
        self.grok_dir = ""
        self.grok_bin_dir = ""
        self.grok_lib_dir = ""
        self.grk_compress = ""
        self.configDict = {}
        self.compressionProfile = ""
        self.imageIn = ""
        self.jp2Out = ""
        self.success = True
        self.status = ""
        self.out = ""
        self.errors = ""


    def configure(self):
        """Configure this Grok instance"""
        self.grok_dir = os.path.expanduser(self.configDict["grokDir"])
        self.grok_bin_dir = os.path.join(os.path.normpath(self.grok_dir), "bin")
        self.grok_lib_dir = os.path.join(os.path.normpath(self.grok_dir), "lib")
        if sys.platform == 'win32':
            # Windows
            self.grk_compress = os.path.join(os.path.normpath(self.grok_bin_dir), "grk_compress.exe")
        else:
            # Linux, MacOS
            self.grk_compress = os.path.join(os.path.normpath(self.grok_bin_dir), "grk_compress")
        # Test if grk_compress exists
        if not os.path.isfile(self.grk_compress):
            msg = "grk_compress binary ({}) is missing".format(self.grk_compress)
            shared.errorExit(msg)
        # Test if it is executable
        if not os.access(self.grk_compress, os.X_OK):
            msg = "grk_compress binary ({}) is not executable".format(self.grk_compress)
            shared.errorExit(msg)
        # Test if lib directory exists
        if not os.path.isdir(self.grok_lib_dir):
            msg = "grok lib directory ({}) is missing".format(self.grok_lib_dir)
            shared.errorExit(msg)
        # Set LD_LIBRARY_PATH for this class instance
        if sys.platform == 'linux':
            os.environ['LD_LIBRARY_PATH'] = self.grok_lib_dir
        elif sys.platform == 'darwin':
            # TODO - this is the MacOS equivalent of LD_LIBRARY_PATH, but not
            # sure if this works.
            os.environ['DYLD_LIBRARY_PATH'] = self.grok_lib_dir


    def compress(self):
        """Convert input image to JP2
        """
        # TODO include logfile option?
        # TODO add XMP box
        self.success = True

        # Select compression parameters from user-specified profile
        for profile in self.configDict["compressionProfiles"]:
            if profile["name"] == self.compressionProfile:
                compressionArgs = profile["params"]

        ioArgs = [self.grk_compress, "-i", self.imageIn, "-o", self.jp2Out]
        args = ioArgs + compressionArgs

        # Command line as string (used for logging purposes only)
        cmdStr = " ".join(args)

        out = ""
        errors = ""
        status =""

        # Run grk_compress as subprocess
        try:
            p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE,
                          shell=False, bufsize=1, universal_newlines=True)
            out, err = p.communicate()
            status = p.returncode

        except Exception:
            self.success = False

        self.status = status
        self.out = out
        self.errors = errors



