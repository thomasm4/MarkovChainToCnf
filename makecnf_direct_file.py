from itertools import groupby, product
from pysat.formula import Formula, Atom, Or, Neg, CNF
from pysat.solvers import Solver
from pysat.pb import PBEnc
#from stormpy import *
import sys
import os

import stormpy
from import_transitions import readFromParsedArgs, Transition, Chain


# Variation of the memory version but instead of combining the results at the end it is constantly appending rows to the cnf file.

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

rows = 0
def writeClause(clause, file):
    global rows
    file.write(f'{" ".join(str(x) for x in clause)} 0\n')
    rows += 1

def generateIffFormula(trans: list[Transition], states, steps, file):
    for state in states:
        filtered = list(filter(lambda t: t.end == state, trans))
        for s in range(steps):
            endState = getState(state, s+1)
            atoms = []
            for tra in filtered:
                #startState = stateAtom(tra.start, s)
                tAtom = getTransition(tra, s)
                clause = [endState, -tAtom] #Or(endState, Neg(tAtom))
                writeClause(clause, file)
                atoms.append(tAtom)
            clause = [-endState, *atoms] #Or(Neg(endState), *atoms)
            writeClause(clause, file)

def onlyStartClauses(states, start, file):
    for state in states:
        atom = getState(state, 0)
        if state != start:
            atom *= -1#Neg(atom)
            #atom = -atom
        writeClause([atom], file)

def transExclusionClauses(trans: list[Transition], steps, file):
    groups = [list(g) for k, g in groupby(trans, key=lambda t: t.start)] # GROUP BY DOES NOT WORK ON UNSORTED
    for group in groups:
        for s in range(steps):
            for i in range(len(group)-1):
                for j in range(i+1, len(group)):
                    tra1 = group[i]
                    tra2 = group[j]
                    #Implies(stateAtom(tra1, s), Neg(stateAtom(tra2, s)))
                    #clause = Or(Neg(transAtom(tra1, s)), Neg(transAtom(tra2, s)))
                    clause = [-getTransition(tra1, s), -getTransition(tra2, s)]
                    writeClause(clause, file)

def oneTransClauses(trans: list[Transition], states, steps, file):
    for state in states:
        for s in range(steps):
            #Implies((stateAtom(tra.end, s+1)), *(transAtom(tra, s)))
            filtered = filter(lambda t: t.start == state, trans)
            transAtoms = [getTransition(tra, s) for tra in filtered]
            clause = [-getState(state, s), *transAtoms] #Or(Neg(stateAtom(state, s)), *transAtoms)
            writeClause(clause, file)

def stateImpliesTrans(trans: list[Transition], steps, file):
    for s in range(steps):
        for tra in trans:
            clause = [getState(tra.start, s), -getTransition(tra, s)] #Or(stateAtom(tra.start, s), Neg(transAtom(tra, s)))
            writeClause(clause, file)

def goalClause(goalStates, steps, file):
    goals = []
    for goal in goalStates:
        for s in range(steps+1):
            goals.append(getState(goal, s))
    writeClause(goals, file)

def addWeights(transitions: list[Transition], steps, file):
    for tra in transitions:
        for s in range(steps):
            name = getTransition(tra, s)
            file.write(f'c p weight {name} {tra.weight} 0\n')
            file.write(f'c p weight -{name} 1 0\n')

def makeCNF(transitions: list[Transition], states, initialState, goalstates, outputFile, steps: int = 1):
    fillMap(transitions, states)

    file = open(outputFile, "w")
    file.write(f'p cnf {getState(states[-1], steps)}\n') # later in the program the amount of rows should be appended

    generateIffFormula(transitions, states, steps, file)
    stateImpliesTrans(transitions, steps, file)
    transExclusionClauses(transitions, steps, file)
    oneTransClauses(transitions, states, steps, file)
    onlyStartClauses(states, initialState, file)
    goalClause(goalstates, steps, file)

    addWeights(transitions, steps, file)

    print(rows)

chain = readFromParsedArgs()

makeCNF(chain.transitions, chain.states, chain.start_state, chain.goal_states, chain.output_file, chain.steps)

