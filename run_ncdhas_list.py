'''
1:  -ipc -cl -cf    DONE
2:  +ipc -cl -cf    DOING
3:  -ipc +cl -cf    NOT DONE
4:  -ipc -cl +cf    NOT DONE
5:  +ipc +cl -cf    NOT DONE
6:  +ipc -cl +cf    NOT DONE
7:  -ipc +cl +cf    NOT DONE
8:  +ipc +cl +cf    NOT DONE
'''

import pdb
from subprocess import call
from os import listdir, getcwd
from sys import argv
from copy import deepcopy

ncdhas      = '/usr/local/ncdhas/ncdhas'

''' Setup Flag Structures '''
''' Everett suggests ALWAYS having CBS on: (A + B2) - (A + B1) = B2 - B1 (+cbs removes A from all frames) '''

''' start without CDS'''
flags_all   = '+ow +wi +wd +ws -rx +rc -rss +rsf +cbp +cs +cbs -cd'

p_ipc   = ' +ipc'
m_ipc   = ' -ipc'
p_cl    = ' +cl'
m_cl    = ' -cl'
p_cf    = ' +cf'
m_cf    = ' -cf'

flagsMMM    = flags_all + m_ipc + m_cl + m_cf  # 1  X
flagsPMM    = flags_all + p_ipc + m_cl + m_cf  # 2  X
flagsMPM    = flags_all + m_ipc + p_cl + m_cf  # 3  X
flagsMMP    = flags_all + m_ipc + m_cl + p_cf  # 4  X
flagsPPM    = flags_all + p_ipc + p_cl + m_cf  # 5  X
flagsPMP    = flags_all + p_ipc + m_cl + p_cf  # 6  X
flagsMPP    = flags_all + m_ipc + p_cl + p_cf  # 7  X
flagsPPP    = flags_all + p_ipc + p_cl + p_cf  # 8  X

''' Setup File Structures '''
basedir     = '/data/External/ISIMCV3_unzipped/NRCN821/fitsfilesonly/'
if basedir == getcwd():
    basedir = ''

rawdir      = 'raw_separated_'
rawdir      = rawdir + argv[1] + '/'

set_raw_dirs= listdir(basedir + rawdir)

raw_files       = {}

ignoretypes = ['.red.','.dia.','.slp.','.cds.']
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

exec("flagsNOW    = flags" + argv[1])

# ''' Now run without CDS '''
# for dirNow in raw_files.keys():
#     for filename in raw_files[dirNow]:
#         fileNOW     = basedir + rawdir + dirNow + '/' + filename
#         call([ncdhas, fileNOW, flagsNOW])

# for dirNow in raw_files.keys():
#     red_files_list = basedir + rawdir + dirNow + '/' + '*.*.fits'
#     call(['/bin/mkdir', '-p', basedir + reddir + dirNow])
#     call(['/bin/mv'   , red_files_list, basedir + reddir + dirNow + '/' ])

''' Now run with CDS '''
flags_all   = '+ow -wi -wd +ws -rx +rc -rss +rsf +cbp +cs +cbs -cd +cds'

p_ipc   = ' +ipc'
m_ipc   = ' -ipc'
p_cl    = ' +cl'
m_cl    = ' -cl'
p_cf    = ' +cf'
m_cf    = ' -cf'

flagsMMM    = flags_all + m_ipc + m_cl + m_cf  # 1  X
flagsPMM    = flags_all + p_ipc + m_cl + m_cf  # 2  X
flagsMPM    = flags_all + m_ipc + p_cl + m_cf  # 3  X
flagsMMP    = flags_all + m_ipc + m_cl + p_cf  # 4  X
flagsPPM    = flags_all + p_ipc + p_cl + m_cf  # 5  X
flagsPMP    = flags_all + p_ipc + m_cl + p_cf  # 6  X
flagsMPP    = flags_all + m_ipc + p_cl + p_cf  # 7  X
flagsPPP    = flags_all + p_ipc + p_cl + p_cf  # 8  X

exec("flagsNOW    = flags" + argv[1])
# flagsNOW    = flagsNOW

for dirNow in raw_files.keys():
    for filename in raw_files[dirNow]:
        fileNOW     = basedir + rawdir + dirNow + '/' + filename
        pdb.set_trace()
        call([ncdhas, fileNOW, flagsNOW])

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
