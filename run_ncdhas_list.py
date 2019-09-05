'''
1:  -ipc -cl -cf    
2:  +ipc -cl -cf    
3:  -ipc +cl -cf    
4:  -ipc -cl +cf    
5:  +ipc +cl -cf    
6:  +ipc -cl +cf    
7:  -ipc +cl +cf    
8:  +ipc +cl +cf    
'''

import pdb
import subprocess
from subprocess import call
from subprocess import check_output
import os
import yaml
from os import listdir, getcwd
from sys import argv
import sys
from copy import deepcopy
from astropy.io import fits
import glob
import warnings
import logging
from multiprocessing import Pool

paramFile = 'parameters/pipe_params.yaml'
if os.path.exists(paramFile) == False:
    copyfile('parameters/example_pipe_params.yaml',paramFile)
with open(paramFile) as paramFileOpen:
    ncdhasParam = yaml.safe_load(paramFileOpen)

ncdhas      = ncdhasParam['ncdhasCommand']



''' Setup File Structures '''
basedir     = ncdhasParam['symLinkDir']+'/'
if basedir == getcwd():
    basedir = ''

if len(argv) <2:
    raise Exception('No argument specified.')

if len(argv) >= 3:
    if argv[2] == 'test':
        rawdir = 'one_file_tests/'
    elif argv[2] == 'noreftest':
        rawdir = 'no_ref_one_file_tests/'
    elif argv[2] == 'norefAll':
        rawdir = 'no_ref_raw_separated_'+argv[1] + '/'
    elif argv[2] == 'fullRefAll':
        rawdir = 'full_ref_raw_separated_'+argv[1] + '/'
    elif argv[2] == 'refpix':
        rawdir = 'raw_separated_{}_refpix/'.format(argv[1])
    elif argv[2] == 'backsub_by_frame':
        rawdir = 'raw_separated_{}_backsub_by_frame/'.format(argv[1])
    else:
        raise Exception('Unexpected input')
else:
    rawdir      = 'raw_separated_'
    rawdir      = rawdir + argv[1] + '/'


set_raw_dirs= listdir(basedir + rawdir)

raw_files       = {}

ignoretypes = ['.red.','.dia.','.slp.','.cds.','.txt','ncdhas_output']
for dirNow in set_raw_dirs:
    fitsList = listdir(basedir + rawdir + dirNow)
    useList = deepcopy(fitsList)
    for onefile in fitsList:
        for ignoretype in ignoretypes:
            if ignoretype in onefile:
                useList.remove(onefile)
    raw_files[dirNow] = useList

reddir      = 'reduced_separated_'
reddir      = reddir + argv[1] + '/'

''' Setup Flag Structures '''
''' Everett suggests ALWAYS having CBS on: (A + B2) - (A + B1) = B2 - B1 (+cbs removes A from all frames) '''

''' Now run without CDS (we can always take plane [1] - plane[0] of the red image'''
if 'customFlags' in ncdhasParam:
    flags_all = ncdhasParam['customFlags']
elif 'no_ref' in rawdir:
    flags_all   = '+cfg isimcv3 +ow +wi +wd +ws -rx -rc -rss -rsf +cbp +cs +cbs -cd +mf 2 -dr'
else:
    flags_all   = '+cfg isimcv3 +ow +wi +wd +ws -rx +rc -rss +rsf +cbp +cs +cbs -cd +mf 2'

p_ipc   = ' +ipc'
m_ipc   = ' -ipc'
p_cl    = ' +cl'
m_cl    = ' -cl'
p_cf    = ' +cf'
m_cf    = ' -cf'


