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
    print(matrix)
    
    transitions = []

    states = mdp.states

    stringifiedStates = []
    goals = []
    actions = [] #

    for index, s in enumerate(states):
        print(f'index:{index}')
        print(f'state:{s}')
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
            print(row)
            for entry in row:
                transitions.append(Transition(stringified, entry.column, action, entry.value()))

        actions.append(action_combo)

    for tra in transitions:
        print(vars(tra))

    print(actions)
    return transitions, actions, stringifiedStates, goals

def readFromParsedArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="The path of the input file")
    parser.add_argument("-o", "--output", required=True, help="The path to output the cnf to")
    parser.add_argument("-s", "--start", required=True, help="The initial state")
    parser.add_argument("-g", "--goal", required=False, help="The goal state")
    parser.add_argument("-n", "--steps", required=True, help="The maximum amount of steps to reach the goal states")
    parser.add_argument("-l", "--label", required=False, help="The label of the goal states. Only works with .pm files")

    args = parser.parse_args()
    inputFile = args.input
    outputFile = args.output
    startState = args.start
    N = int(args.steps)

    #_, extension = os.path.splitext(inputFile)
    
    transitions, actions, states, goals = readFromMdp(inputFile, args.label)
    
    if args.goal:
        goals = [args.goal]

    return Chain(transitions, actions, states, startState, goals, N, outputFile)
    
readFromParsedArgs()
