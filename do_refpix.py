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

paramFile = 'parameters/symLinkParams.yaml'
if os.path.exists(paramFile) == False:
    raise Exception("No symlink params file found")
symLinkParam = yaml.load(open(paramFile))

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
        
        for fileName in useFiles:
            HDUList = fits.open(os.path.join(linkDir,dirNow,fileName))
            dat = HDUList[0].data
            useDat = pynrc.reduce.ref_pixels.reffix_hxrg(dat,nchans=4,in_place=True,fixcol=True,
                                                         altcol=True,ntop=0,nbot=4,left_ref=4,
                                                         right_ref=4)
            dat = HDUList[0].data
            header = HDUList[0].header
            header['REFPIX'] = (True,'pynrc reference pixel applied?')
            outName = os.path.join(saveDir,fileName)
            primHDU = fits.PrimaryHDU(useDat,header=header)
            
            if os.path.exists == outName:
                print("Already found {}. Skipping.".format(outName))
            else:
                primHDU.writeto(outName,overwrite=True)
            
            HDUList.close()


def do_testrun():
    do_refpix(testMode=True)

if __name__ == "__main__":
    make_symlink_dir()
    do_refpix()
    make_syml.make_syml(fromRefPix=True)
