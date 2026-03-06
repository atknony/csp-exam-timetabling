"""
A module for defining the Solution dataclass.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from .domain import ProblemInstance


@dataclass
class Solution:

    exam_time: dict[int, int]               # X_e: exam_id → timeslot_id
    exam_room: dict[int, int]               # Y_e: exam_id → room_id
    assigned_invigilators: dict[int, set[int]]  # Z_e: exam_id → {instructor_ids}

    # ── Secondary indexes — maintained incrementally, never iterated for checks ──
    # O(1) room clash detection for H3
    _occupied_slots: set[tuple[int, int]] = field(
        default_factory=set, init=False, repr=False
    )
    # O(1) instructor availability detection for H5/H6
    _instructor_timeslots: dict[int, set[int]] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self):
        if self.exam_time.keys() != self.exam_room.keys():
            raise ValueError(
                "exam_time and exam_room must cover identical exam sets."
            )
        # Rebuild indexes from any pre-populated assignments
        for exam_id, timeslot_id in self.exam_time.items():
            room_id = self.exam_room[exam_id]
            self._occupied_slots.add((timeslot_id, room_id))

    # ── Assignment API — the solver MUST use these, never mutate dicts directly ──

    def assign(self, exam_id: int, timeslot_id: int, room_id: int) -> None:
        """
        Assign an exam to a timeslot and room. Updates all indexes atomically.
        Call check_h3 BEFORE calling this.
        """
        self.exam_time[exam_id] = timeslot_id
        self.exam_room[exam_id] = room_id
        self._occupied_slots.add((timeslot_id, room_id))

    def unassign(self, exam_id: int) -> None:
        """
        Retract an assignment during backtracking. Updates all indexes atomically.
        """
        timeslot_id = self.exam_time.pop(exam_id, None)
        room_id = self.exam_room.pop(exam_id, None)
        if timeslot_id is not None and room_id is not None:
            self._occupied_slots.discard((timeslot_id, room_id))

    def assign_invigilators(self, exam_id: int, instructor_ids: set[int]) -> None:
        """Assign invigilators and update the instructor-timeslot index."""
        self.assigned_invigilators[exam_id] = instructor_ids
        timeslot_id = self.exam_time.get(exam_id)
        if timeslot_id is not None:
            for iid in instructor_ids:
                self._instructor_timeslots.setdefault(iid, set()).add(timeslot_id)

    def is_slot_occupied(self, timeslot_id: int, room_id: int) -> bool:
        """O(1) H3 check. Use this instead of iterating exam_time."""
        return (timeslot_id, room_id) in self._occupied_slots

    def is_instructor_busy(self, instructor_id: int, timeslot_id: int) -> bool:
        """O(1) H5/H6 check. Returns True if instructor is already assigned."""
        return timeslot_id in self._instructor_timeslots.get(instructor_id, set())

    # ── Completeness & serialization (unchanged logic, cleaner style) ──────────

    def is_complete(self, instance: ProblemInstance) -> bool:
        """Return True iff every exam has a time, room, and invigilators assigned."""
        for exam in instance.exams:
            if exam.id not in self.exam_time:
                return False
            if exam.id not in self.assigned_invigilators:
                return False
        return True

    def to_dict(self) -> dict:
        return {
            "exam_time": {str(k): v for k, v in self.exam_time.items()},
            "exam_room": {str(k): v for k, v in self.exam_room.items()},
            "assigned_invigilators": {
                str(k): list(v) for k, v in self.assigned_invigilators.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> Solution:
        return cls(
            exam_time={int(k): v for k, v in data["exam_time"].items()},
            exam_room={int(k): v for k, v in data["exam_room"].items()},
            assigned_invigilators={
                int(k): set(v) for k, v in data["assigned_invigilators"].items()
            },
        )

    def __repr__(self):
        return (
            f"Solution(assigned={len(self.exam_time)}, "
            f"occupied_slots={len(self._occupied_slots)})"
        )