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

def requireStateClauses(trans, steps):
    clauses = []
    
    for tra in trans:
        for s in range(steps):
            #Implies(Neg(stateAtom(tra.start, s)), Neg(transAtom(tra, s)))
            clause = Or(stateAtom(tra.start, s), Neg(transAtom(tra, s)))
            print(clause)
            clause.clausify()
            clauses.append(clause.clauses[0])
    return clauses

def requireTransClauses(trans: list[Transition], states, steps):
    clauses = []
    for state in states:
        #print(group)
        for s in range(steps):
            #Implies((stateAtom(tra.end, s+1)), *(transAtom(tra, s)))
            filtered = filter(lambda t: t.end == state, trans)
            transAtoms = [transAtom(tra, s) for tra in filtered]
            print(transAtoms)
            for tra in transAtoms:
                clause = Or(Neg(stateAtom(state, s+1)), tra)
                clause.clausify()
                clauses.append(clause.clauses[0])
    return clauses

def oneTransClauses(trans: list[Transition], states, steps):
    clauses = []
    for state in states:
        #print(group)
        for s in range(steps):
            #Implies((stateAtom(tra.end, s+1)), *(transAtom(tra, s)))
            filtered = filter(lambda t: t.start == state, trans)
            transAtoms = [transAtom(tra, s) for tra in filtered]
            print(transAtoms)
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


chain = readFromParsedArgs()

#for state in chain.states:
#    print(state)
#    print(f'{state}')

#groupTransitions(transitions)
makeCNF(chain.transitions, chain.states, chain.start_state, chain.goal_states, chain.output_file, chain.steps)

