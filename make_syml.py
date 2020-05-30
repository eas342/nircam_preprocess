import glob
import numpy as np
from subprocess import call
import os
from astropy.io import fits
import yaml
from shutil import copyfile
import pdb
from copy import deepcopy

paramFile = 'parameters/pipe_params.yaml'
if os.path.exists(paramFile) == False:
    copyfile('parameters/example_pipe_params.yaml',paramFile)
with open(paramFile) as paramFileOpen:
    symLinkParam = yaml.safe_load(paramFileOpen)

if 'dmsConvert' not in symLinkParam:
    symLinkParam['dmsConvert'] = False

defaultDirSearch = '/surtrdata/Local/AZLab/Dark/Test2/*.fits'
def build_files(dirSearch=defaultDirSearch):
    if os.path.exists(symLinkParam['baseDir']) == False:
        os.mkdir(symLinkParam['baseDir'])
    
    for oneFile in glob.glob(dirSearch):
        baseName = os.path.basename(oneFile)
        preName = os.path.splitext(baseName)[0]
        dirName = os.path.join(symLinkParam['baseDir'],preName)
        if os.path.exists(dirName) == False:
            os.mkdir(dirName)
        link = os.path.join(dirName,baseName)
        if os.path.exists(link) == False:
            call(['ln','-s',oneFile,link])

defaultBreaknint = ('/surtrdata1/tso_analysis/AZLab_darks/rpi_vs_rpf_all/'+
                    'NRCTEST2RPF_1_487_S_2019-05-30T21h50m51/NRCTEST2RPF_1_487_S_2019-05-30T21h50m51.fits')

def merge_headers(head_prim,head_sci):
    """ This function merges the Primary and Science headers from the DMS format
    
    """
    dontCopy = ['SIMPLE','BITPIX','NAXIS','EXTEND']
    
    head = fits.Header(head_sci)
    head.append(('',''),end=True)
    head.append(('',''),end=True)
    head.append(('','     Primary Header Stuff '),end=True)
    head.append(('',''),end=True)
    head.append(('',''),end=True)
    for card in head_prim.cards:
        if card[0] not in dontCopy:
            head.append((card[0],card[1],card[2]),end=True)
    
    return head


def dms_plurals_to_singlular(head):
    """
    This adds the singular header keyword used in Fitswriter
    ie. NGROUP = NGROUPS
    """
    plurals = ['NINTS','NFRAMES','NGROUPS']
    for onePlural in plurals:
        singular = onePlural[:-1]
        head[singular] = (head[onePlural],head.comments[onePlural])
    return head

def dms_to_fitswriter_head(head):
    head = dms_plurals_to_singlular(head)
    if 'DETECTOR' not in head:
        raise Exception("Couldn't find detector name to know how to assign SCA_ID")
    elif head['DETECTOR'] == 'NRCALONG':
        head['SCA_ID'] = (485, 'Detector ID')
    else:
        raise Exception("Need to add this detector {}".format(head['DETECTOR']))
    
    if 'SUBARRAY' not in head:
        raise Exception("Couldn't find subarray name in head to place subarray")
    elif head['SUBARRAY'] == 'FULL':
        head['COLCORNR'] = (1, "Starting column number")
        head['ROWCORNR'] = (1, "Starting row number")
        head['TREFROW'] = (4,'top reference pixel rows   ')
        head['BREFROW'] = (4,'bottom reference pixel rows')
        head['LREFCOL'] = (4,'left col reference pixels  ')
        head['RREFCOL'] = (4,'right col reference pixels ')
    
    elif 'SUBGRISM' in head['SUBARRAY']:
        head['COLCORNR'] = (1, "Starting column number")
        head['ROWCORNR'] = (1, "Starting row number")
        head['TREFROW'] = (0,'top reference pixel rows   ')
        head['BREFROW'] = (4,'bottom reference pixel rows')
        head['LREFCOL'] = (4,'left col reference pixels  ')
        head['RREFCOL'] = (4,'right col reference pixels ')
    else:
        raise Exception("Need to add this subarray {}".format(head['SUBARRAY']))
    
    head['READOUT'] = (head['READPATT'], 'Readout pattern')
    
    return head

def flip_data(data,head):
    """ This flips the detector coordinates from DMS to the Fitswriter way"""
    
    if 'DETECTOR' not in head:
        raise Exception("Couldn't find detector name to know how to flip")
    elif head['DETECTOR'] == 'NRCALONG':
        return data[:,:,::-1]
    else:
        raise NotImplementedError("Need to add this detector")


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
          Summer 2019 - converting to Python (eas342@email.arizona.edu)
    """
    HDUList = fits.open(fitsFile)
    
    if symLinkParam['dmsConvert'] == True:
        ## combine the header info together
        head_prim = HDUList[0].header
        head_sci = HDUList['SCI'].header
        
        head = merge_headers(head_prim,head_sci)
        head = dms_to_fitswriter_head(head)
        
        dat = HDUList['SCI'].data
        nr = dat.shape[0] * dat.shape[1]
        
    else:
            
        head = HDUList[0].header
        dat = HDUList[0].data
    
        # Get data axes
        nx = dat.shape[2]
        ny = dat.shape[1]
        nr = dat.shape[0]
    
    # Check nint
    if "NINT" in head:
        if symLinkParam['dmsConvert'] == True:
            int_start_num = head['INTSTART'] ## starting integration number for the segment
            ## use the value packed into the segment/file (not total)
            nint = head['INTEND'] - int_start_num + 1
            nint_orig = head['NINTS'] ## original number of integrations in exposure
        else:
            nint = head["NINT"]
            if nint == 1:  # not a packed data cube
                print("NINT is {}; {} is not a packed data cube.".format(nint,fitsFile))
                print("Going to create just one int file")
            int_start_num = 1
            nint_orig = nint
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
            print("Counting doesn't work out. NREAD must equal NGROUP*NINT")
            print('NINT:  {}'.format(nint))
            print('NGROUP: {}'.format(ngroup))
            print('NGROUP*NINT: {}'.format(ngroup * nint))
            print('NREAD: {}'.format(nr))
            return
    
    # start your engines. 
    BaseName = os.path.splitext(fitsFile)[0]
    print(fitsFile)
    print(BaseName)
    z0=0
    z1=z0+ngroup-1
    for i in np.arange(nint): # Loop over nints
        if np.mod(i,40) == 0:
            print("Breaking int {} of {}".format(i,nint))
        
        FullHeader=deepcopy(head)
        
        tmpStr="{:05d}".format(i+int_start_num-1)
        
        if symLinkParam['dmsConvert'] == True:
            _thisint = flip_data(dat[i],head)
        else:
            # Get this block on nint
            if nint == 1:
                _thisint = dat
            else:
                _thisint = dat[z0:z1+1]
        _thisheader = FullHeader
        _thisfile = BaseName + '_I' + tmpStr + '.fits'
        _thisheader['NINT'] = 1 # set nint to 1
        _thisheader.insert("NINT",("ON_NINT",i+int_start_num,"This is INT of TOT_NINT"))
        _thisheader.insert("ON_NINT",("TOT_NINT",nint_orig,"Total number of NINT in original exposure"))
        if symLinkParam['dmsConvert'] == True:
            ## keep track of yet another NINT, which is for the total exposure
            _thisheader.insert("TOT_NINT",("SEGNINT",nint,"Total number of NINT in the segment or file"))
        
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
        
        fitsSearch = os.path.join(basedir,test,'*.fits')
        for datfile in glob.glob(fitsSearch):
            ## Skip the original file containing the entire exposure
            if datfile != os.path.join(basedir,test,'{}.fits'.format(test)):
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
