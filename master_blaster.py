import do_refpix
import make_syml
import glob
import os
from subprocess import call
from sys import argv
import yaml

## Must be run with the astroconda environment where I installed pynrc
## (if wanting to use his reference pixel routines)

def run_all():
    with open('parameters/pipe_params.yaml') as pipeParamFile:
        pipeParams = yaml.load(pipeParamFile)
    
    origFiles = pipeParams['originalFiles']
    
    print("Making symbolic links to original files...")
    
    ## Build symbolic links to original files
    make_syml.build_files(origFiles)
    
    print("Breaking original exposures into individual ints...")
    ## break all exposures into individual integrations
    origList = glob.glob(origFiles)
    for oneRamp in origList:
        baseName = os.path.basename(oneRamp)
        preName = os.path.splitext(baseName)[0]
        path = os.path.join(pipeParams['baseDir'],preName,baseName)
        make_syml.breaknint(path)
    
    print("Making symbolic links to individual integrations...")
    make_syml.make_syml()
    
    if 'pynrcRefpix' not in pipeParams:
        pynrcRefpix = True
    else:
        pynrcRefpix = pipeParams['pyrncRefpix']
    
    if pynrcRefpix == True:
        print("Applying pynrc reference pixel corrections...")
        ## Correct reference pixels with pynrc since it works on subarrays
        do_refpix.make_symlink_dir()
        do_refpix.do_refpix()
        
        print("Making symbolic links to refence-corrected integrations...")
        ## Make symbolic links to the files that have been reference pixel corrected
        make_syml.make_syml(fromRefPix=True)
        
        ## copy the symbolic links where ncdas will be run
        symlinks_sep_refpix = os.path.join(pipeParams['symLinkDir'],'symlinks_sep_refpix')
        runDirectory = os.path.join(pipeParams['symLinkDir'],'raw_separated_MMM_refpix')
        if os.path.exists(runDirectory) == False:
            os.mkdir(runDirectory)
        call('cp -r {}/* {}'.format(symlinks_sep_refpix,runDirectory),shell=True)
        
        print("Running NCDHAS on reference-corrected data...")
        ## Run this command line version of ncdhas
        call('python run_ncdhas_list.py MMM refpix',shell=True)
    else:
        symlinks_sep = os.path.join(pipeParams['symLinkDir'],'symlinks_separated')
        runDirectory = os.path.join(pipeParams['symLinkDir'],'raw_separated_MMM')
        call('cp -r {}/* {}'.format(symlinks_sep,runDirectory),shell=True)
        print("Running NCDHAS on MMM data...")
        ## Run this command line version of ncdhas
        call('python run_ncdhas_list.py MMM',shell=True)
    
if __name__ == "__main__":
    run_all()
