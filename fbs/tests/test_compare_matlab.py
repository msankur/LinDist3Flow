# convert a mat struct into python dictionary
# copied from this post: https://stackoverflow.com/review/suggested-edits/21667510

import scipy
import scipy.io as spio
from fbs.utils import init_from_dss
from fbs.fbs import fbs
import pytest
import opendssdirect as dss
import numpy as np
import pandas as pd

parent_path = 'fbs/tests/05n3ph_unbal/'
dss_file = parent_path + 'compare_opendss_05node_threephase_unbalanced_oscillation_03.dss'
mat_struct = 'fbs/tests/05n3ph_unbal/05n3ph_unbal_network.mat'

# maps matlab node names to python node names
NODE_DICT = {
    'sub': 'sourcebus',
    'A01': 'a01',
    'A02': 'a02',
    'A03': 'a03',
    'A04': 'a04',
    'A05': 'a05',
    'A06': 'a06',
}
# CONFIRM NETWORK MAPPING-------------------------------------------------------

def test_FZpu(py_network, mat_network):
    tolerance = 10**-6
    py_lines = py_network.get('Lines')
    mat_lines = mat_network.get('lines')
    err = []
    index = []
    for mat_line_idx in range(mat_lines.get('nline')):
        mat_tx = mat_lines.get('TXname')[mat_line_idx]
        mat_rx = mat_lines.get('RXname')[mat_line_idx]
        py_line_key = f"('{NODE_DICT.get(mat_tx)}', '{NODE_DICT.get(mat_rx)}')"
        mat_FZ = mat_lines.get('FZpu').transpose()[mat_line_idx]
        py_FZ = py_lines.loc[py_line_key].FZpu
        err.append(np.abs((np.subtract(py_FZ, mat_FZ))).max())
        index.append(py_line_key)
    df = pd.DataFrame(err, index, ['err'])
    # print(df)
    assert (df.err <= tolerance).all()

# TODO: CONFIRM SOLUTION VARS-------------------------------------------------------


# FIXTURES AND HELPERS-------------------------------------------------------
@pytest.fixture
def fbssol_py(py_network):
    return fbs(dss_file)


@pytest.fixture
def py_network():
    """setup test network from dss_file"""
    return init_from_dss(dss_file).to_dataframes()


@pytest.fixture
def mat_network():
    """ Load matlab network struct into a python dictionary """
    n = loadmat(mat_struct).get('network1')
    return n


@pytest.fixture
def get_dss_instance():
    """set-up dss instance for dss_file"""
    dss.run_command('Redirect ' + dss_file)
    return None


def loadmat(filename):
    '''
    this function should be called instead of direct spio.loadmat
    as it cures the problem of not properly recovering python dictionaries
    from mat files. It calls the function check keys to cure all entries
    which are still mat-objects
    '''
    def _check_keys(d):
        '''
        checks if entries in dictionary are mat-objects. If yes
        todict is called to change them to nested dictionaries
        '''
        for key in d:
            if isinstance(d[key], spio.matlab.mio5_params.mat_struct):
                d[key] = _todict(d[key])
        return d

    def _has_struct(elem):
        """Determine if elem is an array and if any array item is a struct"""
        return isinstance(elem, np.ndarray) and any(isinstance(
                    e, scipy.io.matlab.mio5_params.mat_struct) for e in elem)

    def _todict(matobj):
        '''
        A recursive function which constructs from matobjects nested dictionaries
        '''
        d = {}
        for strg in matobj._fieldnames:
            elem = matobj.__dict__[strg]
            if isinstance(elem, spio.matlab.mio5_params.mat_struct):
                d[strg] = _todict(elem)
            elif _has_struct(elem):
                d[strg] = _tolist(elem)
            else:
                d[strg] = elem
        return d

    def _tolist(ndarray):
        '''
        A recursive function which constructs lists from cellarrays
        (which are loaded as numpy ndarrays), recursing into the elements
        if they contain matobjects.
        '''
        elem_list = []
        for sub_elem in ndarray:
            if isinstance(sub_elem, spio.matlab.mio5_params.mat_struct):
                elem_list.append(_todict(sub_elem))
            elif _has_struct(sub_elem):
                elem_list.append(_tolist(sub_elem))
            else:
                elem_list.append(sub_elem)
        return elem_list
    data = scipy.io.loadmat(filename, struct_as_record=False, squeeze_me=True)
    return _check_keys(data)
