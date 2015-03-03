#coding: utf-8
#-----------------------------------------------------------------------------
# Copyright (c) 2015 Tiago Baptista
# All rights reserved.
#-----------------------------------------------------------------------------

from __future__ import division

__docformat__ = 'restructuredtext'
__author__ = 'Tiago Baptista'

import pyafai
from pyafai import shapes
import pyglet
from pyglet.window import key
from pyglet.window import mouse


class ColorConfig(object):
    WALL = ('c3B', (100, 100, 220))
    DOT = ('c3B', (200, 200, 200))
    PELLET = ('c3B', (200, 200, 100))
    PACMAN = ('c3B', (220, 220, 0))
    GHOST1 = ('c3B', (220, 0, 0))
    GHOST2 = ('c3B', (0, 220, 0))
    GHOST3 = ('c3B', (0, 100, 220))
    GHOST4 = ('c3B', (180, 180, 20))
    GHOSTS = [GHOST1, GHOST2, GHOST3, GHOST4]


class AgentBody(pyafai.Object):
    dir_to_angle = {(0, 1): 90,
                    (0, -1): 270,
                    (1, 0): 0,
                    (-1, 0): 180}

    def __init__(self, x, y):
        super(AgentBody, self).__init__(x, y)

        self.velocity = 5.0
        self._direction = (0, 0)
        self._velx = 0
        self._vely = 0

    def update(self, delta):
        if self.direction != (0, 0):
            self.x += self._velx * delta
            self.y += self._vely * delta

            if self._direction[0] == 1 and abs(self.x - self.cell_x) < 0.1:
                if self.agent.world.has_object_type_at(self.cell_x + 1, self.cell_y, Wall):
                    self.direction = (0, 0)
            elif self._direction[0] == -1 and abs(self.x - self.cell_x) < 0.1:
                if self.agent.world.has_object_type_at(self.cell_x - 1, self.cell_y, Wall):
                    self.direction = (0, 0)
            elif self._direction[1] == 1 and abs(self.y - self.cell_y) < 0.1:
                if self.agent.world.has_object_type_at(self.cell_x, self.cell_y + 1, Wall):
                    self.direction = (0, 0)
            elif self._direction[1] == -1 and abs(self.y - self.cell_y) < 0.1:
                if self.agent.world.has_object_type_at(self.cell_x, self.cell_y - 1, Wall):
                    self.direction = (0, 0)

    @property
    def cell(self):
        return int(round(self.x)), int(round(self.y))

    @property
    def cell_x(self):
        return int(round(self.x))

    @property
    def cell_y(self):
        return int(round(self.y))

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, direction):
        if abs(self._direction[0]) == 1 and abs(direction[0]) != 1:
            self.x = self.cell_x
        elif abs(self._direction[1]) == 1 and abs(direction[1]) != 1:
            self.y = self.cell_y

        self._direction = direction
        if direction != (0, 0):
            self._velx = direction[0] * self.velocity
            self._vely = direction[1] * self.velocity
        else:
            self._velx = 0
            self._vely = 0


class PacmanBody(AgentBody):
    def __init__(self, x, y):
        super(PacmanBody, self).__init__(x, y)

        shape = shapes.Circle(12.5, color=ColorConfig.PACMAN)
        self.add_shape(shape)

    @property
    def direction(self):
        return self._direction

    @AgentBody.direction.setter
    def direction(self, direction):
        AgentBody.direction.fset(self, direction)
        if direction != (0, 0):
            self.angle = self.dir_to_angle[direction]

class GhostBody(AgentBody):
    def __init__(self, x, y, color=ColorConfig.GHOST1):
        super(GhostBody, self).__init__(x, y)

        shape = shapes.Rect(20, 30, color=color)
        self.add_shape(shape)


class GameAction(pyafai.Action):
    def __init__(self, name):
        super(GameAction, self).__init__(name)
        self.direction = (0, 0)

    def execute(self, agent):
        x = agent.body.cell_x + self.direction[0]
        y = agent.body.cell_y + self.direction[1]
        if agent.world.is_valid_action(agent, self):
            agent.body.direction = self.direction

    def execution_result(self, agent):
        return (agent.body.cell_x + self.direction[0],
                agent.body.cell_y + self.direction[1])



