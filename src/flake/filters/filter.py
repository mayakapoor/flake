import orjson
import os
import sys
import time

from . import config

class Filter():
    """
    Initialize the filter.
    """
    def __init__(self):
        EDGE_GRANULARITY = config.initFromConfig('EDGE_GRANULARITY')
        NODE_GRANULARITY = config.initFromConfig('NODE_GRANULARITY')

        if EDGE_GRANULARITY is None or EDGE_GRANULARITY != 'fine':
            EDGE_GRANULARITY = 'coarse'
        if NODE_GRANULARITY is None or NODE_GRANULARITY != 'fine':
            NODE_GRANULARITY = 'coarse'

        self.node_granularity = NODE_GRANULARITY
        self.edge_granularity = EDGE_GRANULARITY

    def load_data(self, data, G):
        raise NotImplementedError()

    def load_data_from_file(self, data, G):
        raise NotImplementedError()
