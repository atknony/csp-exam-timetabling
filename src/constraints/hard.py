"""
Hard constraint checkers for the Exam Timetabling CSP.

"""

from typing import Dict, Set
from src.models.solution import Solution
from src.models.domain import ProblemInstance

# Type alias
ConflictGraph = Dict[int, Set[int]]

# H1 - No Student Time Conflict
def check_h1(
    exam_id: int,
    timeslot_id: int,
    solution: Solution,
    conflict_graph: ConflictGraph,
) -> bool:
    """"
    Return True if assigning `exam_id` to `timeslot_id` satisfies H1.

    Checks that no already-assigned neighbor in the conflict graph
    occupies the same timeslot.  Only *assigned* neighbors are tested,
    so this is safe to call incrementally during backtracking.

    Args:
        exam_id:        The exam being (tentatively) assigned.
        timeslot_id:    The timeslot under evaluation.
        solution:       Current (partial) solution state.
        conflict_graph: Pre-built adjacency list from build_conflict_graph().

    Returns:
        True  → assignment is H1-feasible.
        False → at least one conflicting exam shares this timeslot.

    Raises:
        KeyError: If exam_id is absent from conflict_graph, signalling a
                  mismatch between the graph and the problem instance.
    """
    if exam_id not in conflict_graph:
        raise KeyError(
            f"exam_id={exam_id} not found in conflict_graph. "
            "Ensure build_conflict_graph() was called on the same exam list."
        )

    assigned_time = solution.exam_time  # single local binding — avoids repeated attr lookup

    return all(
        assigned_time.get(neighbor_id) != timeslot_id
        for neighbor_id in conflict_graph[exam_id]
    )

# H2 - Room Capacity Constraint
def check_h2(
    exam_id: int,
    room_id: int,
    instance: ProblemInstance,
) -> bool:
    """
    Return True iff assigning exam_id to room_id satisfies H2.

    Raises:
        KeyError: If exam_id or room_id is absent from the instance.
    """
    exam = instance.get_exam(exam_id)    # O(1)
    room = instance.get_room(room_id)    # O(1)
    return len(exam.student_ids) <= room.capacity