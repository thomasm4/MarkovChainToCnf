from itertools import groupby
from pysat.formula import Formula, Atom, Or, Neg, CNF
from pysat.solvers import Solver
from pysat.pb import PBEnc
#from stormpy import *
import sys
import os

import stormpy
from import_transitions import readFromArgs, Transition, Chain

#matrixFile = "test.tra" #"lib/stormpy/examples/files/tra/die.tra"
#outputFile = "test.cnf" #"die.cnf"
#goalState = 10

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

    cnf = CNF(from_clauses=formula)
    cnf.to_file(outputFile)
    addWeights(transitions, outputFile, steps)
    print(Formula.export_vpool().id2obj)

chain = readFromArgs()

groupTransitions(chain.transitions)
makeCNF(chain.transitions, chain.states, chain.start_state, chain.goal_states, chain.output_file, chain.steps)

