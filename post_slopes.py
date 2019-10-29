import glob
import numpy as np
import os
from astropy.io import fits, ascii
from astropy.table import Table
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

## make all output directories
outputDir = os.path.join(baseDir,'slope_post_process')
flatDir = os.path.join(baseDir,'flat_fields')
dividedDir = os.path.join(baseDir,'flat_fielded')
for onePath in [outputDir,flatDir,dividedDir]:
    if os.path.exists(onePath) == False:
        os.mkdir(onePath)


if 'rowsUse' not in pipeParam:
    pipeParam['rowsUse'] = {487:[[0,80],[140,256]],
                            488:[[0,80],[140,256]],
                            489:[[0,80],[140,256]],
                            490:[[0,80],[140,256]]}
if 'colsUse' not in pipeParam:
    pipeParam['colsUse'] = {487: [[4,190]],
                            488: [[4,190]],
                            489: [[4,190]],
                            490: [[4,190]]}


if 'indices_for_flatfield' not in pipeParam:
    pipeParam['indices_for_flatfield'] = [None, None]


def do_subtraction(inputPath,outFilePath,diagnostics=False):
    """

    Do a column-by-column, row-by-row or both subtractions
    The column-by-column can remove amplifier offsets
    The row-by-row can remove 1/f noise noise.

    Indices are explained in this table:
    
    Type of subtraction | Direction of mask | Direction along
                        |  coordinates      | which to median
    ----------------------------------------------------------------
    column-by-column    |  Y / 0  'rowsUse' |   Y / 0
    row-by-row          |  X / 0  'colsUse' |   X / 1
    """
    fileName = os.path.basename(inputPath)
    HDUList = fits.open(inputPath)
    dat = HDUList[0].data
    img = dat[0]
    head = HDUList[0].header
    
    ## Look up which rows and columns to median based on SCA ID
    ## (different for different images)
    if 'SCA_ID' not in head:
        raise Exception("Could not find SCA ID")
    elif head['SCA_ID'] not in pipeParam['rowsUse'].keys():
        raise Exception("Could not find rows for SCA {}".format(head['SCA_ID']))
    elif head['SCA_ID'] not in pipeParam['colsUse'].keys():
        raise Exception("Could not find columns for SCA {}".format(head['SCA_ID']))
    else:
        rowsToMedian = pipeParam['rowsUse'][head['SCA_ID']]
        colsToMedian = pipeParam['colsUse'][head['SCA_ID']]
    
    ## Copy the original image
    correctedImage = deepcopy(img)
    ## make a coordinate grid
    x,y = np.meshgrid(np.arange(img.shape[1]),np.arange(img.shape[0]))
    
    
    
    if diagnostics == True:
        primHDU = fits.PrimaryHDU(np.array(img))
        primHDU.writeto('diagnostics/'+fileName+'_original.fits',overwrite=True)
    
    ## Do the column-by-column subtraction
    if rowsToMedian is not None:
        pts = np.zeros_like(img,dtype=np.bool)
        ## gather coordinates (could be a disjointed list of them) 
        for oneRange in rowsToMedian:
            thisRangePts = (y >= oneRange[0]) & (y <= oneRange[1])
            pts = pts | thisRangePts
       
        if diagnostics == True:
            primHDU = fits.PrimaryHDU(np.array(pts,dtype=np.uint16))
            primHDU.writeto('diagnostics/'+fileName+'_mask_coord_col_by_col.fits',overwrite=True)
        
        ## make a mask
        maskedImg = deepcopy(correctedImage) ## apply to the latest corrected image
        maskedImg[pts == False] = np.nan
        
        ## find median and 2D correction
        medianThisDirection = np.nanmedian(maskedImg,axis=0)
        correction2D = np.tile(medianThisDirection,[img.shape[0],1])
        
        if diagnostics == True:
            primHDU = fits.PrimaryHDU(np.array(correction2D))
            primHDU.writeto('diagnostics/'+fileName+'_correction_coord_dim_col_by_col.fits',overwrite=True)
        
        correctedImage = correctedImage - correction2D
        
        if diagnostics == True:
            primHDU = fits.PrimaryHDU(np.array(correctedImage))
            primHDU.writeto('diagnostics/'+fileName+'_corrrected_after_dim_col_by_col.fits',overwrite=True)
        
        columnByColumn = True
    else:
        columnByColumn = True
    
    ## Do the row-by-row subtraction
    if colsToMedian is not None:
        pts = np.zeros_like(img,dtype=np.bool)
        ## gather coordinates (could be a disjointed list of them)
        for oneRange in colsToMedian:
            thisRangePts = (x >= oneRange[0]) & (x <= oneRange[1])
            pts = pts | thisRangePts
        
        if diagnostics == True:
            primHDU = fits.PrimaryHDU(np.array(pts,dtype=np.uint16))
            primHDU.writeto('diagnostics/'+fileName+'_mask_coord_row_by_row.fits',overwrite=True)
        
        maskedImg = deepcopy(correctedImage) ## apply to the latest corrected image
        maskedImg[pts == False] = np.nan
        medianThisDirection = np.nanmedian(maskedImg,axis=1)
        
        ## need to rotate this for the row-by-row median
        correction2D = np.tile(medianThisDirection,[img.shape[1],1]).transpose()
        
        if diagnostics == True:
            primHDU = fits.PrimaryHDU(np.array(correction2D))
            primHDU.writeto('diagnostics/'+fileName+'_correction_coord_dim_row_by_row.fits',overwrite=True)
        
        correctedImage = correctedImage - correction2D
        
        if diagnostics == True:
            primHDU = fits.PrimaryHDU(np.array(correctedImage))
            primHDU.writeto('diagnostics/'+fileName+'_corrrected_after_dim_row_by_row.fits',overwrite=True)
        
        rowByRow = True
    else:
        rowByRow = False
    
    outHDU = fits.PrimaryHDU(correctedImage,HDUList[0].header)
    outHDU.header['COLBYCOL'] = (columnByColumn, 'Is a col-by-col median subtraction performed?')
    outHDU.header['ROWBYROW'] = (rowByRow, 'Is a row-by-row median subtraction performed?')
    
    outHDU.writeto(outFilePath,overwrite=True)
    HDUList.close()

    

