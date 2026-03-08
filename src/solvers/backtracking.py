"""
Module for implementing backtracking algorithm
"""

from src.models.domain import ProblemInstance
from src.models.solution import Solution
from src.utils.conflict_graph import build_conflict_graph
from src.constraints.hard import check_h1_partial, check_h2_partial, check_h3_partial


def backtrack(instance: ProblemInstance, solution: Solution, conflict_graph: dict[int, set[int]], exam_index: int) -> bool:
    """
    Function to backtrack in case of encountering a conflict.
    """
    
    # Check the base case which is is every exam assigned
    if exam_index == len(instance.exams):
        return True
    
    # Store the next exam
    next_exam = instance.exams[exam_index]

    # Iterate trough timeslots and rooms
    for timeslot in instance.timeslots:
        for room in instance.rooms:
            # Check every (timeslot, room) pairs constraints using h1, h2, h3 partial checker functions (partial to avoid KeyError)
            if (check_h1_partial(instance, solution, conflict_graph, next_exam.id, timeslot.id) and
                check_h2_partial(instance, solution, next_exam.id, room.id) and
                check_h3_partial(instance, solution, next_exam.id, timeslot.id, room.id)):
                # Assign the solution
                solution.exam_time[next_exam.id] = timeslot.id
                solution.exam_room[next_exam.id] = room.id

                # Check if the backtrack avoided conflicts
                if backtrack(instance, solution, conflict_graph, exam_index + 1):
                    return True
                else:
                    # Delete the pair and try again
                    del solution.exam_time[next_exam.id]
                    del solution.exam_room[next_exam.id]
    
    return False


def solver(instance: ProblemInstance) -> Solution | None:
    """
    The main function that called from outside. Allows the recursive usage of backtrack function.
    """

    # Build the conflict graph
    conflict_graph = build_conflict_graph(exams=instance.exams)

    # Create the solution instance
    solution = Solution(exam_time={}, exam_room={}, assigned_invigilators={})

    # Call the backtrack function
    found = backtrack(instance, solution, conflict_graph, 0)
    if not found:
        return None

    return solution