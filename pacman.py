# coding: utf-8
# -----------------------------------------------------------------------------
# Copyright (c) 2015 Tiago Baptista
# All rights reserved.
# -----------------------------------------------------------------------------

from __future__ import division
from io import open
import pyafai
from pyafai import shapes
import pyglet
from pyglet.window import key
import graph
import random

__docformat__ = 'restructuredtext'
__author__ = 'Tiago Baptista'
__version__ = '1.0b4'


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
    GHOST_SCARED = ('c3B', (0, 0, 200))
    GHOST_SCARED_FLASH = ('c3B', (200, 200, 200))

    @staticmethod
    def random_ghost_color():
        return random.choice(ColorConfig.GHOSTS)


class AgentBody(pyafai.Object):
    dir_to_angle = {(0, 1): 90,
                    (0, -1): 270,
                    (1, 0): 0,
                    (-1, 0): 180}

    VELOCITY = 5.0

    def __init__(self, x, y):
        super(AgentBody, self).__init__(x, y)

        self.velocity = AgentBody.VELOCITY
        self._direction = (0, 0)
        self._target = None
        self._velx = 0
        self._vely = 0
        self._excess = [0, 0]
        self.animate = True

    @property
    def target(self):
        return self._target

    def update(self, delta):
        if self.animate:
            if self._target is not None:
                if self._excess[0] != 0:
                    self.x += self._excess[0]
                    self._excess[0] = 0
                elif self._excess[1] != 0:
                    self.y += self._excess[1]
                    self._excess[1] = 0

                self.x += self._velx * delta
                self.y += self._vely * delta

                w = self.agent.world.grid_width
                h = self.agent.world.grid_height

                if self._direction[0] > 0:
                    if self.x > w - 0.5:
                        self._target = (self._target[0] % w, self._target[1])

                    elif self._target[0] - self.x <= 0:
                        self._excess[0] = self.x - self._target[0]
                        self.x = self._target[0]
                        self._target = None

                elif self._direction[0] < 0:
                    if self.x < -0.5:
                        self._target = (self._target[0] % w, self._target[1])

                    elif self.x - self._target[0] <= 0:
                        self._excess[0] = self.x - self._target[0]
                        self.x = self._target[0]
                        self._target = None

                elif self._direction[1] > 0:
                    if self.y > h - 0.5:
                        self._target = (self._target[0], self._target[1] % h)

                    elif self._target[1] - self.y <= 0:
                        self._excess[1] = self.y - self._target[1]
                        self.y = self._target[1]
                        self._target = None

                elif self._direction[1] < 0:
                    if self.y < -0.5:
                        self._target = (self._target[0], self._target[1] % h)

                    elif self.y - self._target[1] <= 0:
                        self._excess[1] = self.y - self._target[1]
                        self.y = self._target[1]
                        self._target = None

        elif self._target is not None:
            self.x = self._target[0]
            self.y = self._target[1]
            self._target = None

    @property
    def cell(self):
        return round(self.x), round(self.y)

    @property
    def cell_x(self):
        return round(self.x)

    @property
    def cell_y(self):
        return round(self.y)

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, direction):
        if self._target is None:
            if self._direction != direction:
                self._excess = [0, 0]

            self._direction = direction
            self._target = (self.cell_x + direction[0],
                            self.cell_y + direction[1])
            if direction != (0, 0):
                self._velx = direction[0] * self.velocity
                self._vely = direction[1] * self.velocity
            else:
                self._velx = 0
                self._vely = 0


