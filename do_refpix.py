import pynrc
import pynrc.reduce.ref_pixels
import numpy as np
from astropy.io import fits, ascii
import glob
import os
from os import listdir, getcwd
from subprocess import call
from shutil import copyfile
import yaml
import pdb
from copy import deepcopy
import make_syml
from multiprocessing import Pool
import warnings

pynrc.setup_logging('WARN', verbose=False)

biasDir = '/usr/local/nircamsuite/ncdhas/cal/Bias/'

paramFile = 'parameters/pipe_params.yaml'
if os.path.exists(paramFile) == False:
    copyfile('parameters/example_pipe_params.yaml',paramFile)
with open(paramFile) as paramFileOpen:
    symLinkParam = yaml.safe_load(paramFileOpen)

if 'skipSide' in symLinkParam:
    if symLinkParam['skipSide'] == True:
        skipSide = True
    else:
        skipSide = False
else:
    skipSide = False
    
dirname = 'raw_separated_refpix'
linkDir = os.path.join(symLinkParam['symLinkDir'],'symlinks_separated')
outDir = os.path.join(symLinkParam['symLinkDir'],dirname)

def make_symlink_dir():
    ## First make a copy of symlinks
    linkDir = os.path.join(symLinkParam['symLinkDir'],'symlinks_separated')
    if os.path.exists(outDir) == False:
        os.mkdir(outDir)
        #call('cp -r {} {}'.format(linkDir,outDir),shell=True)
        #No need to copy files again since we'll process them and make new ones here
    
def get_rawfiles():
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
    return raw_files

def get_bias(dat,header):
    nZ, nY, nX = dat.shape
    if ('DETECTOR' in header):
        skip_bias = False
        if header['DETECTOR'] == 'NRCALONG':
            bias_name = 'NRCA5_17158_Bias_ISIMCV3_2016-02-09.fits'
        elif header['DETECTOR'] == 'NRCA1':
            bias_name = 'NRCA1_17004_Bias_ISIMCV3_2016-02-09.fits'
        elif header['DETECTOR'] == 'NRCA2':
            bias_name = 'NRCA2_17006_Bias_ISIMCV3_2016-02-09.fits'
        elif header['DETECTOR'] == 'NRCA3':
            bias_name = 'NRCA3_17012_Bias_ISIMCV3_2016-02-09.fits'
        elif header['DETECTOR'] == 'NRCA4':
            bias_name = 'NRCA4_17048_Bias_ISIMCV3_2016-02-09.fits'
        elif header['DETECTOR'] == 'NRCBLONG':
            bias_name = 'NRCB5_17161_Bias_ISIMCV3_2016-02-09.fits'
        elif header['DETECTOR'] == 'NRCB1':
            bias_name = 'NRCB1_16991_Bias_ISIMCV3_2016-02-09.fits'
        elif header['DETECTOR'] == 'NRCB2':
            bias_name = 'NRCB2_17005_Bias_ISIMCV3_2016-02-09.fits'
        elif header['DETECTOR'] == 'NRCB3':
            bias_name = 'NRCB3_17011_Bias_ISIMCV3_2016-02-09.fits'
        elif header['DETECTOR'] == 'NRCB4':
            bias_name = 'NRCB4_17047_Bias_ISIMCV3_2016-02-09.fits'
        else:
            skip_bias = True

        
        ## cut out bias and tile it to match the cube, if there is a bias
        if skip_bias == True:
            bias_cube = 0
        else:
            bias_file = os.path.join(biasDir,bias_name)
            bias_full = fits.getdata(bias_file,extname='SCI')
            startX = header['COLCORNR'] - 1
            endX = startX + nX
            startY = header['ROWCORNR'] - 1
            endY = startY + nY
            bias_cut = bias_full[startY:endY,startX:endX]
            bias_cube = np.tile(bias_cut,[nZ,1,1])
            
    else:
        bias_cube = 0
    return bias_cube


def one_file_refpix(allInput):
    fileName,linkDir,dirNow,saveDir = allInput
    HDUList = fits.open(os.path.join(linkDir,dirNow,fileName))
    dat = HDUList[0].data
    header = HDUList[0].header
    bias_cube = get_bias(dat,header)
    
    refObject = pynrc.reduce.ref_pixels.NRC_refs(dat-bias_cube,header,altcol=True)
    refObject.calc_avg_amps()
    refObject.correct_amp_refs()
    refObject.calc_avg_cols(avg_type='pixel')
    refObject.calc_col_smooth(savgol=True)
    if (refObject.refs_side_avg is None) | (skipSide == True):
        pass ## can't do side ref correction with no side ref pixels
    else:
        refObject.correct_col_refs()
    
    useDat = refObject.data #+ bias_cube
    header['REFPIX'] = (True,'pynrc reference pixel applied?')
    header['SKIPSD'] = (skipSide,'Skip the side reference pixel correction?')
    outName = os.path.join(saveDir,fileName)
    primHDU = fits.PrimaryHDU(useDat,header=header)
    
    if os.path.exists(outName) == True:
        print("Already found {}. Skipping.".format(outName))
    else:
        primHDU.writeto(outName,overwrite=True)
        
    HDUList.close()


def do_refpix(testMode=False):
    raw_files = get_rawfiles()
    for dirNow in raw_files.keys():
        print("Working on directory {} of {}".format(dirNow,len(raw_files.keys())))
        saveDir = os.path.join(outDir,dirNow)
        
        if os.path.exists(saveDir) == False:
            os.mkdir(saveDir)
        
        if testMode == True:
            useFiles = [raw_files[dirNow][0]]
        else:
            useFiles = raw_files[dirNow]
        
        inputList = []
        for fileName in useFiles:
            inputList.append([fileName,linkDir,dirNow,saveDir])
            #one_file_refpix([fileName,linkDir,dirNow,saveDir])
        
        p = Pool(12)
        p.map(one_file_refpix,inputList)


def do_testrun():
    do_refpix(testMode=True)

def do_all_pipeline(pipeParamsFileName='parameters/pipe_params.yaml'):
    with open(pipeParamsFileName) as pipeParamFile:
        pipeParams = yaml.safe_load(pipeParamFile)
    
    ## Correct reference pixels with pynrc since it works on subarrays
    make_symlink_dir()
    do_refpix()
    
    print("Making symbolic links to refence-corrected integrations...")
    ## Make symbolic links to the files that have been reference pixel corrected
    make_syml.make_syml(fromRefPix=True)
    
    ## copy the symbolic links where ncdas will be run
    symlinks_sep_refpix = os.path.join(pipeParams['symLinkDir'],'symlinks_sep_refpix')
    
    for runDirectory_baseName in ['raw_separated_MMM_refpix','raw_separated_MPM_refpix']:
        runDirectory = os.path.join(pipeParams['symLinkDir'],runDirectory_baseName)
        if os.path.exists(runDirectory) == False:
            os.mkdir(runDirectory)
        call('cp -r {}/* {}'.format(symlinks_sep_refpix,runDirectory),shell=True)


if __name__ == "__main__":
    do_all_pipeline()
