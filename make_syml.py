import glob
import numpy as np
from subprocess import call
import os
import ipdb

def make_syml(output='first_test'):
    """
    Makes symbolic links to all files
    """
    basedir = '/data/External/ISIMCV3_unzipped/NRCN821/fitsfilesonly/raw_separated/'


    if not os.path.exists(output):
        call(['mkdir',output])
    tests = os.listdir(basedir)
    for test in tests:
        linkdir=output+'/'+test
        if not os.path.exists(linkdir):
            call(['mkdir',linkdir])
        for datfile in glob.glob(basedir+test+'/*.fits'):
            link = linkdir+'/'+os.path.basename(datfile)
            call(['ln','-s',datfile,link])

