# coding: utf-8
# -----------------------------------------------------------------------------
# Copyright (c) 2015 Tiago Baptista
# All rights reserved.
# -----------------------------------------------------------------------------

from __future__ import division

__docformat__ = 'restructuredtext'
__author__ = 'Tiago Baptista'


class Graph(object):
    """Base class for graphs. It is completely generic. A node can be any
    hashable Python type."""

    def __init__(self):
        self._graph = {}

    def add_node(self, node, connections):
        self._graph[node] = connections

    def get_connections(self, node):
        return self._graph.get(node, [])

    def clear(self):
        self._graph = {}

    def get_nodes(self):
        return self._graph.keys()

    def __len__(self):
        return len(self._graph)

    def __iter__(self):
        return self._graph.__iter__()