class UpAction(GameAction):
    def __init__(self):
        super(UpAction, self).__init__('up')
        self.direction = (0, 1)


class DownAction(GameAction):
    def __init__(self):
        super(DownAction, self).__init__('down')
        self.direction = (0, -1)


class LeftAction(GameAction):
    def __init__(self):
        super(LeftAction, self).__init__('left')
        self.direction = (-1, 0)


class RightAction(GameAction):
    def __init__(self):
        super(RightAction, self).__init__('right')
        self.direction = (1, 0)


class PacmanAgent(pyafai.Agent):
    def __init__(self, x, y):
        super(PacmanAgent, self).__init__()
        self.score = 0

        self.body = PacmanBody(x, y)

        self.add_action(UpAction())
        self.add_action(DownAction())
        self.add_action(LeftAction())
        self.add_action(RightAction())

    def update(self, delta):
        super(PacmanAgent, self).update(delta)

        x, y = self.body.cell
        if self.world.has_food_at(x, y):
            obj = self.world.eat_food_at(x, y)
            self.score += obj.value

    def _think(self, delta):
        pass


class GhostAgent(pyafai.Agent):
    def __init__(self, x, y, color=ColorConfig.GHOST1):
        super(GhostAgent, self).__init__()
        self.body = GhostBody(x, y, color)

        self.add_action(UpAction())
        self.add_action(DownAction())
        self.add_action(LeftAction())
        self.add_action(RightAction())

    def _think(self, delta):
        pass


class KeyboardAgent(PacmanAgent):
    def __init__(self, x, y):
        super(KeyboardAgent, self).__init__(x, y)
        self._next_action = None
        self._timeout = 0.3
        self._timer = 0

    @property
    def next_action(self):
        return self._next_action

    @next_action.setter
    def next_action(self, action_name):
        if action_name is not None:
            self._next_action = self._actions[action_name]
            self._timer = self._timeout
        else:
            self._next_action = None

    def _think(self, delta):
        self._timer -= delta
        if self._timer < 0:
            self.next_action = None
            self._timer = 0

        if self.next_action is not None:
            if self.world.is_valid_action(self, self.next_action):
                res = [self.next_action]
                self.next_action = None
                return res

        return []


class Wall(pyafai.Object):
    def __init__(self, x, y, cell_size, batch):
        super(Wall, self).__init__(x, y)

        self._batch = batch
        half = cell_size / 2
        shape = shapes.Rect(half, half, x * cell_size + half, y * cell_size + half,
                            color=ColorConfig.WALL)
        self.add_shape(shape)

    def draw(self):
        pass


class Food(pyafai.Object):
    def __init__(self, x, y):
        super(Food, self).__init__(x, y)

        self.value = 0

    def draw(self):
        pass


class Dot(Food):
    def __init__(self, x, y, cell_size, batch):
        super(Dot, self).__init__(x, y)

        self.value = 10

        half = cell_size / 2
        shape = shapes.Circle(half / 4, x * cell_size + half, y * cell_size + half,
                            color=ColorConfig.DOT)
        shape.add_to_batch(batch)
        self._shapes.append(shape)


class Pellet(Food):
    def __init__(self, x, y, cell_size, batch):
        super(Pellet, self).__init__(x, y)

        self.value = 50

        half = cell_size / 2
        shape = shapes.Circle(half / 1.5, x * cell_size + half, y * cell_size + half,
                            color=ColorConfig.PELLET)
        shape.add_to_batch(batch)
        self._shapes.append(shape)


