from itertools import groupby

import stormpy
import sys
import os
import argparse
import dataclasses
from pprint import pprint

class Transition:
    def __init__(self, start, end, action, weight: float):
        self.start = f'{start}'
        self.end = f'{end}'
        self.action = action
        self.weight = weight

@dataclasses.dataclass
class Chain:
    def __init__(self, transitions, actions, states, start_state, goal_states, steps, output_file):
        self.transitions = transitions
        self.actions = actions # a list of lists containing the actions that belong with each other and should be unique
        self.states = states
        self.start_state = start_state
        self.goal_states = goal_states
        self.steps = steps
        self.output_file = output_file


def readFromMdp(filename: str, label = None):
    model = stormpy.parse_prism_program(filename)
    mdp = stormpy.build_sparse_model(model)

    matrix = mdp.transition_matrix
    
    transitions = []

    states = mdp.states

    stringifiedStates = []
    goals = []
    actions = [] #

    for index, s in enumerate(states):
        stringified = f'{s}'
        if label in s.labels:
            goals.append(stringified)
        stringifiedStates.append(stringified)

        row_group_start = matrix.get_row_group_start(index)
        row_group_end = matrix.get_row_group_end(index)

        action_combo = []
        for i in range(row_group_start, row_group_end):
            row = matrix.get_row(i)
            action = i
            action_combo.append(action)
            for entry in row:
                transitions.append(Transition(stringified, entry.column, action, entry.value()))

        actions.append(action_combo)

    return transitions, actions, stringifiedStates, goals

def readFromPomdp(filename: str, label = None):
    model = stormpy.parse_prism_program(filename)
    mdp = stormpy.build_sparse_model(model)

    matrix = mdp.transition_matrix
    
    transitions = []

    states = mdp.states

    stringifiedStates = []
    goals = []
    actions = [] #
    observations = []

    for index, s in enumerate(states):
        stringified = f'{s}'
        if label in s.labels:
            goals.append(stringified)
        stringifiedStates.append(stringified)

        row_group_start = matrix.get_row_group_start(index)
        row_group_end = matrix.get_row_group_end(index)

        observation = mdp.get_observation(s.id)

        action_combo = []
        for i in range(row_group_start, row_group_end):
            row = matrix.get_row(i)
            action = f'{observation}_{i - row_group_start}'
            action_combo.append(action)
            for entry in row:
                transitions.append(Transition(stringified, entry.column, action, entry.value()))

        if observation not in observations:
            actions.append(action_combo)
            observations.append(observation)

    return transitions, actions, stringifiedStates, goals


def readFromParsedArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="The path of the input file")
    parser.add_argument("-o", "--output", required=True, help="The path to output the cnf to")
    parser.add_argument("-s", "--start", required=True, help="The initial state")
    parser.add_argument("-g", "--goal", required=False, help="The goal state")
    parser.add_argument("-n", "--steps", required=True, help="The maximum amount of steps to reach the goal states")
    parser.add_argument("-l", "--label", required=False, help="The label of the goal states. Only works with .pm files")
    parser.add_argument("-p", "--pompd", action='store_true', help="Argument to indicate the input is a POMDP (Partially Observable)")

    args = parser.parse_args()
    inputFile = args.input
    outputFile = args.output
    startState = args.start
    N = int(args.steps)

    #_, extension = os.path.splitext(inputFile)
    
    if args.pompd:
        transitions, actions, states, goals = readFromPomdp(inputFile, args.label)
    else:
        transitions, actions, states, goals = readFromMdp(inputFile, args.label)
    
    if args.goal:
        goals = [args.goal]

    return Chain(transitions, actions, states, startState, goals, N, outputFile)
    
