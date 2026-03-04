# AI Toolkit for Project Managers

Two practical AI tools built by a Technical Project Manager to automate the most time-consuming parts of the PM workflow: **sprint retrospectives** and **release notes**.

![Demo](demo/retro_demo.gif)

## Why I Built This

After years of running Agile teams, I kept running into the same two problems.

**Sprint retrospectives** took hours to prepare properly. Pulling data from Jira, spotting patterns across dozens of tickets, writing up findings in a format the team could actually act on — it always landed on me, usually the night before the meeting. The work wasn't complex, but it was slow, manual, and repetitive.

**Release notes** were a constant translation problem. Developers write commit messages for other developers. Users need something completely different. Someone always had to bridge that gap, and that someone was usually the PM.

These tools automate both. Not to replace PM judgment — but to produce a structured, AI-generated first draft in seconds instead of hours, so the PM can focus on what actually requires their experience.

## Tools

### 1. Sprint Retrospective Analyzer (`scrips/retro_analyzer.py`)

Connects to Jira (or reads from a local JSON file), pulls all issues from a completed sprint, and uses AI to generate a structured retrospective report — ready to paste into Confluence.

**What it produces:**
- Sprint summary with completion rate and goal status
- What went well (data-driven, references real ticket keys)
- What didn't go well (blockers, scope issues, quality problems)
- Key patterns across the sprint (workload distribution, bug trends, carry-overs)
- Concrete action items for the next sprint
- Risk flags that could affect upcoming work

### 2. Release Notes Generator (`scrips/release_notes.py`)

Reads Git commit history or Jira fixVersion issues and generates professional, user-facing release notes grouped by category.

**Three input modes:**
- **Git mode** — reads commit history from a local repo, parses Conventional Commits
- **Jira mode** — queries all issues under a fixVersion
- **File mode** — reads from JSON (useful for demos or CI pipelines)

## Sample Output

### Retrospective Report

```markdown
# Sprint Retrospective: Sprint 42

## Sprint Summary
The team completed 18 of 23 planned issues (78% completion rate). The sprint goal —
shipping the new billing module — was partially achieved. Core functionality was
delivered but CSV export (PROJ-356) was moved to Sprint 43.

## What Went Well
- Bug resolution rate was strong: 7 of 8 bugs closed within the sprint
- PROJ-341 (payment gateway integration) was delivered ahead of schedule
- No unplanned work was added mid-sprint

## What Didn't Go Well
- PROJ-356 was scoped too broadly and carried over
- Two team members carried 60% of the ticket load (unbalanced distribution)
- Three P2 bugs were found in QA that should have been caught earlier

## Action Items
- Break PROJ-356 into smaller sub-tasks before Sprint 43 planning
- Cap any single developer at 30% of sprint capacity during assignment
- Add a pre-QA checklist for features with P2 risk
```

### Release Notes

```markdown
# Release Notes - 2.4.0
**Release Date:** 2026-03-04

## Highlights
This release delivers the new billing module with usage-based pricing, alongside
performance improvements and several stability fixes.

## New Features
- **Usage-based Billing** - Flexible pricing tiers based on actual usage
- **Google SSO Login** - Sign in with your Google account for faster, more secure access

## Bug Fixes
- Fixed session not persisting after browser refresh
- Resolved export timeout on large datasets (10,000+ rows)

## Improvements
- Database query performance improved by 60% on event lookups
```

## Quick Start

```bash
git clone https://github.com/Gil80/pm-ai-toolkit.git
cd pm-ai-toolkit
pip install -r requirements.txt

export AI_API_KEY="your-openai-or-anthropic-key"
export AI_PROVIDER="openai"  # or "anthropic"

# Try the retrospective analyzer with demo data
python scrips/retro_analyzer.py --from-file examples/sprint_example.json

# Try the release notes generator with demo data
python scrips/release_notes.py --from-file examples/commits_example.json --version "2.4.0"
```

## Jira Integration

```bash
export JIRA_BASE_URL="https://yourcompany.atlassian.net"
export JIRA_EMAIL="your-email@company.com"
export JIRA_API_TOKEN="your-token"

# Retrospective for the most recent closed sprint
python scrips/retro_analyzer.py --board-id 42

# Retrospective for a specific sprint
python scrips/retro_analyzer.py --board-id 42 --sprint-id 123

# Release notes for a Jira fixVersion
python scrips/release_notes.py --jira-version "App 3.2" --version "3.2.0"
```

## Git Integration

```bash
# Release notes from commits since last tag
python scrips/release_notes.py --git --since-tag v2.3.0 --version "2.4.0"

# Between two specific tags
python scrips/release_notes.py --git --since-tag v2.3.0 --until-tag v2.4.0 --version "2.4.0"

# Save output to a file
python scrips/release_notes.py --git --since-tag v2.3.0 --version "2.4.0" --output RELEASE_NOTES.md
```

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `AI_API_KEY` | Yes | OpenAI or Anthropic API key |
| `AI_PROVIDER` | No | `openai` (default) or `anthropic` |
| `JIRA_BASE_URL` | For Jira mode | Your Jira instance URL |
| `JIRA_EMAIL` | For Jira mode | Jira account email |
| `JIRA_API_TOKEN` | For Jira mode | Jira API token |

## Built With

- Python 3.10+
- [OpenAI API](https://platform.openai.com/) or [Anthropic API](https://www.anthropic.com/)
- [Jira REST API](https://developer.atlassian.com/cloud/jira/software/rest/intro/)

## Project Structure

```
pm-ai-toolkit/
├── scrips/
│   ├── retro_analyzer.py       # Sprint retrospective generator
│   └── release_notes.py        # Release notes generator
├── examples/
│   ├── sprint_example.json     # Demo sprint data
│   └── commits_example.json    # Demo commit data
├── requirements.txt
├── LICENSE
└── README.md
```

## License

MIT
