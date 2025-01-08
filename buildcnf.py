def buildcnf(clauses, highest_number, filename):
    f = open(filename, "w")
    f.write(f'p cnf {highest_number} {len(clauses)}\n')
    for clause in clauses:
        f.write(f'{" ".join(str(x) for x in clause)} 0\n')