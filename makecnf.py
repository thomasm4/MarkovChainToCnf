from itertools import groupby
from pysat.formula import Formula, Atom, Or, Neg, CNF
from pysat.solvers import Solver
from pysat.pb import PBEnc
#from stormpy import *
import sys
import os

import stormpy

#matrixFile = "test.tra" #"lib/stormpy/examples/files/tra/die.tra"
#outputFile = "test.cnf" #"die.cnf"
#goalState = 10

class Transition:
    def __init__(self, start, end, weight: float):
        self.start = start
        self.end = end
        self.weight = weight
    
    #Property indicating if transition is C{start}_{step} or Neg(C{start}_{step})
    isPositive: bool

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

def groupTransitions(transitions: list[Transition]):
    groups = [list(g) for k, g in groupby(transitions, key=lambda t: t.start)]
    for group in groups:
        group[0].isPositive = True
        if(len(group) == 2):
            group[1].isPositive = False
        elif(len(group) > 2):
            for tra in group:
                print(vars(tra))
            raise Exception(f'states with more than 2 transitions are not supported')

def stateAtom(state, step):
    return Atom(f'X{state}_{step}')

def transAtom(tra: Transition, step):
    return Atom(f'C{tra.start}_{tra.end}_{step}')

def oldtransAtom(tra: Transition, step):
    transition = Atom(f'C{tra.start}_{step}')
    if not tra.isPositive:
        transition = Neg(transition)
    return transition


def transtitionToFormulas(tra: Transition, steps: int = 1):
    clauses = []
    for s in range(steps):
        #Implies(And(Atom(f'X{tra.start}_{s}'), transition), Atom(f'X{tra.end}_{s+1}'))
        clause = Or(Neg(stateAtom(tra.start, s)), Neg(transAtom(tra, s)), stateAtom(tra.end, s+1))
        
        clause.clausify()
        clauses.append(clause.clauses[0])
    return clauses

def allTransitionsToFormula(trans: list[Transition], steps: int = 1):
    formulas = []
    for t in trans:
        for f in transtitionToFormulas(t, steps):
            formulas.append(f)
    return formulas

def stateExclusionClauses(states, steps: int = 1):
    clauses = []
    for s in range(steps + 1):
        for i in range(len(states)-1):
            for j in range(i+1, len(states)):
                state1 = states[i]
                state2 = states[j]
                #Implies(stateAtom(state1, s), Neg(stateAtom(state2, s)))
                clause = Or(Neg(stateAtom(state1, s)), Neg(stateAtom(state2, s)))
                clause.clausify()
                clauses.append(clause.clauses[0])
    return clauses

def transExclusionClauses(trans: list[Transition], steps: int = 1):
    clauses = []
    groups = [list(g) for k, g in groupby(trans, key=lambda t: t.start)]
    for group in groups:
        for s in range(steps):
            for i in range(len(group)-1):
                for j in range(i+1, len(group)):
                    tra1 = group[i]
                    tra2 = group[j]
                    #Implies(stateAtom(tra1, s), Neg(stateAtom(tra2, s)))
                    clause = Or(Neg(transAtom(tra1, s)), Neg(transAtom(tra2, s)))
                    clause.clausify()
                    clauses.append(clause.clauses[0])
    return clauses

def oneStateClauses(states, steps: int = 1):
    clauses = []
    for s in range(steps + 1):
        clause = []
        for state in states:
            atom = stateAtom(state, s)
            atom.clausify()
            clause.append(atom.clauses[0][0])
        clauses.append(clause)
    return clauses


def goalClause(goalStates, steps: int = 1):
    goals = []
    for goal in goalStates:
        for s in range(steps+1):
            goals.append(stateAtom(goal, s))
    clause = Or(*goals)
    clause.clausify()
    return clause.clauses[0]

def addWeights(transitions: list[Transition], fileName, steps: int = 1):
    f = open(fileName, "a")
    idPool = Formula.export_vpool()
    for tra in transitions:
        for s in range(steps):
            start = transAtom(tra, s)
            name = idPool.obj2id[start]
            f.write(f'c p weight {name} {tra.weight} 0\n')

def makeCNF(transitions: list[Transition], states, initialState, goalstates, outputFile, steps: int = 1):
    formula = allTransitionsToFormula(transitions, steps)

    start = stateAtom(initialState, 0)
    start.clausify()
    formula.append(start.clauses[0])

    formula.append(goalClause(goalstates, steps))

    formula.extend(stateExclusionClauses(states, steps))
    formula.extend(oneStateClauses(states, steps))
    #formula.extend(transExclusionClauses(transitions, steps))

    cnf = CNF(from_clauses=formula)
    cnf.to_file(outputFile)
    addWeights(transitions, outputFile, steps)
    print(Formula.export_vpool().id2obj)


args = sys.argv
inputFile = args[1]
outputFile = args[2]
startState = args[3]
goalState = args[4]
N = int(args[5])

_, extension = os.path.splitext(inputFile)

print(args)
print(extension)

if extension == '.tra':
    transitions, states = readFromTra(inputFile)
elif extension == '.pm':
    transitions, states = readFromPm(inputFile)
else:
    raise Exception(f'Unknown extension')

for state in states:
    print(state)
#    print(f'{state}')

#groupTransitions(transitions)
makeCNF(transitions, states, startState, [goalState], outputFile, N)

