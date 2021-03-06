from astropy.io import fits, ascii
import numpy as np
import matplotlib.pyplot as plt
import pdb
from os import listdir, getcwd
import yaml
import os
from copy import deepcopy

defaultFile = 'nircam_011_nircam_011_jw88888002001_01101_00002-seg002_nrca5_uncal_I00065.fits'

def fit_slope(fileName=defaultFile,writeOutput=False,
              returnIntercept=False):
    """
    Fit a line to each pixel's samples up the ramp
    
    Parameters
    ----------
    fileName: str
        Path to FITS cube file (assuming integrations are split up)
    writeOutput: bool
        Write output to a fits file called :code:`es_slope.fits` or 
        :code:`es_intercept.fits`?
    returnIntercept: bool
        If True, returns the intercept of the line. Otherwise
        the slope is returned.
    """
    HDUList = fits.open(fileName)
    origHead = HDUList[0].header
    dat = HDUList[0].data
    nz, ny, nx = dat.shape
    
    flatDat = np.reshape(dat,[nz,nx * ny])
    x = np.arange(origHead['NGROUP']) * origHead['TGROUP']
    pfit = np.polyfit(x,flatDat,1)
    
    if returnIntercept == True:
        flatResult = pfit[1]
        resultFile = 'es_intercept.fits'
    else:
        flatResult = pfit[0]
        resultFile = 'es_slope.fits'
    
    result2D = np.reshape(flatResult,[ny,nx])
    outHDU = fits.PrimaryHDU(result2D,origHead)
    
    HDUList.close()
    if writeOutput == True:
        outHDU.writeto(resultFile,overwrite=True)
    else:
        return outHDU


def get_rawfiles():
    paramFile = 'parameters/pipe_params.yaml'
    with open(paramFile) as paramFileOpen:
        symLinkParam = yaml.safe_load(paramFileOpen)
    if symLinkParam['pynrcRefpix'] == True:
        linkDir = os.path.join(symLinkParam['symLinkDir'],'symlinks_sep_refpix')
        outDir = os.path.join(symLinkParam['symLinkDir'],'simple_slopes_refpix')
    else:
        linkDir = os.path.join(symLinkParam['symLinkDir'],'symlinks_separated')
        outDir = os.path.join(symLinkParam['symLinkDir'],'simple_slopes')
    
    if os.path.exists(outDir) == False:
        os.mkdir(outDir)
    
    raw_dirs= listdir(linkDir)
    
    raw_files = {}
    ignoretypes = ['.red.','.dia.','.slp.','.cds.','.txt']
    for oneDir in raw_dirs:
        fitsList = listdir(os.path.join(linkDir,oneDir))
        useList = deepcopy(fitsList)
        for onefile in fitsList:
            for ignoretype in ignoretypes:
                if ignoretype in onefile:
                    useList.remove(onefile)

        raw_files[oneDir] = useList
    return linkDir, outDir, raw_files
    

def do_all_slopes():
    linkDir, outDir, raw_files = get_rawfiles()
    for dirInd,dirNow in enumerate(raw_files.keys()):
        saveDir = os.path.join(outDir,dirNow)
        
        if os.path.exists(saveDir) == False:
            os.mkdir(saveDir)
            
        print("Working on directory {}".format(dirNow))
        print("This is dir {} of {}".format(dirInd+1,len(raw_files.keys())))
        
        useFiles = raw_files[dirNow]
        for oneFile in useFiles:
            rampFile = os.path.join(linkDir,dirNow,oneFile)
            outHDU = fit_slope(rampFile)
            outName = os.path.splitext(oneFile)[0]+'.slp.fits'
            outHDU.writeto(os.path.join(saveDir,outName),overwrite=True)
        
if __name__ == "__main__":
    do_all_slopes()
    
