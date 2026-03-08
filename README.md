# University Exam Timetabling System (CSP)

A Constraint Satisfaction Problem (CSP) based system that schedules university exams into timeslots and rooms without conflicts, while considering soft preferences like instructor workload fairness and time preferences.

## Problem Definition

Scheduling university exams is a real-world combinatorial optimization problem. Given a set of exams, timeslots, rooms, and instructors, the goal is to find an assignment that satisfies all hard constraints and minimizes penalties from soft constraints.

### CSP Formulation

The problem is formally defined as **CSP = (X, D, C)** where:

- **Variables (X):** Each exam `e` has three decision variables:
  - `X_e ∈ T` → timeslot assignment
  - `Y_e ∈ R` → room assignment  
  - `Z_{e,i} ∈ {0,1}` → invigilator assignment

- **Domains (D):** All available timeslots, rooms, and instructors.

- **Constraints (C):** Six hard constraints (must be satisfied) and three soft constraints (optimization goals).

### Hard Constraints

| ID | Constraint | Formula | Description |
|----|-----------|---------|-------------|
| H1 | No Student Time Conflict | `students(e_a) ∩ students(e_b) ≠ ∅ → X_ea ≠ X_eb` | Two exams sharing a student cannot be in the same timeslot |
| H2 | Room Capacity | `\|students(e)\| ≤ capacity(Y_e)` | Exam's student count must fit in the assigned room |
| H3 | No Room Clash | `Y_ea = Y_eb → X_ea ≠ X_eb` | Same room cannot host two exams at the same timeslot |
| H4 | Lecturer Conflict | `lecturer(e) = i → Z_{e',i} = 0 if X_{e'} = X_e` | PhD instructor's own exam and invigilation cannot overlap |
| H5 | No Double Invigilation | `Σ_{e:X_e=t} Z_{e,i} ≤ 1` | An instructor cannot invigilate two exams in the same slot |
| H6 | Minimum Invigilators | `Σ_i Z_{e,i} ≥ required(e)` | Each exam must have the required number of invigilators |

### Soft Constraints

| ID | Constraint | Description |
|----|-----------|-------------|
| S1 | Instructor Time Preference | Minimize assignments to unwanted timeslots |
| S2 | Workload Fairness | Minimize variance in invigilation load across instructors |
| S3 | Avoid Consecutive Invigilation | Penalize back-to-back invigilation assignments |

### Multi-Objective Function

`F = w1 * penalty1 + w2 * penalty2 + w3 * penalty3`

Where `w1`, `w2`, `w3` are tunable weights for each soft constraint.

## Project Structure

```
csp-exam-timetabling/
├── data/
│   ├── generators/
│   │   └── synthetic.py        # Synthetic instance generator
│   └── instances/              # Generated test instances (JSON)
│
├── src/
│   ├── models/
│   │   ├── domain.py           # Exam, TimeSlot, Room, Instructor, ProblemInstance
│   │   └── solution.py         # Solution dataclass with serialization
│   │
│   ├── constraints/
│   │   ├── hard.py             # H1-H6 full and partial constraint checkers
│   │   └── soft.py             # S1-S3 penalty functions (planned)
│   │
│   ├── solvers/
│   │   ├── backtracking.py     # Basic backtracking solver
│   │   ├── propagation.py      # AC-3 & forward checking (Week 3)
│   │   ├── heuristic.py        # MRV, LCV, degree heuristic (Week 4)
│   │   └── local_search.py     # Simulated annealing / tabu search (Week 6)
│   │
│   └── utils/
│       ├── conflict_graph.py   # Student-based exam conflict graph builder
│       └── io.py               # JSON serialization helpers (planned)
│
├── tests/                      # Unit tests
├── experiments/                # Benchmark results and analysis (Week 8)
├── main.py                    # Entry point — generate, solve, validate
├── requirements.txt
└── README.md
```

## Implementation Details

### Data Model (`src/models/`)

Every mathematical set in the CSP formulation maps directly to a Python dataclass:

