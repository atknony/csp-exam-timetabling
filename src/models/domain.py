"""
A module for defining domain dataclasses to solve afterwards.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Exam:
    
    id: int                         # exam id
    student_ids: set[int]           # id's of students
    lecturer_id: int                # id of lecturer
    required_invigilators: int      # The amount of invigilators required

    # Edge case detection
    def __post_init__(self):
        if self.id < 0:
            raise ValueError(f"Exam id must be non-negative, got {self.id}.")
        if self.lecturer_id < 0:
            raise ValueError(f"Lecturer id must be non-negative, got {self.lecturer_id}.")
        if self.required_invigilators <= 0:
            raise ValueError("At least one invigilator is required.")
        if not self.student_ids:
            raise ValueError("An exam must have at least one student.")
            

@dataclass
class TimeSlot:

    id: int                         # timeslot id
    day: int                        # number of day. (e.g monday = 0, tuesday = 1... etc.)
    period: int                     # number of period. (e.g morning = 0, noon = 1 etc.)

    # Edge case detection
    def __post_init__(self):
        if self.day < 0 or self.period < 0:
            raise ValueError("Day and/or period should be a positive integer.")


@dataclass
class Room:

    id: int                         # room id
    capacity: int                   # amount of room capacity

    # Edge case detection
    def __post_init__(self):
        if self.capacity <= 0:
            raise ValueError(f"Insufficient or invalid capacity for room {self.id}")


@dataclass
class Instructor:

    id: int                         # instructor id
    is_phd: bool                    # If true, the instructor can both give lectures and be invigilator
    preferences: dict[int, bool]    # key is a timeslot_id where value is if the instructor wants that slot or not.
                                    # pref = 1, penalty = 0 for value True. -- pref = 0, penalty = 1 for value False.

    # Edge case detection
    def __post_init__(self):
        if len(self.preferences) == 0:
            raise ValueError("Instructors should have preferences about timeslots.")


@dataclass
class ProblemInstance:

    exams: list[Exam]
    timeslots: list[TimeSlot]
    rooms: list[Room]
    instructors: list[Instructor]

    # O(1) lookup indexes — built once, used everywhere 
    _exam_index: dict[int, Exam] = field(default_factory=dict, init=False, repr=False)
    _room_index: dict[int, Room] = field(default_factory=dict, init=False, repr=False)
    _timeslot_index: dict[int, TimeSlot] = field(default_factory=dict, init=False, repr=False)
    _instructor_index: dict[int, Instructor] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self):
        # Validation
        if not (self.exams and self.timeslots and self.rooms and self.instructors):
            raise ValueError("All fields must be non-empty.")
        if len(self.timeslots) * len(self.rooms) < len(self.exams):
            raise ValueError("Insufficient timeslot-room combinations for all exams.")

        # Build indexes
        self._exam_index = {e.id: e for e in self.exams}
        self._room_index = {r.id: r for r in self.rooms}
        self._timeslot_index = {t.id: t for t in self.timeslots}
        self._instructor_index = {i.id: i for i in self.instructors}

        # Cross-reference validation (now O(1) per lookup)
        for exam in self.exams:
            if exam.lecturer_id not in self._instructor_index:
                raise ValueError(
                    f"Exam {exam.id}: lecturer {exam.lecturer_id} not registered."
                )

    # Accessor API — constraint checkers call these, never raw lists
    def get_exam(self, exam_id: int) -> Exam:
        try:
            return self._exam_index[exam_id]
        except KeyError:
            raise KeyError(f"exam_id={exam_id} not found in ProblemInstance.")

    def get_room(self, room_id: int) -> Room:
        try:
            return self._room_index[room_id]
        except KeyError:
            raise KeyError(f"room_id={room_id} not found in ProblemInstance.")

    def get_timeslot(self, timeslot_id: int) -> TimeSlot:
        try:
            return self._timeslot_index[timeslot_id]
        except KeyError:
            raise KeyError(f"timeslot_id={timeslot_id} not found in ProblemInstance.")

    def get_instructor(self, instructor_id: int) -> Instructor:
        try:
            return self._instructor_index[instructor_id]
        except KeyError:
            raise KeyError(f"instructor_id={instructor_id} not found in ProblemInstance.")

    def __repr__(self):
        return (
            f"ProblemInstance(exams={len(self.exams)}, timeslots={len(self.timeslots)}, "
            f"rooms={len(self.rooms)}, instructors={len(self.instructors)})"
        )