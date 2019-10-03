import pynrc
import pynrc.reduce.ref_pixels
import numpy as np
from astropy.io import fits, ascii
import glob
import os
from subprocess import call
from shutil import copyfile
import yaml
import pdb
from copy import deepcopy
import make_syml
from astropy.time import Time
import astropy.units as u


detectorDict = {481: "NRCA1", 482: "NRCA2", 483: "NRAC3", 484: "NRCA4",
                485: "NRCA5",
                486: "NRCA1", 487: "NRCB2", 488: "NRCB3", 489: "NRCB4",
                490: "NRCB5"}

def fix_headers(testMode=True):
    """ Fix the headers of the fitsWriter files since they need updating usually
    Parameters
    -----------
    testMode: bool
        Do a dry run before modifying headers?
    """
    
    with open('parameters/header_fixes.yaml') as f:
        hParams = yaml.safe_load(f)
    
    fileList = glob.glob(hParams['fileList'])
    detTiming = pynrc.pynrc_core.DetectorOps(detector=481,
                                             wind_mode=hParams['wind_mode'],
                                             xpix=hParams['xpix'],
                                             ypix=hParams['ypix'],
                                             x0=hParams['COLCORNR']-1,
                                             y0=hParams['ROWCORNR']-1,
                                             nint=hParams['nint'],
                                             ngroup=hParams['ngroup'],
                                             nf=hParams['nf'])
    correctHead = detTiming.make_header()
    for oneFile in fileList:
        with fits.open(oneFile,'update') as HDUList_orig:
            if testMode == True:
                print("Doing a dry run without modifying headers")
                HDUList = fits.HDUList([fits.PrimaryHDU(None,header=HDUList_orig[0].header)])
                primHead = HDUList[0].header
            else:
                primHead = HDUList_orig[0].header
            
            obsId = primHead['OBS_ID']
            if obsId in hParams['expStart'].keys():
                expStart = hParams['expStart'][obsId]
                date, time = expStart.split('T')
                primHead['DATE-OBS'] = date
                primHead['TIME-OBS'] = time
                
                t_expStart = Time(expStart)
                t_expEnd = t_expStart + correctHead['EXPTIME'] * u.second
                expEnd = t_expEnd.fits
                date, time = expEnd.split('T')
                primHead['DATE-END'] = date
                primHead['TIME-END'] = time
            else:
                print("Couldn't find exp start for {}".format(obsId))
            

            for oneKey in ['TFRAME','TGROUP','INTTIME','EXPTIME',
                           'TREFROW','BREFROW','LREFCOL','RREFCOL',
                           'COLCORNR','ROWCORNR']:
                primHead[oneKey] = correctHead[oneKey]
            
            if hParams['wind_mode'] == 'WINDOW':
                primHead['HWINMODE'] = 'ENABLE'
            else:
                primHead['HWINMODE'] = 'DISABLE'
            primHead['DETECTOR'] = detectorDict[primHead['SCA_ID']]
            
            primHead['TLDYNEID'] = hParams['teledyneID'][primHead['SCA_ID']]
        


if __name__ == "__main__":
    fix_headers()
