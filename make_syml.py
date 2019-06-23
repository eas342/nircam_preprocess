import glob
import numpy as np
from subprocess import call
import os
import ipdb
from astropy.io import fits
import yaml
from shutil import copyfile
import pdb
from copy import deepcopy

paramFile = 'parameters/symLinkParams.yaml'
if os.path.exists(paramFile) == False:
    copyfile('parameters/symLinkParam_example.yaml',paramFile)
symLinkParam = yaml.load(open(paramFile))


defaultDirSearch = '/surtrdata/Local/AZLab/Dark/Test2/*.fits'
def build_files(dirSearch=defaultDirSearch):
    for oneFile in glob.glob(dirSearch):
        baseName = os.path.basename(oneFile)
        preName = os.path.splitext(baseName)[0]
        dirName = os.path.join(symLinkParam['baseDir'],preName)
        if os.path.exists(dirName) == False:
            os.mkdir(dirName)
        link = os.path.join(dirName,baseName)
        call(['ln','-s',oneFile,link])

defaultBreaknint = ('/surtrdata1/tso_analysis/AZLab_darks/rpi_vs_rpf_all/'+
                    'NRCTEST2RPF_1_487_S_2019-05-30T21h50m51/NRCTEST2RPF_1_487_S_2019-05-30T21h50m51.fits')

def breaknint(fitsFile=defaultBreaknint):
    """
    
    NAME:
    ---------
    
    
    PURPOSE:
    ---------
          Separate a 'nominal' NIRCam exposure of NINTS packed into a 
          cube into separate FITS files for each integration. 
    
    CATEGORY:
    ---------
          Data analysis, NIRCam 
    
    
    Parameters
    ------------
    fitsFile: str
        Fits file

    
    DESCRIPTION:
    ------------
          A nominal NIRCam exposure will consist of NINT individual
          ramps. For some reason, someone though it's a good idea to
          make the exposure into a DATA CUBE of size (NX,NY,NZ) where NZ
          is NINT*NGROUP.  A CUBE.  Not extensions, not single files, A
          CUBE. So this code breaks up the exposure into individual FITS
          files, one for each integration. 
    
    MODIFICATION HISTORY:
          Spring 2012 - Created; putridmeat (misselt@as.arizona.edu)
          Summ 2019 - converting to Python
    """
    HDUList = fits.open(fitsFile)
    head = HDUList[0].header
    dat = HDUList[0].data
    
    # Get data axes
    nx = dat.shape[2]
    ny = dat.shape[1]
    nr = dat.shape[0]
    
    # Check nint
    if "NINT" in head:
        nint = head["NINT"]
        if nint == 1:  # not a packed data cube
            print("NINT is {}; {} is not a packed data cube.".format(nint,fitsFile))
            return
    else:
        print("Keyword NINT not found; can't split data up.")
        return
    
    
    # check ngroup
    if "NGROUP" not in head:
        print('Keyword NGROUP not found.  Assuming NGROUP = NREAD/NINT')
        print('NREAD: {}'.format(nr))
        print('NINT:  {}'.format(nint))
        if np.mod(nr,nint) != 0:
            print("NREAD is not an even multiple of NINT. Can''t proceed")
            return
        else:
            ngroup = nr/nint
            print('Setting NGROUP to {}'.format(ngroup))
    else: # ngroup found make sure number works
        ngroup = head["NGROUP"]
        if nr != ngroup * nint:
            print("Counting doesn''t work out. NREAD must equal NGROUP*NINT")
            print('NINT:  {}'.format(nint))
            print('NGROUP: {}'.format(ngroup))
            print('NGROUP*NINT: '.format(ngroup * nint))
            print('NREAD: '.format(nr))
            return
    
    # start your engines. 
    dat = HDUList[0].data
    BaseName = os.path.splitext(fitsFile)[0]
    print(fitsFile)
    print(BaseName)
    z0=0
    z1=z0+ngroup-1
    for i in np.arange(nint): # Loop over nints
        FullHeader=deepcopy(head)
        
        tmpStr="{:04d}".format(i)
        # Get this block on nint
        _thisint = dat[z0:z1]
        _thisheader = FullHeader
        _thisfile = BaseName + '_I' + tmpStr + '.fits'
        _thisheader['NINT'] = 1 # set nint to 1
        _thisheader.insert("NINT",("ON_NINT",i+1,"This is INT of TOT_NINT"))
        _thisheader.insert("ON_NINT",("TOT_NINT",nint,"Total number of NINT in original file"))
        _thisheader["COMMENT"] = 'Extracted from a multi-integration file by ParseIntegration.pro'
        outHDU = fits.PrimaryHDU(_thisint,header=_thisheader)
        if os.path.exists(_thisfile):
            print("Found {}. Not overwriting".format(_thisfile))
        else:
            outHDU.writeto(_thisfile)
        z0 += ngroup
        z1 = z0+ngroup-1
        del outHDU
    
    HDUList.close()

def make_syml(output=symLinkParam['symLinkDir'],fromRefPix=False):
    """
    Makes symbolic links to all files
    
    Parameters
    -----------
    output: str
        where to put the directory for symbolically linked files
    fromRefPix: bool
        Use output from reference pixel correction?
    """
    if fromRefPix == True:
        basedir = os.path.join(symLinkParam['symLinkDir'],'raw_separated_refpix')
    else:
        basedir = symLinkParam['baseDir']
    
    ## make an output link directory
    if not os.path.exists(output):
        call(['mkdir',output])
    
    ## make a sub-directory for the first copy of sym links
    if fromRefPix == True:
        linkOutput = os.path.join(output,'symlinks_sep_refpix')
    else:
        linkOutput = os.path.join(output,'symlinks_separated')
    
    if not os.path.exists(linkOutput):
        call(['mkdir',linkOutput])
    tests = os.listdir(basedir)
    
    for test in tests:
        linkdir=linkOutput+'/'+test
        if not os.path.exists(linkdir):
            call(['mkdir',linkdir])
        
        fitsSearch = os.path.join(basedir,test,'*I[0123456789]*.fits')
        for datfile in glob.glob(fitsSearch):
            link = linkdir+'/'+os.path.basename(datfile)
            if os.path.exists(link) == False:
                call(['ln','-s',datfile,link])

def copy_syml():
    """
    Copies the symbolic links to all files into files for outputs
    """
    
    linkDir = os.path.join(symLinkParam['symLinkDir'],'symlinks_separated')
    for ipc in ['P','M']:
        for lin in ['P','M']:
            for flat in ['P','M']:
                dirname = 'raw_separated_'+ipc+lin+flat
                outName = os.path.join(symLinkParam['symLinkDir'],dirname)
                if os.path.exists(outName) == False:
                    call('cp -r {} {}'.format(linkDir,outName),shell=True)

def make_flats():
    """
    Makes single extension versions of the flat fields
    """
    basedir = '/usr/local/nircamsuite/cal/Flat/ISIMCV3/'
    outdir = '/data1/tso_analysis/all_tso_cv3/flat_data/'
    filel = glob.glob(basedir+'*_F150W_*.fits')
    for onefile in filel:
        if '_illumpattern' not in onefile:
            HDU = fits.open(onefile)
            outdata = HDU[1].data
            outheader = HDU[0].header
            basename, extname = os.path.splitext(os.path.basename(onefile))
            fits.writeto(outdir+basename+'_1ext.fits',outdata,outheader,clobber=True)
            HDU.close()

if __name__ == '__main__':
    make_syml()
    copy_syml()
