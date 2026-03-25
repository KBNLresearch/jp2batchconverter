#! /usr/bin/env python3
"""Kakadu wrapper module"""

import os
import sys
import subprocess as sub
import logging
from . import shared
from . import config

class Kakadu:
    """Kakadu class"""

    def __init__(self):
        """initialise Kakadu class instance"""
        self.kdu_dir = config.kdu_dir
        self.kdu_compress = os.path.join(os.path.normpath(self.kdu_dir), "kdu_compress")
        # Test if kdu_compress exists
        if not os.path.isfile(self.kdu_compress):
            msg = "kdu_compress binary ({}) is missing".format(self.kdu_compress)
            shared.errorExit(msg)
        # Test if it is executable
        if not os.access(self.kdu_compress, os.X_OK):
            msg = "kdu_compress binary ({}) is not executable".format(self.kdu_compress)
            shared.errorExit(msg)

        # Set LD_LIBRARY_PATH to kdu_dir (this only sets the variable for this
        # Kakadu class instance ,not system wide)
        if sys.platform == 'linux':
            os.environ['LD_LIBRARY_PATH'] = self.kdu_dir
        elif sys.platform == 'darwin':
            # TODO - this is the MacOS equivalent of LD_LIBRARY_PATH, but not
            # sure if this works, or if Kakadu even uses this!
            os.environ['DYLD_LIBRARY_PATH'] = self.kdu_dir

        # File I/O
        self.imageIn = ""
        self.jp2Out = ""

    def compress(self):
        """Convert input image to JP2
        """

        ## Bitrates for RGB images, following KB specs
        # TODO read this from config file
        # TODO define as compression ratios, then calculate corresponding bitrates
        #      as a function of the number of colour components in the input image

        bitrates = "-,4.8,2.4,1.2,0.6,0.3,0.15,0.075,0.0375,0.01875,0.009375"

        # TODO add XMP box
        # TODO add codestream comment
        compress_args = ["Creversible=yes",
                        "Clevels=5",
                        "Corder=RPCL",
                        "Stiles={1024,1024}",
                        "Cblk={64,64}",
                        "Cprecincts={256,256},{256,256},{128,128}",
                        "Clayers=11",
                        "-rate", bitrates,
                        "Cuse_sop=yes",
                        "Cuse_eph=yes",
                        "Cmodes=SEGMARK"]

        io_args = [self.kdu_compress, "-i", self.imageIn, "-o", self.jp2Out]
        args = io_args + compress_args

        # Command line as string (used for logging purposes only)
        cmdStr = " ".join(args)

        out = ""
        errors = ""
        status =""

        # Run kdu_compress as subprocess
        try:
            p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE,
                        shell=False, bufsize=1, universal_newlines=True)
            out, err = p.communicate()
            status = p.returncode

        except Exception:
            logging.error("running Kakadu resulted in an exception")

        logging.info("Kakadu exit status: {}".format(status))

        if status != 0:
            logging.error("abnormal Kakadu exit status")

        # All results to dictionary
        dictOut = {}
        dictOut["cmdStr"] = cmdStr
        dictOut["status"] = status
        dictOut["stdout"] = out
        dictOut["stderr"] = err

