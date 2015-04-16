# coding: utf-8
# -----------------------------------------------------------------------------
# Copyright (c) 2015 Tiago Baptista
# All rights reserved.
# -----------------------------------------------------------------------------

"""
Knowledge-Based Agents for the pac-man game.

"""

from __future__ import division

__docformat__ = 'restructuredtext'
__author__ = 'Tiago Baptista, Alexandre Pinto'
__version__ = '1.0'


import pacman
import pyafai


class Literal(object):
    def __init__(self, lit_string =""):
        self._lit_string = lit_string

    def is_neg(self):
        return (self._lit_string[:4] == "not ")

    def get_atom(self):
        if self._lit_string[:4] == "not ":
            atom = self._lit_string[4:]
        else:
            atom = self._lit_string
        return atom

    def __str__(self):
        return self._lit_string

    def __repr__(self):
        return "Literal(" + self._lit_string + ")"


class Rule(object):
    def __init__(self, line):
        rule_components = line.split(":-")
        self.head = rule_components[0]
        self.head = self.head.strip(" .\n")
        self.body = ""
        if len(rule_components) > 1:
            self.body = rule_components[1]
            self.body = self.body.split(",")
            for i in range(len(self.body)):
                lit = self.body.pop(0)
                lit = lit.strip(" .\n")
                self.body.append(Literal(lit))
        else:
            self.body = []

    def is_fact(self):
        return len(self.body) == 0

    def verify(self, work_mem):
        for lit in self.body:
            if lit.is_neg():
                if lit.get_atom() in work_mem:
                    return False
            elif lit.get_atom() not in work_mem:
                return False

        return True

    def __str__(self):
        if self.is_fact():
            return self.head + "."
        else:
            return self.head + " :- " + ", ".join([str(lit) for lit in self.body]) + "."

    def __repr__(self):
        return "Rule(" + str(self) + ")"


class KB(object):
    def __init__(self, kbfile):
        self.rules = []
        self.facts = []
        with open(kbfile) as f:
            for line in f:
                if line != "\n":
                    new_rule = Rule(line)
                    if (new_rule.is_fact()):
                        self.facts.append(new_rule)
                    else:
                        self.rules.append(new_rule)

    def add_fact(self, fact):
        rule = Rule(fact + '.')
        self.facts.append(rule)

    def remove_fact(self, fact):
        for f in self.facts:
            if f.head == fact:
                self.facts.remove(f)

    def infer(self, perceptions):
        # TODO
        pass

    def is_action(self, string):
        if "(" in string:
            return True
        else:
            return False

    def __str__(self):
        res = "Facts:\n"
        res += '\n'.join([str(fact) for fact in self.facts])
        res += "\n\nRules:\n"
        res += '\n'.join([str(rule) for rule in self.rules])
        return res


class KBPacman(pacman.PacmanAgent):
    def __init__(self, x, y, cell, kb_file):
        super(KBPacman, self).__init__(x, y, cell)

        # Add perceptions
        self.add_perception(Direction())
        self.add_perception(WallPerception((0, 1)))
        self.add_perception(WallPerception((0, -1)))
        self.add_perception(WallPerception((1, 0)))
        self.add_perception(WallPerception((-1, 0)))
        self.add_perception(GhostPerception())

        self._kb = KB(kb_file)

    def _think(self, delta):
        # If the previous action has finished
        if self.body.target is None:
            # Construct perception list. Add other facts to the list if needed.
            perceptions = [p.value for p in self._perceptions.values() if p.value != '']

            # Do inference. The infer method should return an action to
            # execute ('up', 'down', 'left' or 'right').
            action = self._kb.infer(perceptions)

            # Return actions to execute
            if action is not None:
                return [self._actions[action]]


class Direction(pyafai.Perception):
    def __init__(self):
        super(Direction, self).__init__(str, 'direction')

    def update(self, agent):
        self.value = 'going_' + pacman.GameAction.DIR_TO_ACTION[agent.body.direction]


class WallPerception(pyafai.Perception):
    def __init__(self, direction):
        super(WallPerception, self).__init__(str,
                        'wall_' + pacman.GameAction.DIR_TO_ACTION[direction])
        self._dir = direction

    def update(self, agent):
        if agent.world.has_wall_at(agent.body.cell_x + self._dir[0],
                                   agent.body.cell_y + self._dir[1]):
            self.value = self.name
        else:
            self.value = ''


class GhostPerception(pyafai.Perception):
    def __init__(self):
        super(GhostPerception, self).__init__(str, 'ghost')

    def update(self, agent):
        x = agent.body.cell_x
        y = agent.body.cell_y
        dir = agent.body.direction
        if agent.world.has_object_type_at(x + dir[0], y + dir[1],
                                          pacman.GhostBody):
            self.value = self.name
        else:
            self.value = ''


def test_kb():
    mykb = KB('ex03_kb_test.txt')
    print(mykb)
    print(mykb.infer(['red', 'rectangle']))


def setup():
    world = pacman.PacmanWorld(20, 'levels/medium.txt')
    display = pacman.PacmanDisplay(world)

    # Create ghosts
    world.spawn_ghost(pacman.RandomGhost)

    # Create pac-man agent
    world.spawn_player(KBPacman, 'ex03_kb_pacman.txt')
    world.player_lives = 1


if __name__ == '__main__':
    # test_kb()

    setup()
    pyafai.run()