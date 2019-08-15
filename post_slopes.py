import glob
import numpy as np
import os
from astropy.io import fits, ascii
import yaml
from shutil import copyfile
import pdb
from copy import deepcopy


paramFile = 'parameters/pipe_params.yaml'
if os.path.exists(paramFile) == False:
    copyfile('parameters/example_pipe_params.yaml',paramFile)
with open(paramFile) as paramFileOpen:
    pipeParam = yaml.safe_load(paramFileOpen)

baseDir = os.path.join(pipeParam['symLinkDir'])
procDir = os.path.join(baseDir,'raw_separated_MMM_refpix')
outputDir = os.path.join(baseDir,'slope_post_process')
if os.path.exists(outputDir) == False:
    os.mkdir(outputDir)

if 'rowsUse' not in pipeParam:
    rowsUse = [[0,80],[140,256]]
if 'colsUse' not in pipeParam:
    colsUse = [[4,190]]


def do_subtraction(inputPath,outFilePath,diagnostics=False):
    fileName = os.path.basename(inputPath)
    HDUList = fits.open(inputPath)
    dat = HDUList[0].data
    img = dat[0]
    
    
    rowsAndCols = [rowsUse,colsUse]
    
    x,y = np.meshgrid(np.arange(img.shape[1]),np.arange(img.shape[0]))
    allCoords = [y,x]
    medianDirections = [0,1] ## perpendicular to the coordinate dimensions
    correctedImage = deepcopy(img)
    for oneDim in [1,0]: ## Python does X=1, Y=0
        # Start with column-by-column, so the coordinate direction is X
        # to get rid of pre-amp resets
        # This means that we use a mask for the X pixels
        
        indArray = allCoords[oneDim]
        pts = np.zeros_like(img,dtype=np.bool)
        for oneRange in rowsAndCols[oneDim]:
            thisRangePts = (indArray >= oneRange[0]) & (indArray <= oneRange[1])
            pts = pts | thisRangePts
        if diagnostics == True:
            primHDU = fits.PrimaryHDU(np.array(pts,dtype=np.uint16))
            primHDU.writeto('diagnostics/'+fileName+'_mask_coord_dim_{}.fits'.format(oneDim),overwrite=True)
        
        maskedImg = deepcopy(correctedImage) ## apply to the latest corrected image
        maskedImg[pts == False] = np.nan
        medianThisDirection = np.nanmedian(maskedImg,axis=medianDirections[oneDim])
        
        correction2D = np.tile(medianThisDirection,[img.shape[oneDim],1])
        if medianDirections[oneDim] == 1:
            ## for Y coordinates/ median along X, need to rotate this
            correction2D = correction2D.transpose() 
        
        if diagnostics == True:
            primHDU = fits.PrimaryHDU(np.array(correction2D))
            primHDU.writeto('diagnostics/'+fileName+'_correction_coord_dim_{}.fits'.format(oneDim),overwrite=True)
        
        correctedImage = correctedImage - correction2D

        if diagnostics == True:
            primHDU = fits.PrimaryHDU(np.array(correctedImage))
            primHDU.writeto('diagnostics/'+fileName+'_corrrected_after_dim_{}.fits'.format(oneDim),overwrite=True)
    
    outHDU = fits.PrimaryHDU(correctedImage,HDUList[0].header)
    outHDU.header['ROWBYROW'] = (True, 'Is a row-by-row median subtraction performed?')
    outHDU.header['COLBYCOL'] = (True, 'Is a col-by-col median subtraction performed?')
    
    outHDU.writeto(outFilePath,overwrite=True)
    HDUList.close()

    

def subtract_all_files():
    testNames = os.listdir(procDir)
    for testInd,oneTest in enumerate(testNames):
        print("Working on Exposure {} ({} of {})".format(oneTest,testInd,len(testNames)))
        inputTestDir = os.path.join(procDir,oneTest)
        outputTestDir = os.path.join(outputDir,oneTest)
        if os.path.exists(outputTestDir) == False:
            os.mkdir(outputTestDir)
        fileL = np.sort(glob.glob(os.path.join(inputTestDir,'*.slp.fits')))
        for fileInd,oneFile in enumerate(fileL):
            if np.mod(fileInd,50) == 0:
                print("Working on integration {} of {}".format(fileInd,len(fileL)))
            filePrefix = os.path.splitext(os.path.basename(oneFile))[0]
            outFilePath = os.path.join(outputTestDir,filePrefix+'_rowcolsub.fits')
            outHDU = do_subtraction(oneFile,outFilePath)
            
        
        
if __name__ == '__main__':
    subtract_all_files()
