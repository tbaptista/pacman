# coding: utf-8
#-----------------------------------------------------------------------------
# Copyright (c) 2015 Tiago Baptista
# All rights reserved.
#-----------------------------------------------------------------------------

"""
Path-finding exercise using the pac-man game.

"""

from __future__ import division

__docformat__ = 'restructuredtext'
__author__ = 'Tiago Baptista'
__version__ = '1.0b1'

import pacman
import pyafai
from pyglet.window import mouse


class SearchAgent(pacman.PacmanAgent):
    def __init__(self, x, y):
        super(SearchAgent, self).__init__(x, y)

        self._target = None
        self._path = []

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

        # invalidate existing path, if any
        if value is not None and self._path:
            self._path = []

    def _think(self, delta):

        pass



class SearchDisplay(pacman.PacmanDisplay):
    def on_mouse_release(self, x, y, button, modifiers):
        super(SearchDisplay, self).on_mouse_release(x, y, button, modifiers)

        if button == mouse.LEFT:
            x1, y1 = self.world.get_cell(x, y)
            # send agent to x1, y1
            if isinstance(self.world.player, SearchAgent):
                self.world.player.target = (x1, y1)

        elif button == mouse.RIGHT:
            x1, y1 = self.world.get_cell(x, y)
            print("Cell: ({}, {})".format(x1, y1))
            print("Valid neighbours:", self.world.graph.get_connections((x1, y1)))


def setup():
    world = pacman.PacmanWorld(20, 'levels/maze.txt')
    display = SearchDisplay(world)

    # create pacman agent
    world.spawn_player(SearchAgent)


if __name__ == '__main__':
    setup()
    pyafai.run()