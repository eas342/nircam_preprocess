from astropy.io import ascii,fits
import os
import numpy as np
import pdb
import sys
from sys import argv
import glob

overWrite = True
customRegion = True
correctionMode = 'rowSub'

dataDir = 'raw_separated_MPP'
obsDir = 'NRCN83-FULLFRAME-7251210755_1_2825_JW1_JLAB40_20170908T210928.164_20170908T213806.429'
fileL = glob.glob(os.path.join(dataDir,obsDir,'*I???.slp.fits'))

# Directory where to save files
outDataDir = 'additional_proc_MPP'
outDir = os.path.join(outDataDir,obsDir)

if os.path.exists(outDir) == False:
    os.mkdir(outDir)

for oneFile in fileL:
    redDat = fits.open(oneFile)
    
    ## dat = np.array(redDat['PRIMARY'].data,dtype='int32')
    dat = np.array(redDat['PRIMARY'].data[0]) ## just get the Slope image
    head = redDat['PRIMARY'].header
    
    baseName = os.path.splitext(os.path.basename(oneFile))[0]
    
    if customRegion == True:
        leftHandSide = np.median(dat[:,0:1400],axis=1)
        rightHandSide = np.median(dat[:,1800:2048],axis=1)
        medianOfEachRow = (leftHandSide + rightHandSide) /2.
        
        rowRegionText = "[0:1400] and [1800:2048]"
    else:
        medianOfEachRow = np.median(dat,axis=1)
        rowRegionText = "[0:2048]"
    
    correction2D = np.tile(medianOfEachRow,[head['NAXIS1'],1]).transpose()

    if correctionMode == 'rowColSub':
        medianOfEachColumn = np.median(dat,axis=0)
        correction2D_col = np.tile(medianOfEachColumn,[head['NAXIS1'],1])
        correctedDat = dat - correction2D - correction2D_col
    else:
        correctedDat = dat - correction2D
    
    imgHDU = fits.PrimaryHDU(correctedDat,head)
    HDUList = fits.HDUList([imgHDU])
    fitsName = "{}_{}.fits".format(baseName,correctionMode)
    if correctionMode == 'rowColSub':
        imgHDU.header["CCORRECT"] = (True, "Is a column-by-column median subtraction applied?")
    else:
        imgHDU.header["CCORRECT"] = (False, "Is a column-by-column median subtraction applied?")
    
    imgHDU.header["RCORRECT"] = (True, "Is a row-by-row median subtraction applied?")
    imgHDU.header["RCORREG"] = (rowRegionText, "Region over which median is calculated")

    outPath = os.path.join(outDir,fitsName)
    HDUList.writeto(outPath,overwrite=overWrite)
    redDat.close()
    HDUList.close()

