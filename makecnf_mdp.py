from itertools import groupby, product
from pysat.formula import Formula, Atom, Or, Neg, CNF
from pysat.solvers import Solver
from pysat.pb import PBEnc
#from stormpy import *
import sys
import os
import math

import stormpy
from import_mdp import readFromParsedArgs, Transition, Chain


# Variation of the multiplication algorithm for MDPs

atomMap : dict
mapSize : int
actionStart : int # variable to show were the actions start counting (mapsize*(steps) + len(states) + 1)
def fillMap(transitions, states):
    global mapSize, atomMap
    atomMap = dict()
    i = 1
    for state in states:
        atomMap[state] = i
        i += 1
    for transition in transitions:
        atomMap[f'{transition.start}_{transition.end}_{transition.action}'] = i
        i += 1
    mapSize = i - 1

def getState(state, step) -> int:
    return atomMap[state] + (step*mapSize)

def getTransition(transition, step) -> int:
    return atomMap[f'{transition.start}_{transition.end}_{transition.action}'] + (step*mapSize)

def getAction(action) -> int:
    return actionStart + action

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

def transExclusionClauses(trans: list[Transition], s: int):
    clauses = []
    groups = [list(g) for k, g in groupby(trans, key=lambda t: t.start)] # GROUP BY DOES NOT WORK ON UNSORTED
    for group in groups:
        for i in range(len(group)-1):
            for j in range(i+1, len(group)):
                tra1 = group[i]
                tra2 = group[j]
                #clause = Or(Neg(transAtom(tra1, s)), Neg(transAtom(tra2, s)))
                clause = [-getTransition(tra1, s), -getTransition(tra2, s)]
                clauses.append(clause)
    return clauses

def oneTransClauses(trans: list[Transition], states, s: int):
    clauses = []
    for state in states:
        #Implies((stateAtom(tra.end, s+1)), *(transAtom(tra, s)))
        filtered = filter(lambda t: t.start == state, trans)
        transAtoms = [getTransition(tra, s) for tra in filtered]
        clause = [-getState(state, s), *transAtoms] #Or(Neg(stateAtom(state, s)), *transAtoms)
        clauses.append(clause)
    return clauses

def stateImpliesTrans(trans: list[Transition], s: int):
    clauses = []
    for tra in trans:
        clause = [getState(tra.start, s), -getTransition(tra, s)] #Or(stateAtom(tra.start, s), Neg(transAtom(tra, s)))
        clauses.append(clause)
    return clauses

def goalClause(goalStates, steps: int):
    goals = []
    for goal in goalStates:
        for s in range(steps+1):
            goals.append(getState(goal, s))
    return goals

# This function cannot be calculated through multiplication since the variables for actions are static and do not scale with s
def transRequiresActionClause(trans: list[Transition], steps: int):
    clauses = []
    for s in range(steps):
        for tra in trans:
            # -action -> -transition
            clause = [getAction(tra.action), -getTransition(tra, s)] #Or(action, Neg(transAtom(tra, s)))
            clauses.append(clause)
    return clauses

def actionExclusiveOr(actions):
    clauses = []
    for actionCombo in actions:
        for i in range(len(actionCombo)-1):
            for j in range(i+1, len(actionCombo)):
                a1 = actionCombo[i]
                a2 = actionCombo[j]
                #clause = Or(Neg(transAtom(tra1, s)), Neg(transAtom(tra2, s)))
                clause = [-getAction(a1), -getAction(a2)]
                clauses.append(clause)
        clauses.append([getAction(a) for a in actionCombo])
    return clauses

def addWeights(transitions: list[Transition], file, steps: int = 1):
    for tra in transitions:
        for s in range(steps):
            name = getTransition(tra, s)
            file.write(f'c p weight {name} {tra.weight} 0\n')
            file.write(f'c p weight -{name} 1 0\n')

def addProjection(actions, file):
    file.write(f'c p max {" ".join(str(getAction(a)) for actionCombo in actions for a in actionCombo)} 0\n')
    #file.write(f'c p show {" ".join(str(x) for x in range(actionStart))} 0\n')

def makeCNF(transitions: list[Transition], actions, states, initialState, goalstates, outputFile, steps: int = 1):
    global actionStart

    fillMap(transitions, states)
    actionStart = (mapSize*(steps)) + len(states) + 1

    print(atomMap)

    formula1 = []
    formula1.extend(generateIffFormula(transitions, states, 0))
    formula1.extend(stateImpliesTrans(transitions, 0))
    formula1.extend(transExclusionClauses(transitions, 0))
    formula1.extend(oneTransClauses(transitions, states, 0))
    formula = formula1.copy()
    for s in range(1, steps):
        for clause in formula1:
            formula.append([x + int(math.copysign(s*mapSize, x)) for x in clause])
    
    formula.extend(transRequiresActionClause(transitions, steps))
    formula.append(goalClause(goalstates, steps))
    formula.extend(onlyStartClauses(states, initialState))
    formula.extend(actionExclusiveOr(actions))

    #print(formula)
    cnf = CNF(from_clauses=formula)
    cnf.to_file(outputFile)

    file = open(outputFile, "a")
    addWeights(transitions, file, steps)
    addProjection(actions, file)
    #print(Formula.export_vpool().id2obj)

chain = readFromParsedArgs()

makeCNF(chain.transitions, chain.actions, chain.states, chain.start_state, chain.goal_states, chain.output_file, chain.steps)

