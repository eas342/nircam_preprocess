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

pynrc.setup_logging('WARN', verbose=False)

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

def one_file_refpix(allInput):
    fileName,linkDir,dirNow,saveDir = allInput
    HDUList = fits.open(os.path.join(linkDir,dirNow,fileName))
    dat = HDUList[0].data
    header = HDUList[0].header
    refObject = pynrc.reduce.ref_pixels.NRC_refs(dat,header,altcol=True)
    refObject.calc_avg_amps()
    refObject.correct_amp_refs()
    refObject.calc_avg_cols(avg_type='pixel')
    refObject.calc_col_smooth(savgol=True)
    if (refObject.refs_side_avg is None) | (skipSide == True):
        pass ## can't do side ref correction with no side ref pixels
    else:
        refObject.correct_col_refs()
    
    useDat = refObject.data
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
    runDirectory = os.path.join(pipeParams['symLinkDir'],'raw_separated_MMM_refpix')
    if os.path.exists(runDirectory) == False:
        os.mkdir(runDirectory)
    call('cp -r {}/* {}'.format(symlinks_sep_refpix,runDirectory),shell=True)


if __name__ == "__main__":
    do_all_pipeline()
