"""
Module for building conflict graph.
"""

from __future__ import annotations
from src.models.domain import Exam


def build_conflict_graph(exams: list[Exam]) -> dict[int, set[int]]:
    """
    A function for building conflict graph between exams.

    Returns an adjacency list. (For every exam id, the set of conflicted exam id's with that exam id)
    """

    # Define a set to store conflicts
    conflicts = {exam.id: set() for exam in exams}

    # Iterate trough exams to build conflict graph (Iterate trough 2 sample exams)
    for i in range(len(exams)):
        for j in range(i + 1, len(exams)):
            # Check if there is a conflict
            if exams[i].student_ids & exams[j].student_ids:
                # Add adjacency to the conflicts
                conflicts[exams[i].id].add(exams[j].id)
                conflicts[exams[j].id].add(exams[i].id)
            
    return conflicts