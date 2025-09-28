from itertools import combinations


def minimal_hitting_sets(conflicts, max_size=3):
    # conflicts: list of sets, each set must be hit by at least one element of the hitting set
    universe = set().union(*conflicts) if conflicts else set()
    for s in range(1, max_size + 1):
        for cand in combinations(universe, s):
            cand_set = set(cand)
            if all(len(cand_set & c) > 0 for c in conflicts):
                yield cand_set