- **Exam** → represents `E = {e1, ..., en}` with fields: `id`, `student_ids` (set for O(1) intersection), `lecturer_id`, `required_invigilators`
- **TimeSlot** → represents `T = {t1, ..., tp}` with fields: `id`, `day`, `period` (separate day/period enables consecutive-slot detection for S3)
- **Room** → represents `R = {r1, ..., rm}` with fields: `id`, `capacity`
- **Instructor** → represents `I = {i1, ..., ik}` with fields: `id`, `is_phd` (dual-role flag for H4), `preferences` (dict for S1)
- **ProblemInstance** → aggregates all sets, validates referential integrity (e.g., every exam's lecturer must exist in the instructor list)
- **Solution** → stores decision variables as dicts: `exam_time`, `exam_room`, `assigned_invigilators`

All dataclasses include `__post_init__` validation to catch invalid data early (negative capacities, empty student sets, infeasible slot/room ratios).

### Conflict Graph (`src/utils/conflict_graph.py`)

Precomputes which exam pairs share students, stored as an adjacency list (`dict[int, set[int]]`). This avoids recalculating set intersections during backtracking. The graph is undirected and built once in O(n² · s) time where n = number of exams, s = average student set size.

The conflict graph serves multiple purposes:
- H1 constraint checking (both full and partial)
- Degree heuristic in Week 4 (most-constrained exam first)
- Arc consistency in Week 3

### Constraint Checking (`src/constraints/hard.py`)

Each constraint has two variants:

- **Full check** — validates the entire solution after completion. Used for final verification.
- **Partial check** — validates a single candidate assignment during backtracking. Used at every node of the search tree to prune invalid branches early.

Partial checks are critical for performance: they only examine already-assigned exams, avoiding KeyError on unassigned variables and skipping unnecessary work.

### Backtracking Solver (`src/solvers/backtracking.py`)

A recursive depth-first search over the assignment space:

1. Pick the next unassigned exam (by index order)
2. Try every (timeslot, room) pair
3. Run H1, H2, H3 partial checks — if any fails, skip this pair
4. If all pass, commit the assignment and recurse to the next exam
5. If recursion succeeds, propagate success upward
6. If recursion fails, undo the assignment (backtrack) and try the next pair
7. If no pair works, return failure (trigger backtracking in the caller)

Currently handles timeslot and room assignment (H1, H2, H3). Invigilator assignment (H4, H5, H6) is planned for later phases.

### Synthetic Data Generator (`data/generators/synthetic.py`)

Generates controlled test instances with tunable parameters:

- `n_exams`, `n_timeslots`, `n_rooms`, `n_instructors`, `n_students`
- `periods_per_day` — for realistic day/period structure
- `seed` — reproducibility for academic experiments

Student enrollment uses a student-centric approach: each student is randomly assigned to `k` exams, which naturally creates a realistic conflict structure. Edge cases are handled: exams with no students get a random assignment, and at least one PhD instructor is guaranteed.

Key insight from development: the density of the conflict graph is highly sensitive to the student-to-exam ratio. With too few exams or too many enrollments per student, the graph becomes complete (K_n), making the problem infeasible for the given number of timeslots.

## Usage

### Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

### Example Output

```
Conflict Graph:
{0: {2, 14, 15, 16, 17, 18}, 1: {2, 3, 14, 7}, 2: {0, 1, 10, 15, 17, 18, 19}, ...}

Solution: Solution(exam_time={0: 0, 1: 0, 2: 1, 3: 1, ...}, exam_room={0: 0, 1: 1, 2: 0, ...})

PASSED
```

### Adjusting Parameters

In `main.py`, modify the `generate_instance()` call:

```python
instance = generate_instance(
    n_exams=20,        # number of exams
    n_timeslots=10,    # available timeslots
    n_rooms=4,         # available rooms
    n_instructors=8,   # teaching staff
    n_students=60,     # student population
    seed=42            # for reproducibility
)
```

## Current Status

### Completed (Week 2)
- CSP formulation with 6 hard constraints and 3 soft constraints
- Full data model with validation
- Conflict graph construction
- Synthetic data generator with reproducible seeds
- Basic backtracking solver (timeslot + room assignment)
- Full and partial constraint checking for H1, H2, H3
- Full constraint checking for H4, H5, H6
- Solution validation pipeline

### Planned
- **Week 3:** Constraint propagation (AC-3, forward checking)
- **Week 4:** Heuristics (MRV, degree heuristic, LCV) + large instance testing
- **Week 5:** Visualization (calendar/timetable view)
- **Week 6:** Soft constraints + local search hybrid
- **Week 7:** Web or desktop interface
- **Week 8:** Report + analysis with experimental benchmarks
- **Week 9:** Final presentation

## Known Limitations

- **Backtracking without heuristics** is exponential in the worst case. Dense conflict graphs (many shared students) can make the solver impractical. This is expected and will be addressed in Weeks 3-4.
- **Invigilator assignment** is not yet integrated into the backtracking search. H4, H5, H6 checks exist but are only used for post-solution validation.
- **Conflict graph density** is sensitive to generator parameters. The student-to-exam ratio must be carefully chosen to produce feasible instances.

## Dependencies

- **Python 3.10+**
- **pytest** — unit testing
- **numpy** — statistical analysis for experiments
- **matplotlib** — performance graphs and visualizations
- **networkx** — conflict graph visualization

## Research Context

This project explores a multi-objective CSP framework for university exam timetabling that balances dual-role PhD instructor conflicts with invigilator workload fairness. The novelty lies in the combination of H4 (PhD dual-role conflict) and S2 (workload fairness), which are rarely modeled together in the exam timetabling literature.

## License

Academic use.