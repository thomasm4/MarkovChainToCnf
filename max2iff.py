from itertools import groupby, product
from pysat.formula import Formula, Atom, Or, Neg, CNF
from pysat.solvers import Solver
from pysat.pb import PBEnc
#from stormpy import *
import sys
import os

import stormpy
from import_transitions import readFromParsedArgs, Transition, Chain


# Variation on the max 2 transition formula utilizing iff between states and transitions instead of exclusion clauses on the states


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

def generateIffFormula(trans: list[Transition], states, steps: int = 1):
    clauses = []
    for state in states:
        filtered = list(filter(lambda t: t.end == state, trans))
        for s in range(steps):
            endState = stateAtom(state, s+1)
            atoms = []
            for tra in filtered:
                startState = stateAtom(tra.start, s)
                tAtom = transAtom(tra, s)

                clause = Or(endState, Neg(startState), Neg(tAtom))
                clause.clausify()
                clauses.append(clause.clauses[0])

                atoms.append([startState, tAtom])
            cartesianProduct = product(*atoms)
            for c in cartesianProduct:
                clause = Or(Neg(endState), *c)
                clause.clausify()
                clauses.append(clause.clauses[0])
    return clauses

def onlyStartClauses(states, start):
    clauses = []
    for state in states:
        atom = stateAtom(state, 0)
        if state != start:
            atom = Neg(atom)
        atom.clausify()
        clauses.append(atom.clauses[0])
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

    formula = []

    formula.extend(generateIffFormula(transitions, states, steps))
    print("iff")

    formula.extend(onlyStartClauses(states, initialState))
    print("start")
    
    formula.append(goalClause(goalstates, steps))
    print("goals")

    cnf = CNF(from_clauses=formula)
    cnf.to_file(outputFile)
    addWeights(transitions, outputFile, steps)
    print(Formula.export_vpool().id2obj)

chain = readFromParsedArgs()

groupTransitions(chain.transitions)
makeCNF(chain.transitions, chain.states, chain.start_state, chain.goal_states, chain.output_file, chain.steps)