class PacmanWorld(pyafai.World2DGrid):
    def __init__(self, cell_size, level_filename):
        self._ghost_start = None
        self._player_start = None
        self.player = None
        self._food_count = 0
        self.game_over = False

        #load level
        grid = self._load_level(level_filename)
        width = len(grid[0])
        height = len(grid)

        #call superclass constructor
        super(PacmanWorld, self).__init__(width, height, cell_size,
                                          tor=True, grid=False)

        #create objects from level data
        for y in range(len(grid)):
            for x in range(len(grid[y])):
                if grid[y][x] == 'X':
                    wall = Wall(x, y, cell_size, self._batch)
                    self.add_object(wall)

                elif grid[y][x] == '.':
                    dot = Dot(x, y, cell_size, self._batch)
                    self.add_object(dot)
                    self._food_count += 1

                elif grid[y][x] == 'O':
                    pellet = Pellet(x, y, cell_size, self._batch)
                    self.add_object(pellet)
                    self._food_count += 1

                elif grid[y][x] == 'P':
                    self._player_start = (x, y)

                elif grid[y][x] == 'G':
                    self._ghost_start = (x, y)


    def _load_level(self, filename):
        grid = []
        with open(filename, 'r', encoding='utf8') as f:
            grid = [list(line.strip('\n')) for line in f.readlines()]
            grid.reverse()

        return grid

    @property
    def score(self):
        if self.player is not None:
            return self.player.score
        else:
            return 0

    def spawn_player(self, player_class):
        self.player = player_class(self._player_start[0], self._player_start[1])
        self.add_agent(self.player)

    def spawn_ghost(self, ghost_class):
        ghost = ghost_class(self._ghost_start[0], self._ghost_start[1])
        self.add_agent(ghost)

    def is_valid_action(self, agent, action):
        new_x = agent.body.cell_x + action.direction[0]
        new_y = agent.body.cell_y + action.direction[1]
        if self.has_object_type_at(new_x, new_y, Wall):
            return False
        else:
            if abs(agent.body.direction[0]) == 1 and abs(action.direction[0]) != 1 and \
                abs(agent.body.cell_x - agent.body.x) > 0.1:
                return False
            elif abs(agent.body.direction[1]) == 1 and abs(action.direction[1]) != 1 and \
                    abs(agent.body.cell_y - agent.body.y) > 0.1:
                return False
            else:
                return True

    def has_food_at(self, x, y):
        return self.has_object_type_at(x, y, Food)

    def eat_food_at(self, x, y):
        list = self.get_cell_contents(x, y)
        for obj in list:
            if isinstance(obj, Food):
                self.remove_object(obj)
                self._food_count -= 1
                return obj

    def update(self, delta):
        if not self.game_over:
            super(PacmanWorld, self).update(delta)

            if self._food_count == 0:
                self.game_over = True


class PacmanDisplay(pyafai.Display):
    def __init__(self, *args, **kwargs):
        super(PacmanDisplay, self).__init__(*args, **kwargs)
        self._game_over_label = pyglet.text.Label('Game Over',
                        font_name='Arial',
                        font_size=80,
                        x=self.width//2, y=self.height//2,
                        anchor_x='center', anchor_y='center')

    def on_draw(self):
        super(PacmanDisplay, self).on_draw()

        if self.world.game_over:
            self._game_over_label.draw()

    def on_key_press(self, symbol, modifiers):
        super(PacmanDisplay, self).on_key_press(symbol, modifiers)

        if isinstance(self.world.player, KeyboardAgent):
            if symbol == key.W or symbol == key.MOTION_UP: #Up
                self.world.player.next_action = 'up'

            elif symbol == key.S or symbol == key.MOTION_DOWN: #Down
                self.world.player.next_action = 'down'

            elif symbol == key.A or symbol == key.MOTION_LEFT: #Left
                self.world.player.next_action = 'left'

            elif symbol == key.D or symbol == key.MOTION_RIGHT: #Right
                self.world.player.next_action = 'right'

    def on_mouse_release(self, x, y, button, modifiers):
        super(PacmanDisplay, self).on_mouse_release(x, y, button, modifiers)

        if button == mouse.LEFT:
            x1, y1 = self.world.get_cell(x, y)
            print(self.world.get_cell_contents(x1, y1))


def main():
    world = PacmanWorld(20, 'levels/pacman.txt')
    world.spawn_player(KeyboardAgent)
    display = PacmanDisplay(world)

    pyafai.run()


if __name__ == '__main__':
    main()