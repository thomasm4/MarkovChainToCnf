from itertools import groupby, product
from pysat.formula import Formula, Atom, Or, Neg, CNF
from pysat.solvers import Solver
from pysat.pb import PBEnc
#from stormpy import *
import sys
import os

import stormpy
from import_transitions import readFromParsedArgs, Transition, Chain


# Variation of the makecnf_new algorithm, optimizing memory usage by calculating only the first step and copying the outcome N times.

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
    

#def stateAtom(state, step):
#    #return Atom(f'X{state}_{step}')
#    return getState(state, step)
#
#def transAtom(tra: Transition, step):
#    #return Atom(f'C{tra.start}_{tra.end}_{step}')
#    return getTransition(tra, step)

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

    formula = []
    for s in range(steps):
        formula.extend(generateIffFormula(transitions, states, s))
        formula.extend(stateImpliesTrans(transitions, s))
        formula.extend(transExclusionClauses(transitions, s))
        formula.extend(oneTransClauses(transitions, states, s))
    
    formula.append(goalClause(goalstates, steps))
    formula.extend(onlyStartClauses(states, initialState))

    #print(formula)
    cnf = CNF(from_clauses=formula)
    cnf.to_file(outputFile)
    addWeights(transitions, outputFile, steps)
    #print(Formula.export_vpool().id2obj)

chain = readFromParsedArgs()

makeCNF(chain.transitions, chain.states, chain.start_state, chain.goal_states, chain.output_file, chain.steps)

