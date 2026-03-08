"""
Module for defining hard contraints (H1 - H6) fully and partially.

Full check: Validates the ENTIRE solution after all assignments are made.
Partial check: Validates a SINGLE assignment during backtracking (before committing it).

H1 ==>  No Student Time Conflict:          Two exams sharing a student cannot be in the same timeslot.
H2 ==>  Room Capacity:                     Exam's student count must not exceed the assigned room's capacity.
H3 ==>  No Room Clash:                     Two exams in the same room cannot be in the same timeslot.
H4 ==>  Lecturer Conflict (Dual-Role PhD): A PhD instructor's own exam and their invigilation cannot overlap.
H5 ==>  No Double Invigilation:            An instructor cannot invigilate two exams in the same timeslot.
H6 ==>  Minimum Invigilators Per Exam:     Each exam must have at least the required number of invigilators.
"""

from __future__ import annotations
from src.models.domain import ProblemInstance
from src.models.solution import Solution


# ===================== H1: No Student Time Conflict =====================

def check_h1(instance: ProblemInstance, solution: Solution, conflict_graph: dict[int, set[int]]) -> bool:
    """
    Full check for H1: students(e_a) ∩ students(e_b) ≠ ∅ → X_ea ≠ X_eb

    Iterates over every conflicting exam pair in the conflict graph.
    If two conflicting exams are assigned to the same timeslot, H1 is violated.
    The (exam_a < exam_b) guard ensures each pair is checked only once since
    the graph is undirected (A→B and B→A both exist).
    """

    for exam_a, neighbors in conflict_graph.items():
        for exam_b in neighbors:
            if exam_a < exam_b:
                if solution.exam_time[exam_a] == solution.exam_time[exam_b]:
                    print(f"H1 violated: exams {exam_a} and {exam_b} share students but are both assigned to timeslot {solution.exam_time[exam_a]}")
                    return False
                
    return True


def check_h1_partial(instance: ProblemInstance, solution: Solution, conflict_graph: dict[int, set[int]], exam_id: int, timeslot_id: int) -> bool:
    """
    Partial check for H1: "If I assign exam_id to timeslot_id, does it conflict 
    with any already-assigned exam that shares students?"

    Looks up exam_id's neighbors in the conflict graph, then checks whether
    any of those neighbors are already assigned to the candidate timeslot_id.
    Unassigned neighbors (not yet in solution.exam_time) are safely skipped.
    """

    neighbors = conflict_graph[exam_id]

    for neighbor_id in neighbors:
        if neighbor_id in solution.exam_time:
            if solution.exam_time[neighbor_id] == timeslot_id:
                return False
            
    return True


# ===================== H2: Room Capacity =====================

def check_h2(instance: ProblemInstance, solution: Solution, conflict_graph: dict[int, set[int]]) -> bool:
    """
    Full check for H2: |students(e)| ≤ capacity(Y_e)

    For every exam, verifies that the number of registered students does not
    exceed the capacity of the room assigned to that exam.
    Uses a room lookup dict to avoid repeated list traversal.
    """

    rooms_lookup = {room.id: room for room in instance.rooms}

    for exam in instance.exams:
        room_id = solution.exam_room[exam.id]
        capacity = rooms_lookup[room_id].capacity
        student_count = len(exam.student_ids)

        if student_count > capacity:
            print(f"H2 violated: exam {exam.id} has {student_count} students but room {room_id} only holds {capacity}")
            return False
        
    return True


def check_h2_partial(instance: ProblemInstance, solution: Solution, exam_id: int, room_id: int) -> bool:
    """
    Partial check for H2: "If I assign exam_id to room_id, will the students fit?"

    Compares the exam's student count against the candidate room's capacity.
    No need to check other exams — this is a per-exam constraint.
    """

    if len(instance.exams[exam_id].student_ids) > instance.rooms[room_id].capacity:
        return False
        
    return True


# ===================== H3: No Room Clash =====================

def check_h3(instance: ProblemInstance, solution: Solution, conflict_graph: dict[int, set[int]]) -> bool:
    """
    Full check for H3: Y_ea = Y_eb → X_ea ≠ X_eb

    Checks every pair of exams. If two exams are assigned to the same room,
    they must be in different timeslots. Unlike H1, there is no conflict graph
    here — any two exams can potentially clash on a room.
    """

    for i in range(len(instance.exams)):
        for j in range(i + 1, len(instance.exams)):
            exam_a_id = instance.exams[i].id
            exam_b_id = instance.exams[j].id

            if solution.exam_room[exam_a_id] == solution.exam_room[exam_b_id]:
                if solution.exam_time[exam_a_id] == solution.exam_time[exam_b_id]:
                    print(f"H3 violated: exams {exam_a_id} and {exam_b_id} are both in room {solution.exam_room[exam_a_id]} at timeslot {solution.exam_time[exam_a_id]}")
                    return False
                
    return True