def subtract_all_files():
    """
    Do row and column subtraction on a set of files
    
    """
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
            

def find_flat_fields():
    testNames = os.listdir(procDir)
    
    for testInd,oneTest in enumerate(testNames):
        print("Working on Exposure {} ({} of {})".format(oneTest,testInd,len(testNames)))
        inputTestDir = os.path.join(procDir,oneTest)
        outputTestDir = os.path.join(flatDir,oneTest)
        if os.path.exists(outputTestDir) == False:
            os.mkdir(outputTestDir)
        fullFileL = np.sort(glob.glob(os.path.join(inputTestDir,'*.slp.fits')))
        if pipeParam['indices_for_flatfield'][0] is None:
            startP = 0
        else:
            startP = pipeParam['indices_for_flatfield'][0]
        if pipeParam['indices_for_flatfield'][1] is None:
            endP = len(fullFileL) - 1
        else:
            endP = pipeParam['indices_for_flatfield'][1]
        fileL = fullFileL[startP:endP]
        nFile = len(fileL)
        firstHead = fits.getheader(fileL[0])
        allSlopes = np.zeros([nFile,firstHead['NAXIS2'],firstHead['NAXIS1']])
        for fileInd,oneFile in enumerate(fileL):
            if np.mod(fileInd,50) == 0:
                print("Reading integration {} of {}".format(fileInd,len(fileL)))
            oneImg = fits.getdata(oneFile)
            allSlopes[fileInd,:,:] = oneImg[0]
        
        avgSlope = np.mean(allSlopes,axis=0)
        normalization = np.percentile(avgSlope,90)
        flatImg = avgSlope / normalization
        primHDU = fits.PrimaryHDU(flatImg,header=firstHead)
        primHDU.header['NORMFLUX'] = (normalization, "Normalization divisor for flat field")
        primHDU.name = 'FLAT'
        
        ## save the filenames used
        t = Table()
        t['Filenames'] = fileL
        tableHDU = fits.BinTableHDU(t)
        tableHDU.name = 'FILENAMES'
        HDUList = fits.HDUList([primHDU,tableHDU])
        
        flatName = os.path.join(outputTestDir,'flat_for_{}.fits'.format(oneTest))
        HDUList.writeto(flatName,overwrite=True)

def divide_all_files():
    """
    Divide all files by a flat field from the flat field directory
    """
    testNames = os.listdir(procDir)
    
    for testInd,oneTest in enumerate(testNames):
        print("Working on Exposure {} ({} of {})".format(oneTest,testInd,len(testNames)))
        inputTestDir = os.path.join(procDir,oneTest)
        outputTestDir = os.path.join(dividedDir,oneTest)
        calDir = os.path.join(flatDir,oneTest)
        if os.path.exists(outputTestDir) == False:
            os.mkdir(outputTestDir)
        fileL = np.sort(glob.glob(os.path.join(inputTestDir,'*.slp.fits')))

        flatName = os.path.join(calDir,'flat_for_{}.fits'.format(oneTest))
        flat_field = fits.getdata(flatName)
        
        for fileInd,oneFile in enumerate(fileL):
            if np.mod(fileInd,50) == 0:
                print("Working on integration {} of {}".format(fileInd,len(fileL)))
            filePrefix = os.path.splitext(os.path.basename(oneFile))[0]
            outFilePath = os.path.join(outputTestDir,filePrefix+'_ff.fits')
            
            HDUListorig = fits.open(oneFile)
            reducedSlope = HDUListorig[0].data[0] / flat_field
            outHDU = fits.PrimaryHDU(reducedSlope,header=HDUListorig[0].header)
            outHDU.header['FFDIVIDE'] = (True, 'Data divided by flat field?')
            outHDU.header['FFNAME'] = ('flat_for_{}.fits'.format(oneTest), 'Name of flat field')
            outHDU.writeto(outFilePath,overwrite=True)
            HDUListorig.close()


        
if __name__ == '__main__':
    subtract_all_files()
