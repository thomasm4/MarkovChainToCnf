from itertools import groupby

import stormpy
import sys
import os
import argparse
import dataclasses
from pprint import pprint

class Transition:
    def __init__(self, start, end, weight: float):
        self.start = f'{start}'
        self.end = f'{end}'
        self.weight = weight
    
    # Property indicating if transition is C{start}_{step} or Neg(C{start}_{step})
    # Only used with max 2 transitions
    isPositive: bool

@dataclasses.dataclass
class Chain:
    def __init__(self, transitions, states, start_state, goal_states, steps, output_file):
        self.transitions = transitions
        self.states = states
        self.start_state = start_state
        self.goal_states = goal_states
        self.steps = steps
        self.output_file = output_file

def fromLine(line: str) -> Transition:
    s = line.split(" ")
    return Transition(s[0], s[1], float(s[2]))


def readFromTra(fileName: str):
    f = open(fileName)
    lines = f.readlines()
    lines.pop(0)
    transitions = [fromLine(line.rstrip('\n')) for line in lines]

    states = list(dict.fromkeys([tra.start for tra in transitions] + [tra.end for tra in transitions]))
    return transitions, states, []

def readFromPm(filename: str, label = None):
    model = stormpy.parse_prism_program(filename)
    dtmc = stormpy.build_sparse_model(model)

    matrix = dtmc.transition_matrix
    
    transitions = []

    states = dtmc.states

    stringifiedStates = []
    goals = []
    for s in states:
        stringified = f'{s}'
        if label in s.labels:
            goals.append(stringified)
        stringifiedStates.append(stringified)
        row = matrix.get_row(s)
        for entry in row:
            transitions.append(Transition(stringified, entry.column, entry.value()))

    return transitions, stringifiedStates, goals

    
        
def readFromFile(path, extension, label = None):
    if extension == '.tra':
        return readFromTra(path)
    elif extension == '.pm':
        return readFromPm(path, label)
    else:
        raise Exception(f'Unknown extension')
    
def readFromArgs():
    args = sys.argv
    inputFile = args[1]
    outputFile = args[2]
    startState = args[3]
    goalState = args[4]
    N = int(args[5])

    _, extension = os.path.splitext(inputFile)

    transitions, states = readFromFile(inputFile, extension)
    return Chain(transitions, states, startState, [goalState], N, outputFile)

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

    _, extension = os.path.splitext(inputFile)
    
    transitions, states, goals = readFromFile(inputFile, extension, args.label)
    
    if args.goal:
        goals = [args.goal]
    print(states)
    print(goals)
        

    return Chain(transitions, states, startState, goals, N, outputFile)
    
