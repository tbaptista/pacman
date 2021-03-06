# coding: utf-8
# -----------------------------------------------------------------------------
# Copyright (c) 2015 Tiago Baptista
# All rights reserved.
# -----------------------------------------------------------------------------

"""
Neural Network Agents for the pac-man game.

"""

from __future__ import division

__docformat__ = 'restructuredtext'
__author__ = 'Tiago Baptista'
__version__ = '1.0'


import pacman
import pyafai
import random
import math


class NNLayer():
    def __init__(self, n_neurons, n_inputs):

        self._weights = []
        for i in range(n_neurons):
            self._weights.append([])
            for j in range(n_inputs + 1):
                self._weights[i].append(random.uniform(-1, 1))

        self._nin = n_inputs
        self._nout = n_neurons

    def sigmoid(self, x):
        return 1 / (1 + math.e ** -x)

    def feed_forward(self, inputs):
        inputs = inputs[:]
        inputs.append(1)
        outputs = []
        for neuron in range(len(self._weights)):
            x = 0
            for i in range(len(self._weights[neuron])):
                x += self._weights[neuron][i] * inputs[i]

            y = self.sigmoid(x)
            outputs.append(y)

        return outputs


class NNFeedForward():
    def __init__(self, n_in, n_hidden, n_out):
        self._hidden = NNLayer(n_hidden, n_in)
        self._out = NNLayer(n_out, n_hidden)

        self._hidden_outputs = []

    def feed_forward(self, inputs):
        self._hidden_outputs = self._hidden.feed_forward(inputs)
        outputs = self._out.feed_forward(self._hidden_outputs)

        return outputs

    def train(self, data, rate):
        # TODO
        pass

class NNPacman(pacman.PacmanAgent):
    def __init__(self, x, y, cell):
        super(NNPacman, self).__init__(x, y, cell)

        # Create perceptions
        # Note that perceptions are stored in a dictionary. As such, order is not preserved.
        self.add_perception(DirectionPerception((0, 1)))
        self.add_perception(DirectionPerception((0, -1)))
        self.add_perception(DirectionPerception((1, 0)))
        self.add_perception(DirectionPerception((-1, 0)))
        self.add_perception(WallPerception((0, 1)))
        self.add_perception(WallPerception((0, -1)))
        self.add_perception(WallPerception((1, 0)))
        self.add_perception(WallPerception((-1, 0)))
        self.add_perception(FoodPerception((0, 1)))
        self.add_perception(FoodPerception((0, -1)))
        self.add_perception(FoodPerception((1, 0)))
        self.add_perception(FoodPerception((-1, 0)))
        self.add_perception(GhostPerception())
        self.add_perception(RandomPerception())

        # Create Neural Network controller.
        # Connect perceptions to input layer, and actions to output layer.
        self._nn = NNFeedForward(14, 14, 2)
        self._inputs =[self._perceptions['wall_up'],
                       self._perceptions['wall_down'],
                       self._perceptions['wall_left'],
                       self._perceptions['wall_right'],
                       self._perceptions['going_up'],
                       self._perceptions['going_down'],
                       self._perceptions['going_left'],
                       self._perceptions['going_right'],
                       self._perceptions['food_up'],
                       self._perceptions['food_down'],
                       self._perceptions['food_left'],
                       self._perceptions['food_right'],
                       self._perceptions['ghost'],
                       self._perceptions['random']]
        self._action_dict = {(0, 0): 'up', (0, 1): 'down',
                             (1, 0): 'left', (1, 1):'right'}
        self._rev_action_dict = dict([(v, k) for k, v in self._action_dict.items()])

    def _think(self, delta):
        # If the previous action has finished
        if self.body.target is None:
            # Activate Feed Forward NN to choose action
            inputs = [p.value for p in self._inputs]
            x, y = [round(o) for o in self._nn.feed_forward(inputs)]
            action = self._action_dict[(x, y)]
            return [self._actions[action]]

    def train(self, filename, rate=0.2, epochs=100):
        data = []

        # Read and parse data file
        with open(filename, 'r') as f:
            header = f.readline().strip().split(',')
            for line in f:
                line = line.strip().split(',')
                line[:-1] = [int(x) for x in line[:-1]]
                data.append([])

                for p in self._inputs:
                    data[-1].append(line[header.index(p.name)])

                data[-1].extend(self._rev_action_dict[line[-1]])

        # Train network
        for i in range(epochs):
            self._nn.train(data, rate)