class PacmanBody(AgentBody):
    def __init__(self, x, y, cell):
        super(PacmanBody, self).__init__(x, y)

        shape = shapes.Circle(int(cell * 0.6), color=ColorConfig.PACMAN)
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
    def __init__(self, x, y, cell, color=ColorConfig.GHOST1):
        super(GhostBody, self).__init__(x, y)
        self._normal_velocity = AgentBody.VELOCITY * 1.0
        self._scared_velocity = AgentBody.VELOCITY * 0.5
        self._color = color
        self._scared = False
        self.velocity = self._normal_velocity

        shape = shapes.Rect(cell * 1.25, cell * 1.25, color=color)
        self.add_shape(shape)

    @property
    def scared(self):
        return self._scared

    @scared.setter
    def scared(self, value):
        if value != self._scared:
            self._scared = value
            if value:
                self._shapes[0].color = ColorConfig.GHOST_SCARED
                self.velocity = self._scared_velocity
            else:
                self._shapes[0].color = self._color
                self.velocity = self._normal_velocity


class GameAction(pyafai.Action):
    DIR_TO_ACTION = {(0, 1): 'up', (0, -1): 'down',
                     (-1, 0): 'left', (1, 0): 'right',
                     (0, 0): 'stop'}
    direction = (0, 0)

    REVERSE = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left',
               'stop': 'stop'}

    def execute(self, agent):
        if agent.world.is_valid_action(agent, self):
            agent.body.direction = self.direction

    def execution_result(self, agent):
        return (agent.body.cell_x + self.direction[0],
                agent.body.cell_y + self.direction[1])


class UpAction(GameAction):
    direction = (0, 1)
    name = 'up'

    def __init__(self):
        super(UpAction, self).__init__(UpAction.name)


class DownAction(GameAction):
    direction = (0, -1)
    name = 'down'

    def __init__(self):
        super(DownAction, self).__init__(DownAction.name)


class LeftAction(GameAction):
    direction = (-1, 0)
    name = 'left'

    def __init__(self):
        super(LeftAction, self).__init__(LeftAction.name)


class RightAction(GameAction):
    direction = (1, 0)
    name = 'right'

    def __init__(self):
        super(RightAction, self).__init__(RightAction.name)


class PacmanAgent(pyafai.Agent):
    def __init__(self, x, y, cell):
        super(PacmanAgent, self).__init__()
        self.score = 0
        self._history = []
        self._header = []
        self._recording = False

        self.body = PacmanBody(x, y, cell)

        self.add_action(UpAction())
        self.add_action(DownAction())
        self.add_action(LeftAction())
        self.add_action(RightAction())

    @property
    def last_action(self):
        return GameAction.DIR_TO_ACTION[self.body.direction]

    def eat_food(self):
        x, y = self.body.cell
        if self.world.has_food_at(x, y):
            obj = self.world.eat_food_at(x, y)
            self.score += obj.value

    def eat_ghosts(self):
        x, y = self.body.cell
        l = self.world.get_cell_contents(x, y)
        if l:
            for obj in l:
                if obj.is_body:
                    ag = obj.agent
                    if isinstance(ag, GhostAgent) and ag.scared:
                        self.world.kill_ghost(ag)

    def update(self, delta):
        self.eat_ghosts()

        if self.body.target is None:
            flag = True
        else:
            flag = False

        super(PacmanAgent, self).update(delta)

        if self._recording and flag:
            self._history.append([])
            self._history[-1].extend([p.value for p in self._perceptions.values()])
            self._history[-1].append(self.last_action)

        self.eat_food()
        self.eat_ghosts()

    def start_recording(self):
        self._header = [p.name for p in self._perceptions.values()] + ['action']
        self._recording = True

    def stop_recording(self):
        self._recording = False

    def save_recording(self, filename):
        with open(filename, 'w') as f:
            f.write(','.join(self._header) + '\n')
            f.writelines([','.join([str(v) for v in line]) + '\n' for line in self._history])

    def _think(self, delta):
        pass


