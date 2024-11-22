import stormpy
from makecnf_multiplication import makeCNF as new_order
from makecnf_multiplication_old_order import makeCNF as old_order
import time
import subprocess

def runStorm(filename, n):
    return subprocess.run(['../storm/build/bin/storm' ,'--prism' ,f'benchmarks/{filename}', '-prop', f'P=?  [F={n} "target" ]'], capture_output=True)

def parseStormResult(output):
    #TODO
    return None

def runFile(filename, n):
    start = time.perf_counter()
    storm = runStorm(filename, n)
    end = time.perf_counter()
    duration = end - start
    #print(storm.stdout)
    print(duration)

runFile("nand-1-1.pm", 100)



