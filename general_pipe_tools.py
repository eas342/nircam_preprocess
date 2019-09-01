import glob
import numpy as np
import os
from astropy.io import fits, ascii
import yaml
from shutil import copyfile
import pdb
from copy import deepcopy

def get_pipe_params():

    paramFile = 'parameters/pipe_params.yaml'
    if os.path.exists(paramFile) == False:
        copyfile('parameters/example_pipe_params.yaml',paramFile)
    with open(paramFile) as paramFileOpen:
        pipeParam = yaml.safe_load(paramFileOpen)

    return pipeParam
