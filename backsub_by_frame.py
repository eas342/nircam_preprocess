import glob
import os
import numpy as np
from astropy.io import fits, ascii
import pdb
import general_pipe_tools

pipeParam = general_pipe_tools.get_pipe_params()

baseDir = os.path.join(pipeParam['symLinkDir'])
rawDir = os.path.join(baseDir,'raw_separated_MMM')
outputDir = os.path.join(baseDir,'raw_separated_MMM_backsub_by_frame')
if os.path.exists(outputDir) == False:
    os.mkdir(outputDir)

if 'backg_rowsUse' not in pipeParam:
    pass ## eventually set with parameter file here
if 'backg_colsUse' not in pipeParam:
    pass ## eventually set with parameter file here

dirList = os.listdir(rawDir)

def run_all(testMode=False):
    for oneDir in dirList:
        if testMode == True:
            fileList = np.sort(glob.glob(os.path.join(rawDir,oneDir,'*I????.fits')))
            filesToRun = fileList[0:3]
        else:
            fileList = np.sort(glob.glob(os.path.join(rawDir,oneDir,'*I????.fits')))
            filesToRun = fileList
        
        outDir = os.path.join(outputDir,oneDir)
        if os.path.exists(outDir) == False:
            os.mkdir(outDir)
        
        for oneFile in filesToRun:
            baseName = os.path.basename(oneFile)
            HDUList = fits.open(oneFile)
            HDUList[0].header['BITPIX'] = -64
            HDUList[0].data = np.array(HDUList[0].data,dtype=np.float)
            NGROUP = HDUList[0].header['NGROUP']
            for oneGrp in np.arange(NGROUP):
                thisData = HDUList[0].data[oneGrp]
                if '1_487_S' in oneDir:
                    X1, X2 = 1132 + 300 - 80, 1132 + 300 + 80
                    Y1, Y2 = 76 - 70, 76 + 70
                elif '1_488_S' in oneDir: ## just a placeholder to deal w/ shortwave detector
                    X1, X2 = 1694 + 311 - 39, 1694 + 311 + 39
                    Y1, Y2 = 88 - 78, 88 + 78
                elif '1_489_S' in oneDir:
                    X1, X2 = 1694 + 311 - 39, 1694 + 311 + 39
                    Y1, Y2 = 88 - 78, 88 + 78
                else:
                    raise Exception("Couldn't recognize detector to choose aperture")
                
                backgVal = np.mean(thisData[Y1:Y2,X1:X2])
                HDUList[0].data[oneGrp] = thisData - backgVal
            
            HDUList[0].header['BKSUBFF'] = (True, "Is the background subtraction done frame-by-frame?")
            outPath = os.path.join(outDir,baseName)
            if os.path.exists(outPath):
                print("Found a previus file {}, not overwriting".format(outPath))
            else:
                HDUList.writeto(outPath)
            
            HDUList.close()

if __name__ == "__main__":
    run_all()
