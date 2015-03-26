# coding: utf-8
# -----------------------------------------------------------------------------
# Copyright (c) 2015 Tiago Baptista
# All rights reserved.
# -----------------------------------------------------------------------------

from __future__ import division

__docformat__ = 'restructuredtext'
__author__ = 'Tiago Baptista'


class Graph(object):
    """Base class for directed graphs. It is completely generic.
    A node can be any hashable Python type."""

    def __init__(self):
        self._graph = {}
        self._expanded_counter = 0
        self._visited_counter = 0

    def add_node(self, node, connections):
        self._graph[node] = connections

    def get_connections(self, node):
        res = self._graph.get(node, [])
        self._expanded_counter += len(res)
        self._visited_counter += 1
        return res

    def clear(self):
        self._graph = {}

    def get_nodes(self):
        return self._graph.keys()

    def reset_counter(self):
        self._expanded_counter = 0
        self._visited_counter = 0

    @property
    def expanded_counter(self):
        return self._expanded_counter

    @property
    def visited_counter(self):
        return self._visited_counter

    def __len__(self):
        return len(self._graph)

    def __iter__(self):
        return self._graph.__iter__()
