from itertools import groupby, product
from pysat.formula import Formula, Atom, Or, Neg, CNF
from pysat.solvers import Solver
from pysat.pb import PBEnc
#from stormpy import *
import sys
import os
import math

import stormpy
from import_transitions import readFromParsedArgs, Transition, Chain
import buildcnf


# Variation of the memory version, instead only calculating the first step deriving the other steps through addition and multiplication.

atomMap : dict
mapSize : int
def fillMap(transitions, states):
    global mapSize, atomMap
    atomMap = dict()
    i = 1
    for state in states:
        atomMap[state] = i
        i += 1
    for transition in transitions:
        atomMap[f'{transition.start}_{transition.end}'] = i
        i += 1
    mapSize = i - 1

def getState(state, step) -> int:
    return atomMap[state] + (step*mapSize)

def getTransition(transition, step) -> int:
    return atomMap[f'{transition.start}_{transition.end}'] + (step*mapSize)

def generateIffFormula(trans: list[Transition], states, s: int = 1):
    clauses = []
    for state in states:
        filtered = list(filter(lambda t: t.end == state, trans))
        endState = getState(state, s+1)
        atoms = []
        for tra in filtered:
            #startState = stateAtom(tra.start, s)
            tAtom = getTransition(tra, s)
            clause = [endState, -tAtom] #Or(endState, Neg(tAtom))
            clauses.append(clause)
            atoms.append(tAtom)
        clause = [-endState, *atoms] #Or(Neg(endState), *atoms)
        clauses.append(clause)
    return clauses

def onlyStartClauses(states, start):
    clauses = []
    for state in states:
        atom = getState(state, 0)
        if state != start:
            atom *= -1#Neg(atom)
            #atom = -atom
        clauses.append([atom])
    return clauses

def transExclusionClauses(trans: list[Transition], s: int = 1):
    clauses = []
    groups = [list(g) for k, g in groupby(trans, key=lambda t: t.start)] # GROUP BY DOES NOT WORK ON UNSORTED
    for group in groups:
        for i in range(len(group)-1):
            for j in range(i+1, len(group)):
                tra1 = group[i]
                tra2 = group[j]
                #Implies(stateAtom(tra1, s), Neg(stateAtom(tra2, s)))
                #clause = Or(Neg(transAtom(tra1, s)), Neg(transAtom(tra2, s)))
                clause = [-getTransition(tra1, s), -getTransition(tra2, s)]
                clauses.append(clause)
    return clauses

def oneTransClauses(trans: list[Transition], states, s: int = 1):
    clauses = []
    for state in states:
        #Implies((stateAtom(tra.end, s+1)), *(transAtom(tra, s)))
        filtered = filter(lambda t: t.start == state, trans)
        transAtoms = [getTransition(tra, s) for tra in filtered]
        clause = [-getState(state, s), *transAtoms] #Or(Neg(stateAtom(state, s)), *transAtoms)
        clauses.append(clause)
    return clauses

def stateImpliesTrans(trans: list[Transition], s: int = 1):
    clauses = []
    for tra in trans:
        clause = [getState(tra.start, s), -getTransition(tra, s)] #Or(stateAtom(tra.start, s), Neg(transAtom(tra, s)))
        clauses.append(clause)
    return clauses

def goalClause(goalStates, steps: int = 1):
    goals = []
    for goal in goalStates:
        for s in range(steps+1):
            goals.append(getState(goal, s))
    return goals

def addWeights(transitions: list[Transition], fileName, steps: int = 1):
    f = open(fileName, "a")
    for tra in transitions:
        for s in range(steps):
            name = getTransition(tra, s)
            f.write(f'c p weight {name} {tra.weight} 0\n')
            f.write(f'c p weight -{name} 1 0\n')

def makeCNF(transitions: list[Transition], states, initialState, goalstates, outputFile, steps: int = 1):

    fillMap(transitions, states)

    formula1 = []
    formula1.extend(generateIffFormula(transitions, states, 0))
    formula1.extend(stateImpliesTrans(transitions, 0))
    formula1.extend(transExclusionClauses(transitions, 0))
    formula1.extend(oneTransClauses(transitions, states, 0))
    formula = formula1.copy()
    for s in range(1, steps):
        for clause in formula1:
            formula.append([x + int(math.copysign(s*mapSize, x)) for x in clause])
    
    formula.append(goalClause(goalstates, steps))
    formula.extend(onlyStartClauses(states, initialState))
    
    buildcnf.buildcnf(formula, (mapSize * steps) + len(states), outputFile)
    addWeights(transitions, outputFile, steps)
    #print(atomMap)
    #print(Formula.export_vpool().id2obj)

if __name__ == "__main__":
    chain = readFromParsedArgs()
    makeCNF(chain.transitions, chain.states, chain.start_state, chain.goal_states, chain.output_file, chain.steps)

