#!/usr/bin/env python3
"""
Mock script that simulates retro_analyzer.py output for demo purposes.
Prints realistic output with a short delay to look like a real AI call.
"""
import sys
import time

print("[INFO] Loading sprint data from examples/sprint_example.json", file=sys.stderr)
time.sleep(0.5)
print("[INFO] Sending data to AI for analysis...", file=sys.stderr)
time.sleep(1.5)

print("""
# Sprint Retrospective: Sprint 42

## Sprint Summary
The team completed 18 of 23 planned issues (78% completion rate). The sprint goal —
delivering the new billing module — was partially achieved. Core functionality
shipped on time, but CSV export (PROJ-356) was moved to Sprint 43 due to scope.

## What Went Well
- Bug resolution was strong: 7 of 8 bugs closed within the sprint
- PROJ-341 (payment gateway integration) delivered ahead of schedule
- No unplanned work was added mid-sprint — scope stayed stable
- Team communication in standups improved noticeably this sprint

## What Didn't Go Well
- PROJ-356 was scoped too broadly and carried over to Sprint 43
- Two team members (Alex, Dana) carried 60% of the ticket load
- Three P2 bugs were discovered in QA that should have been caught in dev review
- Estimation was off on PROJ-349 — took 3x the original story points

## Key Patterns & Observations
- Workload distribution is uneven: top 2 devs close 60% of tickets consistently
- Bug-to-feature ratio is trending up (3 sprints in a row) — possible tech debt signal
- Carry-over items average 2 per sprint — suggests consistent over-commitment in planning

## Action Items
- Break PROJ-356 into sub-tasks before Sprint 43 planning (owner: PM)
- Cap any single developer at 30% of sprint capacity during assignment
- Add a pre-QA checklist for features with P2 risk (owner: Tech Lead)
- Schedule a tech debt grooming session before Sprint 44 planning
- Re-estimate PROJ-349 remainder with the full team, not just the assignee

## Risk Flags
- PROJ-356 carry-over adds scope pressure to Sprint 43 — review capacity before planning
- Unbalanced workload is a burnout risk for Alex and Dana — address in 1:1s
- Rising bug trend may indicate insufficient code review coverage
""")