class GhostAgent(pyafai.Agent):
    GHOST_SCARE_TIMEOUT = 6

    def __init__(self, x, y, cell, color=ColorConfig.GHOST1):
        super(GhostAgent, self).__init__()
        self.body = GhostBody(x, y, cell, color)

        self._scared = False
        self._scared_timer = 0

        self.add_action(UpAction())
        self.add_action(DownAction())
        self.add_action(LeftAction())
        self.add_action(RightAction())

    @property
    def scared(self):
        return self._scared

    @scared.setter
    def scared(self, value):
        self._scared = value
        self.body.scared = value
        if value:
            self._scared_timer = self.GHOST_SCARE_TIMEOUT
        else:
            self._scared_timer = 0

    @property
    def last_action(self):
        return GameAction.DIR_TO_ACTION[self.body.direction]

    def eat_player(self):
        if not self.world.player.is_dead:
            if self.body.cell == self.world.player.body.cell:
                self.world.kill_player()

    def update(self, delta):
        super(GhostAgent, self).update(delta)

        if self._scared:
            self._scared_timer -= delta
            if self._scared_timer <= 0:
                self.scared = False
        else:
            self.eat_player()

    def _think(self, delta):
        pass


class RandomGhost(GhostAgent):
    def __init__(self, x, y, cell, color=ColorConfig.GHOST1):
        super(RandomGhost, self).__init__(x, y, cell, color)

        self._last_action = None

    def _think(self, delta):
        if self.body.target is None:
            valid_actions = self.world.get_valid_actions(self)
            if valid_actions:
                action = random.choice(valid_actions)
                self._last_action = action
                return [self._actions[action]]


class KeyboardAgent(PacmanAgent):
    def __init__(self, x, y, cell):
        super(KeyboardAgent, self).__init__(x, y, cell)

        self.keys = None
        self._action = None

    @property
    def next_action(self):
        if self.keys[key.MOTION_UP] or self.keys[key.W]:
            return 'up'
        elif self.keys[key.MOTION_LEFT] or self.keys[key.A]:
            return 'left'
        elif self.keys[key.MOTION_DOWN] or self.keys[key.S]:
            return 'down'
        elif self.keys[key.MOTION_RIGHT] or self.keys[key.D]:
            return 'right'

        return None

    def _think(self, delta):
        # Only execute new action when the previous is finished
        if self.body.target is None:
            next_action = self.next_action
            if next_action is not None:
                next_action = self._actions[next_action]
                if self.world.is_valid_action(self, next_action):
                    res = [next_action]
                    self._action = next_action
                    return res

            if self._action is not None:
                if self.world.is_valid_action(self, self._action):
                    return [self._action]
                else:
                    self._action = None

        return []


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
        shape = shapes.Rect(int(cell_size / 5), int(cell_size / 5), x * cell_size + half,
                            y * cell_size + half,
                            color=ColorConfig.DOT)
        shape.add_to_batch(batch)
        self._shapes.append(shape)


class Pellet(Food):
    def __init__(self, x, y, cell_size, batch):
        super(Pellet, self).__init__(x, y)

        self.value = 50

        half = cell_size / 2
        shape = shapes.Circle(half / 1.5, x * cell_size + half,
                              y * cell_size + half,
                              color=ColorConfig.PELLET)
        shape.add_to_batch(batch)
        self._shapes.append(shape)


