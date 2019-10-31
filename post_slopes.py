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
rowColSubDir = os.path.join(baseDir,'slope_post_process')
flatDir = os.path.join(baseDir,'flat_fields')
dividedDir = os.path.join(baseDir,'flat_fielded')
profileDir = os.path.join(baseDir,'profiles')

for onePath in [rowColSubDir,flatDir,dividedDir,profileDir]:
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

if 'profileXRange' not in pipeParam:
    pipeParam['profileXRange'] = {487: [   4, 1050],
                                  488: [   4, 1877],
                                  489: [ 160, 2043],
                                  490: [1040, 2043]}

if 'profileYRange' not in pipeParam:
    pipeParam['profileYRange'] = {487: [0, 251],
                                  488: [0, 160],
                                  489: [0, 169],
                                  490: [0, 251]}

if 'indices_for_flatfield' not in pipeParam:
    pipeParam['indices_for_flatfield'] = [None, None]


def get_param_from_scaID(head,lookupDict):
    """
    Get the SCA ID from the header
    """
    if 'SCA_ID' not in head:
        raise Exception("Could not find SCA ID")
    elif head['SCA_ID'] not in lookupDict.keys():
        raise Exception("Could not find parameters for SCA {}".format(head['SCA_ID']))
    else:
        return lookupDict[head['SCA_ID']]
    

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
    rowsToMedian = get_param_from_scaID(head,pipeParam['rowsUse'])
    colsToMedian = get_param_from_scaID(head,pipeParam['colsUse'])
    
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
        outputTestDir = os.path.join(rowColSubDir,oneTest)
        
        if os.path.exists(outputTestDir) == False:
            os.mkdir(outputTestDir)
        fileL = np.sort(glob.glob(os.path.join(inputTestDir,'*.slp.fits')))
        for fileInd,oneFile in enumerate(fileL):
            if np.mod(fileInd,50) == 0:
                print("Working on integration {} of {}".format(fileInd,len(fileL)))
            filePrefix = os.path.splitext(os.path.basename(oneFile))[0]
            outFilePath = os.path.join(outputTestDir,filePrefix+'_rowcolsub.fits')
            outHDU = do_subtraction(oneFile,outFilePath)
            
def get_files_for_flat_fielding(oneTest,useRowCol=True):
    """
    Get files for flat fielding
    
    Parameters
    -----------
    oneTest: string
       Name of the exposure directory
    
    useRowCol: bool
       Use data where columns and rows have been subtracted?
    """
    if useRowCol == True:
        inputTestDir = os.path.join(rowColSubDir,oneTest)
        wildCard = '*.slp_rowcolsub.fits'
    else:
        inputTestDir = os.path.join(procDir,oneTest)
        wildCard = '*.slp.fits'
    
    return wildCard, inputTestDir

def find_flat_fields(useRowCol=True):
    """
    Find flat fields for a given set of indices
    
    Parameters
    -----------
    useRowCol: bool
       Use data that has had rows and columns subtracted?
    
    """
    testNames = os.listdir(procDir)
    
    for testInd,oneTest in enumerate(testNames):
        print("Working on Exposure {} ({} of {})".format(oneTest,testInd,len(testNames)))
        wildCard, inputTestDir = get_files_for_flat_fielding(oneTest,useRowCol)
        
        outputTestDir = os.path.join(flatDir,oneTest)
        if os.path.exists(outputTestDir) == False:
            os.mkdir(outputTestDir)
        fullFileL = np.sort(glob.glob(os.path.join(inputTestDir,wildCard)))
        
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
            if useRowCol == True:
                allSlopes[fileInd,:,:] = oneImg ## a 2D image
            else:
                allSlopes[fileInd,:,:] = oneImg[0] ## a 3D cube
        
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

def divide_all_files(useRowCol=True):
    """
    Divide each image by flat field for a given set of indices
    
    Parameters
    -----------
    useRowCol: bool
       Use data that has had rows and columns subtracted?
    
    """
    testNames = os.listdir(procDir)
    
    for testInd,oneTest in enumerate(testNames):
        print("Working on Exposure {} ({} of {})".format(oneTest,testInd,len(testNames)))
        wildCard, inputTestDir = get_files_for_flat_fielding(oneTest,useRowCol)
        
        outputTestDir = os.path.join(dividedDir,oneTest)
        calDir = os.path.join(flatDir,oneTest)
        if os.path.exists(outputTestDir) == False:
            os.mkdir(outputTestDir)
        fileL = np.sort(glob.glob(os.path.join(inputTestDir,wildCard)))

        flatName = os.path.join(calDir,'flat_for_{}.fits'.format(oneTest))
        flat_field = fits.getdata(flatName)
        
        for fileInd,oneFile in enumerate(fileL):
            if np.mod(fileInd,50) == 0:
                print("Working on integration {} of {}".format(fileInd,len(fileL)))
            filePrefix = os.path.splitext(os.path.basename(oneFile))[0]
            outFilePath = os.path.join(outputTestDir,filePrefix+'_ff.fits')
            
            HDUListorig = fits.open(oneFile)
            if useRowCol == True:
                origData = HDUListorig[0].data ## a 2D image
            else:
                origData = HDUListorig[0].data[0] ## a 3D cube
            
            reducedSlope = origData / flat_field
            outHDU = fits.PrimaryHDU(reducedSlope,header=HDUListorig[0].header)
            outHDU.header['FFDIVIDE'] = (True, 'Data divided by flat field?')
            outHDU.header['FFNAME'] = ('flat_for_{}.fits'.format(oneTest), 'Name of flat field')
            outHDU.writeto(outFilePath,overwrite=True)
            HDUListorig.close()


def extract_illum_profiles():
    """
    Extract illumination profiles for all images
    """
    testNames = os.listdir(procDir)
    
    for testInd,oneTest in enumerate(testNames):
        print("Working on Exposure {} ({} of {})".format(oneTest,testInd,len(testNames)))
        inputTestDir = os.path.join(dividedDir,oneTest)
        
        fileList = np.sort(glob.glob(os.path.join(inputTestDir,'*rowcolsub_ff.fits')))
        
        nFile = len(fileList)
    
        head = fits.getheader(fileList[0])
        xRange = get_param_from_scaID(head,pipeParam['profileXRange'])
        yRange = get_param_from_scaID(head,pipeParam['profileYRange'])
        
        xCoordinates = np.arange(xRange[0],xRange[1])
        profileArray = np.zeros([nFile,xRange[1] - xRange[0]])
        
        for ind,oneFile in enumerate(fileList):
            if np.mod(ind,50) == 0:
                print("Reading integration {} of {}".format(ind,nFile))
            
            img = fits.getdata(oneFile)
            profile = np.mean(img[yRange[0]:yRange[1],xRange[0]:xRange[1]],axis=0)
            profileArray[ind,:] = profile
        
        head = fits.getheader(fileList[0])
        primHDU = fits.PrimaryHDU(profileArray,head)
        xCoordHDU = fits.ImageHDU(xCoordinates)
        
        HDUList = fits.HDUList([primHDU,xCoordHDU])
        HDUList.writeto(os.path.join(profileDir,'profiles_for_{}.fits'.format(oneTest)),overwrite=True)
    
        
if __name__ == '__main__':
    subtract_all_files()
