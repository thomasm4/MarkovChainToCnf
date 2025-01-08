import stormpy
from makecnf_multiplication import makeCNF as new_order
from makecnf_multiplication_old_order import makeCNF as old_order
from import_transitions import readFromPm as read_pm
import time
import subprocess
import re
import os
import pathlib


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

def runSharpSAT(filename, target, n, make_function, tree_timeout = 1):
    cnf_file_name = f'temp_{filename}.cnf'
    start = time.perf_counter()
    transitions, stringifiedStates, goals = read_pm(f'benchmarks/{filename}', target)
    make_function(transitions, stringifiedStates, "0", goals, cnf_file_name, n)
    cnf_made = time.perf_counter()
    output = subSharpSAT(cnf_file_name, tree_timeout)
    end = time.perf_counter()

    cnf_creation = cnf_made - start
    cnf_solved = end - cnf_made
    total_duration = cnf_creation + cnf_solved
    result = parseSharpSATResult(f'{output.stdout}')
    os.remove(cnf_file_name)
    return result, cnf_creation, cnf_solved, total_duration

def runGPMC(filename, target, n, make_function):
    cnf_file_name = f'temp_{filename}.cnf'
    start = time.perf_counter()
    transitions, stringifiedStates, goals = read_pm(f'benchmarks/{filename}', target)
    make_function(transitions, stringifiedStates, "0", goals, cnf_file_name, n)
    cnf_made = time.perf_counter()
    output = subGPMC(cnf_file_name)
    end = time.perf_counter()

    cnf_creation = cnf_made - start
    cnf_solved = end - cnf_made
    total_duration = cnf_creation + cnf_solved
    result = parseGPMCResult(f'{output.stdout}')
    os.remove(cnf_file_name)
    return result, cnf_creation, cnf_solved, total_duration

def runStorm(filename, target, n):
    start = time.perf_counter()
    storm = subprocess.run(['../storm/build/bin/storm', '--prism', f'benchmarks/{filename}', '-prop', f'P=?  [F={n} "{target}" ]'], capture_output=True)
    end = time.perf_counter()
    duration = end - start
    storm_output = f'{storm.stdout}'
    return parseStormResult(storm_output), duration

def runFile(filename, target, n):
    print("storm")
    storm_output, storm_duration = runStorm(filename, target, n)
    print("gpmc old")
    gpmc_output_old, gpmc_creation_old, gpmc_solved_old, gpmc_total_old = runGPMC(filename, target, n, old_order)
    print("gpmc new")
    gpmc_output_new, gpmc_creation_new, gpmc_solved_new, gpmc_total_new = runGPMC(filename, target, n, new_order)
    print("sharp old")
    sharpsat_output_old, sharp_creation_old, sharp_solved_old, sharp_total_old = runSharpSAT(filename, target, n, old_order)
    print("sharp new")
    sharpsat_output_new, sharp_creation_new, sharp_solved_new, sharp_total_new = runSharpSAT(filename, target, n, new_order)
    print("Method, Output, Duration, Cnf creation, Cnf solution\n")
    print(f'Storm, {storm_output}, {storm_duration}\n')
    print(f'GPMC old, {gpmc_output_old}, {gpmc_total_old}, {gpmc_creation_old}, {gpmc_solved_old}\n')
    print(f'GPMC new, {gpmc_output_new}, {gpmc_total_new}, {gpmc_creation_new}, {gpmc_solved_new}\n')
    print(f'Sharp old, {sharpsat_output_old}, {sharp_total_old}, {sharp_creation_old}, {sharp_solved_old}\n')
    print(f'Sharp new, {sharpsat_output_new}, {sharp_total_new}, {sharp_creation_new}, {sharp_solved_new}\n')


#print(runSharpSAT("nand-1-1.pm", "target", 100, old_order))
runFile("nand-1-1.pm", "target", 100)