class PacmanWorld(pyafai.World2DGrid):
    GAME_ACTIONS = [UpAction, DownAction, LeftAction, RightAction]
    NAME_TO_ACTION = dict([(a.name, a) for a in GAME_ACTIONS])

    def __init__(self, cell_size, level_filename):
        self.player = None
        self.game_over = False
        self.player_win = False
        self.player_lives = 1
        self.graph = graph.Graph()
        self.show_graph = False
        self.keys = None    # key state dictionary
        self._ghost_start = []
        self._player_start = None
        self._food_count = 0
        self._valid_actions = None  # speedup for valid actions
        self._walls = None  # speedup for detection of walls
        self._graph_display = None
        self._animate = True

        # load level
        grid = self._load_level(level_filename)
        width = len(grid[0])
        height = len(grid)

        # call superclass constructor
        super(PacmanWorld, self).__init__(width, height, cell_size,
                                          tor=True, grid=False,
                                          nhood=pyafai.World2DGrid.von_neumann)

        self.paused = False

        # create objects from level data
        self._walls = [[False for x in range(self.width)] for y in
                       range(self.height)]
        for y in range(len(grid)):
            self._walls.append([])
            for x in range(len(grid[y])):
                if grid[y][x] == 'X':
                    half = cell_size / 2
                    shape = shapes.Rect(half, half, x * cell_size + half,
                            y * cell_size + half,
                            color=ColorConfig.WALL)
                    shape.add_to_batch(self._batch)
                    self._shapes.append(shape)
                    self._walls[y][x] = True

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
                    self._ghost_start.append((x, y))

        # generate static valid action map
        self._generate_valid_actions()

        # generate graph
        self._generate_graph()

        # generate graph display
        self._graph_display = GraphDisplay(self.graph, self)

    def _load_level(self, filename):
        grid = []
        with open(filename, 'r', encoding='utf8') as f:
            grid = [list(line.strip('\n')) for line in f.readlines()]
            grid.reverse()

        return grid

    def _generate_valid_actions(self):
        self._valid_actions = []
        for y in range(self.height):
            self._valid_actions.append([])
            for x in range(self.width):
                self._valid_actions[y].append([])
                if not self.has_wall_at(x, y):
                    for action in PacmanWorld.GAME_ACTIONS:
                        if not self.has_wall_at(x + action.direction[0],
                                                y + action.direction[1]):
                            self._valid_actions[y][x].append(action.name)

    def _generate_graph(self):
        self.graph.clear()
        for x in range(self._width):
            for y in range(self._height):
                # verify if current cell is a wall
                is_wall = self.has_wall_at(x, y)

                # if it is not a wall, calculate connections and weights
                if not is_wall:
                    connections = []
                    for action_name in self._valid_actions[y][x]:
                        action = PacmanWorld.NAME_TO_ACTION[action_name]
                        x1 = x + action.direction[0]
                        y1 = y + action.direction[1]
                        if self._tor:
                            x1 = x1 % self._width
                            y1 = y1 % self._height
                        weight = 1
                        connections.append(((x1, y1), weight, action_name))

                    self.graph.add_node((x, y), connections)

    def get_neighbourhood(self, x, y):
        result = []
        x = round(x)
        y = round(y)
        for dx, dy in self._nhood:
            x1 = x + dx
            y1 = y + dy
            if not self._tor and 0 <= x1 < self._width and 0 <= y1 < self._height:
                result.append((x1, y1))
            elif self._tor:
                x1 = x1 % self._width
                y1 = y1 % self._height
                result.append((x1, y1))

        return result

    @property
    def score(self):
        if self.player is not None:
            return self.player.score
        else:
            return 0

    @property
    def animate(self):
        return self._animate

    @animate.setter
    def animate(self, value):
        self._animate = value
        for agent in self._agents:
            agent.body.animate = value

    def draw(self):
        super(PacmanWorld, self).draw()

        if self.show_graph:
            self._graph_display.draw()

    def spawn_player(self, player_class, *args, **kwargs):
        if self.player is None or self.player.is_dead:
            self.player = player_class(self._player_start[0],
                                       self._player_start[1], self.cell,
                                       *args, **kwargs)
            if isinstance(self.player, KeyboardAgent):
                if self.keys is not None:
                    self.player.keys = self.keys
                else:
                    print("No key state dictionary has been set!")

            self.player.body.animate = self._animate

            self.add_agent(self.player)
        else:
            print("Only one player is allowed!")

    def spawn_ghost(self, ghost_class, *args, **kwargs):
        location = random.choice(self._ghost_start)
        ghost = ghost_class(location[0], location[1], self.cell,
                            *args, **kwargs)
        ghost.body.animate = self._animate
        self.add_agent(ghost)

    def is_valid_action(self, agent, action):
        if action.name in self.get_valid_actions(agent):
            return True
        else:
            return False

    def get_valid_actions(self, agent):
        # Only allow actions when the body is not executing a previous one
        if agent.body.target is not None:
            return []

        valid = self._valid_actions[agent.body.cell_y][agent.body.cell_x]
        if isinstance(agent, GhostAgent):
            direction = agent.body.direction
            if direction != (0, 0) and len(valid) > 1:
                reverse = (direction[0] * -1, direction[1] * -1)
                action = GameAction.DIR_TO_ACTION[reverse]
                if action in valid:
                    valid = valid[:]
                    valid.remove(action)

        return valid

    def has_food_at(self, x, y):
        return self.has_object_type_at(x, y, Food)

    def has_wall_at(self, x, y):
        if self._tor:
            x = round(x) % self._width
            y = round(y) % self._height

        return self._walls[round(y)][round(x)]

    def eat_food_at(self, x, y):
        l = self.get_cell_contents(x, y)
        for obj in l:
            if isinstance(obj, Food):
                self.remove_object(obj)
                self._food_count -= 1
                if isinstance(obj, Pellet):
                    self.scare_ghosts()
                return obj

    def scare_ghosts(self):
        for g in self._agents:
            if isinstance(g, GhostAgent):
                g.scared = True

    def kill_player(self):
        if self.player is not None:
            self.player.kill()
            self.player_lives -= 1

            if self.player_lives > 0:
                self.spawn_player(type(self.player))

    def kill_ghost(self, ghost):
        if ghost in self._agents:
            ghost.kill()
            self.spawn_ghost(type(ghost))

    def update(self, delta):
        if not self.game_over:
            super(PacmanWorld, self).update(delta)

            if self._food_count == 0:
                self.game_over = True
                self.player_win = True

            if self.player_lives == 0:
                self.game_over = True


