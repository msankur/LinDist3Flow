# Smoke tests for pre-requisites to running fbs.

from powerflowpy.utils import init_from_dss
from powerflowpy.fbs import topo_sort
import pytest
import opendssdirect as dss
import numpy as np

dss_file = 'powerflowpy/tests/05n3ph_unbal/compare_opendss_05node_threephase_unbalanced_oscillation_03.dss'

@pytest.fixture
def get_network():
    """setup test network from dss_file"""
    return init_from_dss(dss_file)

@pytest.fixture
def get_dss_instance():
    """set-up dss instance for dss_file"""
    dss.run_command('Redirect ' + dss_file)
    return None

def test_init_from_dss(get_network) -> None:
    """ Compare opendss.circuit to our Network object"""
    # check that number of dss nodes equals our network's node x phases
    network = get_network
    dss_nodes = len(dss.Circuit.AllNodeNames())
    network_nodes = sum([ node.phases.count(True) for node in network.get_nodes() ])
    node_check = dss_nodes == network_nodes
    # check that number of lines match
    dss_lines = len(dss.Lines.AllNames())
    network_lines = len(network.lines)
    network_edges = sum([ len(node_list) for node_list in network.adj.values() ])
    line_check = (dss_lines == network_lines) and (dss_lines == network_edges)
    assert node_check and line_check

def test_topo_sort() -> None:
    network = init_from_dss(dss_file)
    # TODO: make sure that topo_sort fails on a network with a cycle
    # if any node is preceded by one of its children assert False
    sort = topo_sort(network)
    for idx,node in enumerate(sort):
        children = network.adj[node]
        for child in children:
            if sort.index(child) < idx:
                assert False

def test_network_topo() -> None:
    # check that the first node of topo sort is the source node in the dss file
    # check that opendss' assesment of cycles is the same as toposort
    # TODO: write me!
    pass
