# coding: utf-8
# -----------------------------------------------------------------------------
# Copyright (c) 2015 Tiago Baptista
# All rights reserved.
# -----------------------------------------------------------------------------

"""
Path-finding exercise using the pac-man game. Ghosts follow the player.

"""

from __future__ import division

__docformat__ = 'restructuredtext'
__author__ = 'Tiago Baptista'
__version__ = '1.0'

import pacman
import pyafai
import graph


class GhostGraph(graph.Graph):
    def __init__(self, base_graph: graph.Graph):
        super(GhostGraph, self).__init__()
        self._graph = base_graph._graph

    def get_connections(self, node):
        coord = node[:2]
        reverse = pacman.GameAction.REVERSE[node[2]]
        res = []
        for conn in self._graph.get(coord, []):
            if conn[2] != reverse:
                res.append(conn)

        return res


class SearchGhost(pacman.GhostAgent):
    def __init__(self, x, y, cell):
        super(SearchGhost, self).__init__(x, y, cell)

        self._target = None
        self._path = []

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

        # We are changing destination, so invalidate current path
        if value is not None and self._path:
            self._path = []

    def _think(self, delta):
        # If the previous action has finished
        if self.body.target is None:
            # Set new target and generate path
            # TODO

            # If we have a non empty path
            if self._path:
                # Execute the next action on the path
                # Note that the path is expected to be a list of action names
                next_action = self._path.pop(0)
                return [self._actions[next_action]]


def setup():
    world = pacman.PacmanWorld(20, 'levels/pacman.txt')
    display = pacman.PacmanDisplay(world)
    world.graph = GhostGraph(world.graph)

    # Create pac-man agent
    world.spawn_player(pacman.KeyboardAgent)
    world.player_lives = 3

    # Create ghosts
    world.spawn_ghost(SearchGhost)


if __name__ == '__main__':
    setup()
    pyafai.run()