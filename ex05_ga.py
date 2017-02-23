# coding: utf-8
# -----------------------------------------------------------------------------
# Copyright (c) 2015 Tiago Baptista
# All rights reserved.
# -----------------------------------------------------------------------------

"""
Evolving Neural Networks with a Genetic Algorithm

"""

from __future__ import division

__docformat__ = 'restructuredtext'
__author__ = 'Tiago Baptista'
__version__ = '1.0'


import random
import math


class NNLayer:
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

    def set_weights(self, weights):
        for neuron in range(len(self._weights)):
            for i in range(len(self._weights[neuron])):
                self._weights[neuron][i] = weights[neuron * len(self._weights[neuron]) + i]

    def __len__(self):
        return self._nout


class NNFeedForward:
    def __init__(self, n_in, n_hidden, n_out):
        self._nin = n_in

        self._hidden = NNLayer(n_hidden, n_in)
        self._out = NNLayer(n_out, n_hidden)

        self._hidden_outputs = []

    def feed_forward(self, inputs):
        self._hidden_outputs = self._hidden.feed_forward(inputs)
        outputs = self._out.feed_forward(self._hidden_outputs)

        return outputs

    def set_weights(self, weights):
        self._hidden.set_weights(weights[:self._nin * (len(self._hidden) + 1)])
        self._out.set_weights(weights[self._nin * (len(self._hidden) + 1):])


class GA:
    def __init__(self, n=20):
        self._population_size = n
        self._population = [[self.create_individual(), 0.0] for i in range(n)]

        self._sigma = 2

        self._prob_cx = 0.8
        self._prob_m = 0.01
        self._elitism = int(0.1 * n)

        self._test = [[[0, 0], 0], [[0, 1], 1], [[1, 0], 1], [[1, 1], 0]]

    def run(self, iterations):
        stop = False
        gen = 0

        while not stop:
            # Evaluate
            for i in range(len(self._population)):
                self._population[i][1] = self.fitness(self._population[i][0])
            self._population.sort(key=lambda x: x[1])
            print("Generation:", gen, "Best:", self._population[0][1])

            # Select parents
            parents = self.select_parents()

            # Cross-over
            offspring = []
            for i in range(len(parents) // 2):
                p1 = parents[i]
                p2 = parents[i + 1]
                offspring.extend(self.cross_over(p1, p2))

            # Mutation
            for ind in offspring:
                self.mutate(ind)

            # Select new population
            self._population = self._population[:self._elitism]
            self._population += [[ind, 0.0] for ind in offspring]

            gen += 1
            if gen >= iterations:
                stop = True

        self._population.sort(key=lambda x: self.fitness(x[0]))
        best = self._population[0]
        nn = NNFeedForward(2, 2, 1)
        nn.set_weights(best[0])
        return nn, self.fitness(best[0])

    def create_individual(self):
        return [random.uniform(-10, 10) for _ in range(9)]

    def mutate(self, ind):
        for i in range(len(ind)):
            if random.random() < self._prob_m:
                ind[i] += random.gauss(0, self._sigma)

    def cross_over(self, ind1, ind2):
        if random.random() < self._prob_cx:
            k = random.randint(1, 8)
            child1 = ind1[:k] + ind2[k:]
            child2 = ind2[:k] + ind1[k:]
            return child1, child2
        else:
            return ind1, ind2

    def select_parents(self):
        parents = []
        for i in range(len(self._population) - self._elitism):
            t = random.sample(self._population, 8)
            t.sort(key=lambda x: x[1])
            if random.random() < 1.0:
                parents.append(t[0][0])
            else:
                parents.append(t[1][0])

        return parents

    def fitness(self, ind):
        nn = NNFeedForward(2, 2, 1)
        nn.set_weights(ind)

        total = 0
        for i, o in self._test:
            total += abs(nn.feed_forward(i)[0] - o)

        return total


if __name__ == '__main__':
    ga = GA(100)
    best = ga.run(10000)[0]
    print(best.feed_forward([0, 0]))
    print(best.feed_forward([0, 1]))
    print(best.feed_forward([1, 0]))
    print(best.feed_forward([1, 1]))

