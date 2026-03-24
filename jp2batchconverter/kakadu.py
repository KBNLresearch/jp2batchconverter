#! /usr/bin/env python3
"""Kakadu wrapper module"""

import os
import subprocess as sub
import logging


"""
cmdlineMaster="$kduPath/kdu_compress -i "$file"
        -o "$jp2Out"
        Creversible=yes
        Clevels=5
        Corder=RPCL
        Stiles={1024,1024}
        Cblk={64,64}
        Cprecincts={256,256},{256,256},{128,128}
        Clayers=11
        -rate $bitratesMaster
        Cuse_sop=yes
        Cuse_eph=yes
        Cmodes=SEGMARK
        -jp2_box "$xmpName"
        -com "$cCommentMaster""
"""

def compress(imageIn, jp2Out):
    """Convert input image to JP2
    """
    # TODO read from user-defined config file!
    kdu_dir = "/home/johan/kakadu/"
    kdu_compress = os.path.join(os.path.normpath(kdu_dir), "kdu_compress")

    # Set LD_LIBRARY_PATH to kdu_dir (this only sets the variable for thus process,
    # not system wide)
    os.environ['LD_LIBRARY_PATH'] = kdu_dir

    ## Bitrates for RGB images, following KB specs
    bitratesMaster="-,4.8,2.4,1.2,0.6,0.3,0.15,0.075,0.0375,0.01875,0.009375"
    bitratesAccess="1.2,0.6,0.3,0.15,0.075,0.0375,0.01875,0.009375"
    ## Bitrates for grayscale images, following KB specs
    #bitratesMaster="-,1.6,0.8,0.4,0.2,0.1,0.05,0.025,0.0125,0.00625,0.003125"
    #bitratesAccess="0.4,0.2,0.1,0.05,0.025,0.0125,0.00625,0.003125"

    compress_args = ["Creversible=yes",
                       "Clevels=5",
                       "Corder=RPCL",
                       "Stiles={1024,1024}",
                       "Cblk={64,64}",
                       "Cprecincts={256,256},{256,256},{128,128}",
                       "Clayers=11",
                       "-rate", bitratesMaster,
                       "Cuse_sop=yes",
                       "Cuse_eph=yes",
                       "Cmodes=SEGMARK"]

    io_args = [kdu_compress, "-i", imageIn, "-o", jp2Out]
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


    #print(out)
    #print(err)
    #print(status)

    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err

    return dictOut
