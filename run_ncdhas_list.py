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
from os import listdir, getcwd
from sys import argv
from copy import deepcopy
from astropy.io import fits
import glob

ncdhas      = '/usr/local/ncdhas/ncdhas'



''' Setup File Structures '''
basedir     = '/data1/tso_analysis/all_tso_cv3/'
if basedir == getcwd():
    basedir = ''

if len(argv) <2:
    raise Exception('No argument specified.')

if len(argv) >= 3:
    if argv[2] == 'test':
        rawdir = 'one_file_tests/'
    else:
        raise Exception('Unexpected input')
else:
    rawdir      = 'raw_separated_'
    rawdir      = rawdir + argv[1] + '/'


set_raw_dirs= listdir(basedir + rawdir)

raw_files       = {}

ignoretypes = ['.red.','.dia.','.slp.','.cds.','.txt']
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
flatsuffix = '*PFlat_F150W_CLEAR_2016-04-05.fits'

for dirNow in raw_files.keys():
    dirOutput = []
    for filename in raw_files[dirNow]:
        fileNOW     = basedir + rawdir + dirNow + '/' + filename
        head = fits.getheader(fileNOW)
        if argv[1][2] == 'P':
            flatname = glob.glob(flatdir+head['DETECTOR']+'*.fits')
            flatname = glob.glob(flatdir+head['DETECTOR']+flatsuffix)
            flagsNOW = flagChoice +' +FFf '+ flatname[0]
        else:
            flagsNOW = flagChoice

        cmd = ncdhas+' '+fileNOW+' '+flagsNOW
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

    with open(basedir + rawdir + dirNow+'/ncdhas_output.txt','w') as outputfile:
        for line in dirOutput:
            outputfile.write(line+'\n')
            
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