class PacmanDisplay(pyafai.Display):
    def __init__(self, *args, **kwargs):
        super(PacmanDisplay, self).__init__(*args, **kwargs)
        self._game_over_label = pyglet.text.Label('Game Over',
                                                  font_name='Arial',
                                                  font_size=36,
                                                  x=self.width // 2,
                                                  y=self.height // 2,
                                                  anchor_x='center',
                                                  anchor_y='center')

        self._win_label = pyglet.text.Label('Win', font_name='Arial',
                                            font_size=36,
                                            x=self.width // 2,
                                            y=self.height // 2,
                                            anchor_x='center',
                                            anchor_y='center')

        keys = key.KeyStateHandler()
        self.push_handlers(keys)
        self.world.keys = keys


    def on_draw(self):
        super(PacmanDisplay, self).on_draw()

        if self.world.game_over:
            if self.world.player_win:
                self._win_label.draw()
            else:
                self._game_over_label.draw()

    def on_key_press(self, symbol, modifiers):
        super(PacmanDisplay, self).on_key_press(symbol, modifiers)

        if symbol == key.G:
            self.world.show_graph = not self.world.show_graph


class GraphDisplay(object):
    def __init__(self, graph, world):
        self._batch = pyglet.graphics.Batch()
        self._node_shapes = [[None] * world.grid_width for y in
                             range(world.grid_height)]
        self._conn_shapes = []

        cell = world.cell
        half_cell = world.cell / 2
        color = ('c4B', (150, 150, 150, 100))

        # create nodes
        for node in graph.get_nodes():
            x, y = node
            shape = shapes.Circle(4, cell * x + half_cell, cell * y + half_cell,
                                  color=color)
            shape.add_to_batch(self._batch)
            self._node_shapes[y][x] = shape

        # create connections
        for node in graph.get_nodes():
            x1, y1 = node
            for dest in graph.get_connections(node):
                x2, y2 = dest[0]
                shape = shapes.Line(cell * x1 + half_cell,
                                    cell * y1 + half_cell,
                                    cell * x2 + half_cell,
                                    cell * y2 + half_cell,
                                    color=color)
                shape.add_to_batch(self._batch)
                self._conn_shapes.append(shape)

    def draw(self):
        self._batch.draw()


def main():
    world = PacmanWorld(20, 'levels/pacman.txt')
    display = PacmanDisplay(world)
    world.spawn_player(KeyboardAgent)
    world.spawn_ghost(RandomGhost)
    world.player_lives = 3

    pyafai.run()


if __name__ == '__main__':
    main()
