"""
Main module to run the algorithms.
"""

from data.generators.synthetic import generate_instance
from src.solvers.cp_solver import solve


if __name__ == '__main__':
    # 1. Generate instance
    instance = generate_instance(n_exams=20, n_timeslots=10, n_rooms=4, n_instructors=8, n_students=60)

    # 2. Solve
    solution = solve(instance=instance)

    # 3. Display results
    if solution:
        print("=== Solution Found ===\n")

        print("Exam  | Timeslot | Room | Invigilators")
        print("------+----------+------+-------------")
        for exam in instance.exams:
            t = solution.exam_time[exam.id]
            r = solution.exam_room[exam.id]
            invig = solution.assigned_invigilators.get(exam.id, set())
            invig_str = ", ".join(str(i) for i in sorted(invig)) if invig else "none"
            print(f"  {exam.id:<4}|    {t:<6}|  {r:<4}| {invig_str}")

        print(f"\nTotal exams: {len(instance.exams)}")
        print(f"Timeslots used: {len(set(solution.exam_time.values()))}/{len(instance.timeslots)}")
        print(f"Rooms used: {len(set(solution.exam_room.values()))}/{len(instance.rooms)}")
    else:
        print("No solution found.")