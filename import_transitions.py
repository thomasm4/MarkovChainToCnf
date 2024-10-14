from itertools import groupby

import stormpy
import sys
import os
import argparse


class Transition:
    def __init__(self, start, end, weight: float):
        self.start = start
        self.end = end
        self.weight = weight
    
    # Property indicating if transition is C{start}_{step} or Neg(C{start}_{step})
    # Only used with max 2 transitions
    isPositive: bool

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
    return transitions, states

def readFromPm(filename: str):
    model = stormpy.parse_prism_program(filename)
    dtmc = stormpy.build_sparse_model(model)

    matrix = dtmc.transition_matrix
    states = dtmc.states
    transitions = []
    print(states)

    for s in states:
        row = matrix.get_row(s)
        for entry in row:
            transitions.append(Transition(f'{s}', entry.column, entry.value()))

    return transitions, states

    # get state labeling of dtmc
    #for state in dtmc.states:
    #    if sys.argv[2] in state.labels:
    #        print(state, state.labels)
        
def readFromFile(path, extension):
    if extension == '.tra':
        return readFromTra(path)
    elif extension == '.pm':
        return readFromPm(path)
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
    parser.add_argument("-o", "--ouput", required=True, help="The path to output the cnf to")
    parser.add_argument("-s", "--start", required=True, help="The initial state")
    parser.add_argument("-g", "--goal", required=True, help="The goal state")
    parser.add_argument("-n", "--steps", required=True, help="The maximum amount of steps to reach the goal states")

    args = parser.parse_args()
    inputFile = args.input
    outputFile = args.output
    startState = args.start
    goalState = args.goal
    N = args.steps

    _, extension = os.path.splitext(inputFile)
    transitions, states = readFromFile(inputFile, extension)
    return Chain(transitions, states, startState, [goalState], N, outputFile)
    
