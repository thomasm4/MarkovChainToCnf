# MarkovChainToCnf

This repo contains an algorithm to encode bounded reachability of DTMCs, MDPs and POMDPs as a CNF formula, which can be used with model counters to solve bounded reachability.

DTMCs can be solved using `makecnf_multiplication.py` or `makecnf_multiplication_old_order.py`, and the CNF output can be used in most model counters.

MDPs and POMDPs can both be solved using `makecnf_mdp.py`, the CNF output is only usable with the d4Max model counter as this is the only model counter that supports maximizing the model count and uses custom notation in the CNF file.
The file supports

All of these files have a `-h` or `--help` parameter available to explain what paremeters should be given when calling these files.

## Requirements
Although the required packages are given in the `requirements.txt` file which can be used to automatically import most packages using `pip`, it is not recommended as some requirements are not directly available.
Instead it is recommended to manaully install stormpy and all its requirements following their installation guide: https://moves-rwth.github.io/stormpy/installation.html

## Legacy
The legacy folder contains older and less efficient versions of the algorithm for DTMCs.
These are mostly still here to show the process of how the final algorithm was build.
If you still want to run them you should put the file back in the main folder as some of them require the `import_transitions.py` file.
They also require the package PySat which was dropped in later version to allow manual optimizations: https://pysathq.github.io/installation/
