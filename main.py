"""
Main module to run the algorithms.
"""

from data.generators.synthetic import generate_instance
from src.utils.conflict_graph import build_conflict_graph
from src.solvers.backtracking import solver
from src.constraints.hard import check_h1, check_h2, check_h3


if __name__ == '__main__':
    # 1. Generate instance
    instance = generate_instance(n_exams=15, n_timeslots=6, n_rooms=5, n_instructors=8, n_students=300)

    # 2. Create conflict graph and print it
    conflict_graph = build_conflict_graph(exams=instance.exams)
    print("Conflict Graph:")
    print(conflict_graph)

    # 3. Create solver
    solution = solver(instance=instance)

    # 4. Print out if there's a solution
    if solution:
        print(f"Solution: {solution}")

        # 5. Verify with full checks
        h1 = check_h1(instance=instance, solution=solution, conflict_graph=conflict_graph)
        h2 = check_h2(instance=instance, solution=solution, conflict_graph=conflict_graph)
        h3 = check_h3(instance=instance, solution=solution, conflict_graph=conflict_graph)

        if h1 and h2 and h3:
            print("PASSED")
        else:
            print("FAILED")
    else:
        print("No solution.")