def check_h3_partial(instance: ProblemInstance, solution: Solution, exam_id: int, timeslot_id: int, room_id: int) -> bool:
    """
    Partial check for H3: "If I assign exam_id to (timeslot_id, room_id),
    is that room already occupied at that timeslot by another exam?"

    Iterates only over already-assigned exams to avoid KeyError on
    exams that haven't been placed yet.
    """

    for assigned_exam_id, assigned_slot in solution.exam_time.items():
        if assigned_slot == timeslot_id and solution.exam_room[assigned_exam_id] == room_id:
            return False
        
    return True


# ===================== H4: Lecturer Conflict (Dual-Role PhD) =====================

def check_h4(instance: ProblemInstance, solution: Solution, conflict_graph: dict[int, set[int]]) -> bool:
    """
    Full check for H4: lecturer(e) = i → Z_e',i = 0 if X_e' = X_e

    A PhD instructor who lectures exam e cannot be assigned as an invigilator
    for another exam e' that runs in the same timeslot. This prevents a single
    person from being required in two places at once.
    Only full check is needed for now since invigilator assignment comes later.
    """

    for exam in instance.exams:
        lecturer_id = exam.lecturer_id
        timeslot_id = solution.exam_time[exam.id]

        # Check all other exams in the same timeslot
        for other_exam_id, other_slot in solution.exam_time.items():
            if other_exam_id != exam.id and other_slot == timeslot_id:
                # If the other exam has invigilators assigned, check whether
                # this exam's lecturer is among them — that would be a conflict
                if other_exam_id in solution.assigned_invigilators:
                    if lecturer_id in solution.assigned_invigilators[other_exam_id]:
                        print(f"H4 violated: instructor {lecturer_id} lectures exam {exam.id} but is also invigilating exam {other_exam_id} in the same timeslot {timeslot_id}")
                        return False
                
    return True


# ===================== H5: No Double Invigilation =====================

def check_h5(instance: ProblemInstance, solution: Solution, conflict_graph: dict[int, set[int]]) -> bool:
    """
    Full check for H5: Σ_{e: X_e = t} Z_{e,i} ≤ 1

    An instructor can invigilate at most one exam per timeslot.
    First groups exams by their timeslot, then within each timeslot checks
    whether any instructor appears in more than one exam's invigilator set.
    Uses a 'seen' set per timeslot to detect duplicates efficiently.
    Only full check is needed for now since invigilator assignment comes later.
    """

    # Step 1: Group exams by timeslot → {timeslot_id: [exam_id, exam_id, ...]}
    time_to_exam = dict()
    for exam_id, timeslot_id in solution.exam_time.items():
        if timeslot_id not in time_to_exam:
            time_to_exam[timeslot_id] = []
        time_to_exam[timeslot_id].append(exam_id)

    # Step 2: For each timeslot, check that no instructor appears twice
    for slot in time_to_exam:
        seen = set()
        for exam_id in time_to_exam[slot]:
            if exam_id in solution.assigned_invigilators:
                for instructor_id in solution.assigned_invigilators[exam_id]:
                    if instructor_id in seen:
                        print(f"H5 violated: instructor {instructor_id} is assigned to multiple exams in timeslot {slot}")
                        return False
                    seen.add(instructor_id)

    return True


# ===================== H6: Minimum Invigilators Per Exam =====================

def check_h6(instance: ProblemInstance, solution: Solution, conflict_graph: dict[int, set[int]]) -> bool:
    """
    Full check for H6: Σ_i Z_{e,i} ≥ required(e)

    Every exam must have at least as many invigilators as specified by
    its required_invigilators field. An exam with no entry in
    assigned_invigilators is treated as having zero invigilators.
    Only full check is needed for now since invigilator assignment comes later.
    """

    for exam in instance.exams:
        if exam.id in solution.assigned_invigilators:
            assigned_count = len(solution.assigned_invigilators[exam.id])
            if assigned_count < exam.required_invigilators:
                print(f"H6 violated: exam {exam.id} has {assigned_count} invigilators but requires {exam.required_invigilators}")
                return False
        else:
            print(f"H6 violated: exam {exam.id} has no invigilators assigned (requires {exam.required_invigilators})")
            return False

    return True