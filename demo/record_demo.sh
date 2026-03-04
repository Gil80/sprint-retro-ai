#!/usr/bin/env bash
# Simulates the retro analyzer demo for terminal recording

PS1="$ "
clear

# Simulate typing and output with delays
_type() {
  echo -n "$ "
  local text="$1"
  for ((i=0; i<${#text}; i++)); do
    echo -n "${text:$i:1}"
    sleep 0.04
  done
  echo
}

sleep 0.5

_type "cd ~/projects/sprint-retro-ai"
sleep 0.4

_type "ls"
echo "LICENSE    README.md  demo/  examples/  requirements.txt  scrips/"
sleep 0.8

_type "python3 scrips/retro_analyzer.py --from-file examples/sprint_example.json"
sleep 0.3

echo "[INFO] Loading sprint data from examples/sprint_example.json" >&2
sleep 0.5
echo "[INFO] Sending data to AI for analysis..." >&2
sleep 2

cat << 'EOF'

# Sprint Retrospective: Sprint 42

## Sprint Summary
The team completed 18 of 23 planned issues (78% completion rate). The sprint
goal — delivering the new billing module — was partially achieved. Core
functionality shipped on time, but CSV export (PROJ-356) was moved to Sprint 43.

## What Went Well
- Bug resolution was strong: 7 of 8 bugs closed within the sprint
- PROJ-341 (payment gateway) delivered ahead of schedule
- No unplanned work added mid-sprint — scope stayed stable

## What Didn't Go Well
- PROJ-356 scoped too broadly, carried over to Sprint 43
- Two team members carried 60% of the ticket load
- Three P2 bugs found in QA that should have been caught earlier

## Action Items
- Break PROJ-356 into sub-tasks before Sprint 43 planning (owner: PM)
- Cap any single developer at 30% of sprint capacity during assignment
- Add pre-QA checklist for features with P2 risk (owner: Tech Lead)

## Risk Flags
- PROJ-356 carry-over adds scope pressure to Sprint 43
- Unbalanced workload is a burnout risk — address in 1:1s
EOF

sleep 3
