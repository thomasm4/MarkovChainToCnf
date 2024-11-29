import stormpy
from makecnf_multiplication import makeCNF as new_order
from makecnf_multiplication_old_order import makeCNF as old_order
from import_transitions import readFromPm as read_pm
import time
import subprocess
import re
import os

def runStorm(filename, target, n):
    start = time.perf_counter()
    storm = subprocess.run(['../storm/build/bin/storm', '--prism', f'benchmarks/{filename}', '-prop', f'P=?  [F={n} "{target}" ]'], capture_output=True)
    end = time.perf_counter()
    duration = end - start
    storm_output = f'{storm.stdout}'
    return duration, parseStormResult(storm_output)

def parseStormResult(output):
    return re.search("Result \(for initial states\): ([0-9]*\.[0-9]+)", output).group(1)

def runSharpSAT(filename):
    return subprocess.run(['./sharpSAT', '-decot', '1', '-tmpdir', '.', '-WE', f'{filename}'], capture_output=True, cwd='../sharpsat-td/build')

def runGPMC(filename):
    return subprocess.run(['../GPMC/build/gpmc', '-mode=1', f'{filename}'], capture_output=True)

def parseGPMCResult(output):
    return re.search("exact double prec-sci ([0-9]*\.[0-9]+)", output).group(1)

def runCNF(filename, target, n, make_function, model_count_function):
    cnf_file_name = f'temp_{filename}.cnf'
    start = time.perf_counter()
    transitions, stringifiedStates, goals = read_pm(f'benchmarks/{filename}', target)
    make_function(transitions, stringifiedStates, "0", goals, cnf_file_name, n)
    cnf_made = time.perf_counter()
    output = model_count_function(cnf_file_name)
    end = time.perf_counter()

    #cleanup
    #os.remove(cnf_file_name)

    cnf_creation = cnf_made - start
    cnf_solved = end - cnf_made
    total_duration = cnf_creation + cnf_solved
    print(output.stdout)


def runFile(filename, target, n):
    storm_duration, storm_output = runStorm(filename, target, n)
    print(storm_duration)
    print(storm_output)

runCNF("die.pm", "one", 100, old_order, runSharpSAT)
runFile("nand-1-1.pm", "target", 100)



