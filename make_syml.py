import glob
import numpy as np
from subprocess import call
import os
import ipdb
from astropy.io import fits

def make_syml(output='symlinks_separate_int'):
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

def copy_syml():
    """
    Copies the symbolic links to all files into files for outputs
    """
    for ipc in ['P','M']:
        for lin in ['P','M']:
            for flat in ['P','M']:
                dirname = 'raw_separated_'+ipc+lin+flat
                call('cp -r symlinks_separate_ints '+dirname,shell=True)

def make_flats():
    """
    Makes single extension versions of the flat fields
    """
    basedir = '/usr/local/nircamsuite/cal/Flat/ISIMCV3/'
    outdir = '/data1/tso_analysis/all_tso_cv3/flat_data/'
    filel = glob.glob(basedir+'*_F150W_*.fits')
    for onefile in filel:
        if '_illumpattern' not in onefile:
            HDU = fits.open(onefile)
            outdata = HDU[1].data
            outheader = HDU[0].header
            basename, extname = os.path.splitext(os.path.basename(onefile))
            fits.writeto(outdir+basename+'_1ext.fits',outdata,outheader,clobber=True)
            HDU.close()