class DirectionPerception(pyafai.Perception):
    def __init__(self, direction):
        super(DirectionPerception, self).__init__(int, 'going_' + pacman.GameAction.DIR_TO_ACTION[direction])
        self._dir = direction

    def update(self, agent):
        if self._dir == agent.body.direction:
            self.value = 1
        else:
            self.value = 0


class WallPerception(pyafai.Perception):
    def __init__(self, direction):
        super(WallPerception, self).__init__(int, 'wall_' + pacman.GameAction.DIR_TO_ACTION[direction])
        self._dir = direction

    def update(self, agent):
        if agent.world.has_wall_at(agent.body.cell_x + self._dir[0],
                                   agent.body.cell_y + self._dir[1]):
            self.value = 1
        else:
            self.value = 0


class FoodPerception(pyafai.Perception):
    def __init__(self, direction):
        super(FoodPerception, self).__init__(int, 'food_' + pacman.GameAction.DIR_TO_ACTION[direction])
        self._dir = direction

    def update(self, agent):
        if agent.world.has_food_at(agent.body.cell_x + self._dir[0],
                                   agent.body.cell_y + self._dir[1]):
            self.value = 1
        else:
            self.value = 0


class GhostPerception(pyafai.Perception):
    NHOOD = {(0, 1): [(0, 1), (-1, 1), (1, 1), (0, 2)],
             (0, -1): [(0, -1), (-1, -1), (1, -1), (0, -2)],
             (1, 0): [(1, 0), (1, 1), (1, -1), (2, 0)],
             (-1, 0): [(-1, 0), (-1, 1), (-1, -1), (-2, 0)],
             (0, 0): []}

    def __init__(self):
        super(GhostPerception, self).__init__(int, 'ghost')

    def update(self, agent):
        x = agent.body.cell_x
        y = agent.body.cell_y
        nhood = GhostPerception.NHOOD[agent.body.direction]
        self.value = 0
        for d in nhood:
            if agent.world.has_object_type_at(x + d[0], y + d[1],
                                              pacman.GhostBody):
                self.value = 1
                break


class RandomPerception(pyafai.Perception):
    def __init__(self):
        super(RandomPerception, self).__init__(int, 'random')

    def update(self, agent):
        if random.random() > 0.5:
            self.value = 1
        else:
            self.value = 0


def setup():
    world = pacman.PacmanWorld(20, 'levels/medium.txt')

    # Create pac-man agent
    world.spawn_player(NNPacman)
    world.player_lives = 1

    # Train network
    world.player.train('pacman.sav', 0.2, 100)

    # Create ghosts
    world.spawn_ghost(pacman.RandomGhost)

    # Create display
    pacman.PacmanDisplay(world)

def record_pacman_keyboard():
    world = pacman.PacmanWorld(20, 'levels/medium.txt')
    pacman.PacmanDisplay(world)

    # Create pac-man agent
    world.spawn_player(pacman.KeyboardAgent)

    # Add perceptions
    world.player.add_perception(DirectionPerception((0, 1)))
    world.player.add_perception(DirectionPerception((0, -1)))
    world.player.add_perception(DirectionPerception((1, 0)))
    world.player.add_perception(DirectionPerception((-1, 0)))
    world.player.add_perception(WallPerception((0, 1)))
    world.player.add_perception(WallPerception((0, -1)))
    world.player.add_perception(WallPerception((1, 0)))
    world.player.add_perception(WallPerception((-1, 0)))
    world.player.add_perception(FoodPerception((0, 1)))
    world.player.add_perception(FoodPerception((0, -1)))
    world.player.add_perception(FoodPerception((1, 0)))
    world.player.add_perception(FoodPerception((-1, 0)))
    world.player.add_perception(GhostPerception())
    world.player.add_perception(RandomPerception())
    world.player_lives = 1
    world.player.start_recording()

    # Create ghosts
    world.spawn_ghost(pacman.RandomGhost)

    pyafai.run()

    world.player.stop_recording()
    world.player.save_recording('pacman.sav')


if __name__ == '__main__':
    setup()
    pyafai.run()

    # Test Feed Forward using XOR
    #nn = NNFeedForward(2, 2, 1)
    #print(nn.feed_forward([0, 0]))

    #record_pacman_keyboard()