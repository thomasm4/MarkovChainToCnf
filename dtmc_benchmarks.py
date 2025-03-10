from makecnf_multiplication import makeCNF as new_order
from makecnf_multiplication_old_order import makeCNF as old_order
from import_transitions import readFromPm as read_pm
import time
import subprocess
import re
import os
import pathlib
import sys


def parseStormResult(output):
    return re.search("Result \(for initial states\): ([0-9]*\.?[0-9]*)", output).group(1)

def subSharpSAT(filename, tree_timeout = 1):
    return subprocess.run(['./sharpSAT', '-decot', f'{tree_timeout}', '-tmpdir', '.', '-WE', pathlib.Path(f'{filename}').resolve()], capture_output=True, cwd='../sharpsat-td/build')

def subGPMC(filename):
    return subprocess.run(['../GPMC/build/gpmc', '-mode=1', f'{filename}'], capture_output=True)

def parseGPMCResult(output):
    return re.search("exact double prec-sci ([0-9]*\.?[0-9]*)", output).group(1)

def parseSharpSATResult(output):
    return re.search("exact arb float ([0-9]*\.?[0-9]*)", output).group(1)

def runSharpSAT(filename, tree_timeout = 1):
    start = time.perf_counter()
    output = subSharpSAT(filename, tree_timeout)
    end = time.perf_counter()
    result = parseSharpSATResult(f'{output.stdout}')
    return result, end - start

def runGPMC(filename):
    start = time.perf_counter()
    output = subGPMC(filename)
    end = time.perf_counter()
    result = parseGPMCResult(f'{output.stdout}')
    return result, end - start

def runStorm(filename, target, n):
    start = time.perf_counter()
    storm = subprocess.run(['../storm/build/bin/storm', '--prism', f'benchmarks/{filename}', '-prop', f'P=?  [F={n} "{target}" ]'], capture_output=True)
    end = time.perf_counter()
    duration = end - start
    storm_output = f'{storm.stdout}'
    return parseStormResult(storm_output), duration

def makeOldCNF(filename, target, n):
    cnf_file_name = f'temp_old_{filename}.cnf'
    start = time.perf_counter()
    transitions, stringifiedStates, goals = read_pm(f'benchmarks/{filename}', target)
    old_order(transitions, stringifiedStates, "0", goals, cnf_file_name, n)
    end = time.perf_counter()
    return end - start, cnf_file_name

def makeNewCNF(filename, target, n):
    cnf_file_name = f'temp_new_{filename}.cnf'
    start = time.perf_counter()
    transitions, stringifiedStates, goals = read_pm(f'benchmarks/{filename}', target)
    new_order(transitions, stringifiedStates, "0", goals, cnf_file_name, n)
    end = time.perf_counter()
    return end - start, cnf_file_name

def runFile(filename, name, target, n):
    print(f'name: {name}, target: {target}, n: {n}')
    print("Method, Output/Size, Duration")

    storm_output, storm_duration = runStorm(filename, target, n)
    print(f'Storm, {storm_output}, {storm_duration}')

    old_creation, old_file = makeOldCNF(filename, target, n)
    old_size = os.path.getsize(old_file)
    print(f'CNF old, {old_size}, {old_creation}')
    new_creation, new_file = makeNewCNF(filename, target, n)
    new_size = os.path.getsize(new_file)
    print(f'CNF new, {new_size}, {new_creation}')

    gpmc_output_old, gpmc_solved_old = runGPMC(old_file)
    print(f'GPMC old, {gpmc_output_old}, {gpmc_solved_old}')
    gpmc_output_new, gpmc_solved_new = runGPMC(new_file)
    print(f'GPMC new, {gpmc_output_new}, {gpmc_solved_new}')

    sharpsat_output_old, sharp_solved_old = runSharpSAT(old_file)
    print(f'Sharp old, {sharpsat_output_old}, {sharp_solved_old}')
    sharpsat_output_new, sharp_solved_new = runSharpSAT(new_file)
    print(f'Sharp new, {sharpsat_output_new}, {sharp_solved_new}')
    sharpsat_output_old_long_tree, sharp_solved_old_long_tree = runSharpSAT(old_file, 120)
    print(f'Sharp o tree, {sharpsat_output_old_long_tree}, {sharp_solved_old_long_tree}')
    sharpsat_output_new_long_tree, sharp_solved_new_long_tree = runSharpSAT(new_file, 120)
    print(f'Sharp n tree, {sharpsat_output_new_long_tree}, {sharp_solved_new_long_tree}')

    os.remove(old_file)
    os.remove(new_file)
    
    if storm_output == gpmc_output_old == gpmc_output_new == sharpsat_output_old == sharpsat_output_new:
        print("\n\nCorrect output---------------------------------------------------------------------------------------------------------")
    else:
        print("\n\nWarning: Incorrect output----------------------------------------------------------------------------------------------")
    

def run_and_parse_file(input):
    splitted = input.split(".")
    if len(splitted) < 4:
        raise Exception(f'Not enough arguments to adhere to format:{input}')
    name = splitted[0]
    goal = splitted[1]
    n = splitted[2]
    runFile(input, name, goal, int(n))

args = sys.argv
run_and_parse_file(args[1])

