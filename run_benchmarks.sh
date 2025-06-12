#!/bin/bash

ls benchmarks | parallel "python3 dtmc_benchmarks.py {} > benchmark_output/{}.txt"

# pomdp benchmarks
#ls mdp_benchmarks | parallel "python3 mdp_benchmarks.py {} > mdp_benchmark_output/{}.txt"

