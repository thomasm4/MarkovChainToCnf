from itertools import groupby
from pysat.formula import Formula, Atom, Or, Neg, CNF
from pysat.solvers import Solver
from pysat.pb import PBEnc
#from stormpy import *
import argparse

import stormpy
from import_transitions import readFromArgs, readFromParsedArgs, Transition, Chain

#matrixFile = "test.tra" #"lib/stormpy/examples/files/tra/die.tra"
#outputFile = "test.cnf" #"die.cnf"
#goalState = 10


def stateAtom(state, step):
    return Atom(f'X{state}_{step}')

def transAtom(tra: Transition, step):
    return Atom(f'C{tra.start}_{tra.end}_{step}')

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
    groups = [list(g) for k, g in groupby(trans, key=lambda t: t.start)] # GROUP BY DOES NOT WORK ON UNSORTED
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

def oneTransClauses(trans: list[Transition], states, steps):
    clauses = []
    for state in states:
        for s in range(steps):
            #Implies((stateAtom(tra.end, s+1)), *(transAtom(tra, s)))
            filtered = filter(lambda t: t.start == state, trans)
            transAtoms = [transAtom(tra, s) for tra in filtered]
            clause = Or(*transAtoms)
            clause.clausify()
            clauses.append(clause.clauses[0])
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
            f.write(f'c p weight -{name} 1 0\n')

def makeCNF(transitions: list[Transition], states, initialState, goalstates, outputFile, steps: int = 1):
    formula = allTransitionsToFormula(transitions, steps)

    start = stateAtom(initialState, 0)
    start.clausify()
    formula.append(start.clauses[0])

    formula.append(goalClause(goalstates, steps))

    formula.extend(stateExclusionClauses(states, steps))
    formula.extend(transExclusionClauses(transitions, steps))
    formula.extend(oneTransClauses(transitions, states, steps))

    cnf = CNF(from_clauses=formula)
    cnf.to_file(outputFile)
    addWeights(transitions, outputFile, steps)
    print(Formula.export_vpool().id2obj)
# +1 +2 +3 -4 -5 +6 -7 -8 -9 +10 +11 -12 -13 -14 +15 -16 +17 -18 -19 -20 -21 -22 -23 -24 +25 +26 -27 +28 -29 +30 -31 +32 -33 -34 -35 -36 +37 +38 +39 -40 0

chain = readFromParsedArgs()

#for state in chain.states:
#    print(state)
#    print(f'{state}')

#groupTransitions(transitions)
makeCNF(chain.transitions, chain.states, chain.start_state, chain.goal_states, chain.output_file, chain.steps)

