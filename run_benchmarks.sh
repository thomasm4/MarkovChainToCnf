#!/bin/bash

ls benchmarks | parallel "python3 dtmc_benchmarks.py {} > benchmark_output/{}.txt"