flagopt = {}
flagopt['MMM']    = flags_all + m_ipc + m_cl + m_cf  # 1  X
flagopt['PMM']    = flags_all + p_ipc + m_cl + m_cf  # 2  X
flagopt['MPM']    = flags_all + m_ipc + p_cl + m_cf  # 3  X
flagopt['MMP']    = flags_all + m_ipc + m_cl + p_cf  # 4  X
flagopt['PPM']    = flags_all + p_ipc + p_cl + m_cf  # 5  X
flagopt['PMP']    = flags_all + p_ipc + m_cl + p_cf  # 6  X
flagopt['MPP']    = flags_all + m_ipc + p_cl + p_cf  # 7  X
flagopt['PPP']    = flags_all + p_ipc + p_cl + p_cf  # 8  X

flags_end   = ''

flagChoice    = flagopt[argv[1]] + flags_end

flatdir = '/usr/local/nircamsuite/cal/Flat/ISIMCV3/'

def run_command_save_output(thisInput):
    """ Takes a command line input and logging file
    Run the command and save the output
    """
    cmd, loggingFileName = thisInput
    
    dirOutput=[]
    dirOutput.append('Command to be executed:')
    dirOutput.append(cmd)
    try:
        out = check_output(cmd,shell=True)
        dirOutput.append(out)
    except subprocess.CalledProcessError as e:
        saveout="command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
        dirOutput.append(saveout)
    except:
        saveout="Unknown error for command:"+cmd
        dirOutput.append(saveout)
    
    with open(loggingFileName,'w') as loggingFile:
        for line in dirOutput:
            if (type(line) != str) & (sys.version_info >= (3, 0)):
                useLine = str(line,'ascii')
            else:
                useLine = line
            useLine = useLine.replace('\\n','\n')
            loggingFile.write(useLine+'\n')


for dirNow in raw_files.keys():
    print("Working on {}...".format(dirNow))
    cmdList = []
    loggingDir = basedir + rawdir + dirNow + '/' + 'ncdhas_output'
    if os.path.exists(loggingDir) == False:
        os.mkdir(loggingDir)
    
    for filename in raw_files[dirNow]:
        fileNOW     = basedir + rawdir + dirNow + '/' + filename
        head = fits.getheader(fileNOW)
        if argv[1][2] == 'P':
            if (head['DETECTOR'] == 'NRCALONG'):
                flatsuffix = '*F444W_CLEAR_2016-04-05.fits'
                detectorName = 'NRCA5'
            elif (head['DETECTOR'] == 'NRCBLONG'):
                flatsuffix = '*F444W_CLEAR_2016-04-05.fits'
                detectorName = 'NRCB5'
            else:
                flatsuffix = '*PFlat_F150W_CLEAR_2016-04-05.fits'
                detectorName = head['DETECTOR']
            flatname = glob.glob(flatdir+detectorName+flatsuffix)
            
            if len(flatname) >= 1:
                flagsNOW = flagChoice +' +FFf '+ flatname[0]
            else:
                warnings.warn("No flat found for detector {}".format(head['DETECTOR']))
                flagsNOW = flagChoice
        else:
            flagsNOW = flagChoice

        cmd = ncdhas+' '+fileNOW+' '+flagsNOW
        namePrefix = os.path.splitext(filename)[0]
        loggingFile = os.path.join(loggingDir,'ncdhas_{}.txt'.format(namePrefix))
        cmdList.append([cmd,loggingFile])
    
    p = Pool(10)
    p.map(run_command_save_output,cmdList)

            
            
# for dirNow in raw_files.keys():
#     red_files_list = basedir + rawdir + dirNow + '/' + '*.*.fits'
#     call(['/bin/mkdir', '-p', basedir + reddir + dirNow])
#     call(['/bin/mv'   , red_files_list, basedir + reddir + dirNow + '/' ])

'''
python run_ncdhas_list.py MMM
python run_ncdhas_list.py PMM
python run_ncdhas_list.py MPM
python run_ncdhas_list.py MMP
python run_ncdhas_list.py PPM
python run_ncdhas_list.py PMP
python run_ncdhas_list.py MPP
python run_ncdhas_list.py PPP
'''
