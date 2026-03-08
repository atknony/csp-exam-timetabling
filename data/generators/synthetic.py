"""
Module to create syntetic data.
"""

from __future__ import annotations
import random
from src.models.domain import Exam, TimeSlot, Room, Instructor, ProblemInstance


def generate_instance(
    n_exams: int,
    n_timeslots: int,
    n_rooms: int,
    n_instructors: int,
    n_students: int,
    periods_per_day: int = 3,
    seed: int = 42
) -> ProblemInstance:
    """
    A function to generate syntetic data.
    """

    # Set random seed to achieve same randomness on every call
    random.seed(seed)

    # Create timeslots
    timeslots = [TimeSlot(id=i, day=i // periods_per_day, period=i % periods_per_day) for i in range(n_timeslots)]

    # Create rooms
    rooms = [Room(id=i, capacity=random.randint(80, 200)) for i in range(n_rooms)]

    # Create instructors
    instructors = [Instructor(id=i, is_phd=random.random() < 0.35, 
                              preferences={slot.id: random.random() < 0.8 for slot in timeslots}) for i in range(n_instructors)]

    # Create exams (assign each student on random 3-6 exams so it's student based)
    ## Create an empty student id dict to store unique student ids
    exam_student_ids = {exam_id: set() for exam_id in range(n_exams)}

    ## Assign 3-6 random exams to student
    for student_id in range(n_students):
        # Choose 3 to 6 random exams
        exam_choices = random.sample(range(n_exams), k=2)
        
        for exam_id in exam_choices:
            # Assign exam_id to student ids
            exam_student_ids[exam_id].add(student_id)
    
    ## Choose instructors that is phd
    phd_ids = [ins.id for ins in instructors if ins.is_phd]

    ## Ensure to handle edge cases 
    ### Edge case about a random exam doesn't have any student assigned
    for exam_id in range(n_exams):
        if len(exam_student_ids[exam_id]) == 0:
            exam_student_ids[exam_id].add(random.randint(0, n_students - 1))

    ### Edge case about if no one is phd, we must make at least one of them phd to prevent program crash
    if len(phd_ids) == 0:
        instructors[0].is_phd = True
        phd_ids = [instructors[0].id]
    
    # Finally, create exams
    exams = [Exam(id=i, student_ids=exam_student_ids[i], lecturer_id=random.choice(phd_ids), required_invigilators=1) for i in range(n_exams)]

    return ProblemInstance(exams=exams, timeslots=timeslots, rooms=rooms, instructors=instructors)