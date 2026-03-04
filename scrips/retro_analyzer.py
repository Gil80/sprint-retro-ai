#!/usr/bin/env python3
"""
Sprint Retrospective AI Analyzer
---------------------------------
Connects to Jira REST API (or reads from a local JSON file),
pulls completed sprint data, and uses an AI model to generate
a structured retrospective summary.

Output: Markdown report ready to paste into Confluence.

Author: Gil Levy
License: MIT
"""

import argparse
import json
import os
import sys
from datetime import datetime

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "")          # e.g. https://yourcompany.atlassian.net
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")                 # OpenAI or Anthropic key
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")         # "openai" or "anthropic"

# ---------------------------------------------------------------------------
# Jira client
# ---------------------------------------------------------------------------

class JiraClient:
    """Lightweight Jira REST API wrapper."""

    def __init__(self, base_url: str, email: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (email, token)
        self.session.headers.update({"Accept": "application/json"})

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}/rest/agile/1.0{path}"
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_boards(self) -> list[dict]:
        """List all Scrum boards."""
        data = self._get("/board", params={"type": "scrum"})
        return data.get("values", [])

    def get_sprints(self, board_id: int, state: str = "closed") -> list[dict]:
        """List sprints for a board filtered by state."""
        data = self._get(f"/board/{board_id}/sprint", params={"state": state})
        return data.get("values", [])

    def get_sprint_issues(self, sprint_id: int) -> list[dict]:
        """Return all issues in a sprint with relevant fields."""
        issues = []
        start = 0
        while True:
            data = self._get(
                f"/sprint/{sprint_id}/issue",
                params={
                    "startAt": start,
                    "maxResults": 50,
                    "fields": "summary,status,issuetype,priority,assignee,comment,resolution,labels",
                },
            )
            issues.extend(data.get("issues", []))
            if start + 50 >= data.get("total", 0):
                break
            start += 50
        return issues


def flatten_sprint_data(sprint: dict, issues: list[dict]) -> dict:
    """Convert raw Jira data into a clean dict for the AI prompt."""
    completed = []
    not_completed = []
    bugs = []
    comments_all: list[str] = []

    for issue in issues:
        fields = issue.get("fields", {})
        summary = fields.get("summary", "")
        status = fields.get("status", {}).get("name", "")
        issue_type = fields.get("issuetype", {}).get("name", "")
        priority = fields.get("priority", {}).get("name", "")
        assignee_data = fields.get("assignee") or {}
        assignee = assignee_data.get("displayName", "Unassigned")
        resolution = (fields.get("resolution") or {}).get("name", "Unresolved")
        labels = fields.get("labels", [])

        entry = {
            "key": issue["key"],
            "summary": summary,
            "type": issue_type,
            "status": status,
            "priority": priority,
            "assignee": assignee,
            "resolution": resolution,
            "labels": labels,
        }

        if status.lower() in ("done", "closed", "resolved"):
            completed.append(entry)
        else:
            not_completed.append(entry)

        if issue_type.lower() == "bug":
            bugs.append(entry)

        # Collect last 3 comments per issue
        comment_data = fields.get("comment", {}).get("comments", [])
        for c in comment_data[-3:]:
            body = c.get("body", "")
            if isinstance(body, dict):
                # Atlassian Document Format - extract text nodes
                texts = []
                for content_block in body.get("content", []):
                    for item in content_block.get("content", []):
                        if item.get("type") == "text":
                            texts.append(item.get("text", ""))
                body = " ".join(texts)
            if body.strip():
                comments_all.append(f"[{issue['key']}] {body.strip()[:300]}")

    return {
        "sprint_name": sprint.get("name", "Unknown Sprint"),
        "sprint_goal": sprint.get("goal", ""),
        "start_date": sprint.get("startDate", ""),
        "end_date": sprint.get("endDate", ""),
        "total_issues": len(issues),
        "completed_count": len(completed),
        "not_completed_count": len(not_completed),
        "bug_count": len(bugs),
        "completed": completed,
        "not_completed": not_completed,
        "bugs": bugs,
        "sample_comments": comments_all[:30],  # cap to keep prompt size manageable
    }


# ---------------------------------------------------------------------------
# AI analysis
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an experienced Agile Coach and Scrum Master. 
Analyze the sprint data provided and produce a structured retrospective report.

Your report MUST follow this exact Markdown structure:

# Sprint Retrospective: {sprint_name}

## Sprint Summary
Brief 2-3 sentence overview including completion rate and goal status.

## What Went Well
- List 3-5 specific positive observations based on the data

## What Didn't Go Well
- List 3-5 specific issues, blockers, or concerns based on the data

## Key Patterns & Observations
- Identify patterns: workload distribution, bug trends, priority handling
- Note any scope changes or carry-over items

## Action Items
- List 3-5 concrete, actionable improvements for the next sprint
- Each action should be specific and assignable

## Risk Flags
- Flag any items that could affect the next sprint

Be data-driven. Reference specific ticket keys when relevant.
Do not invent data that is not in the input.
Keep the tone professional but direct."""


def analyze_with_openai(sprint_data: dict) -> str:
    """Call OpenAI chat completions API."""
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o",
            "temperature": 0.4,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(sprint_data, indent=2)},
            ],
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def analyze_with_anthropic(sprint_data: dict) -> str:
    """Call Anthropic messages API."""
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": AI_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2048,
            "system": SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": json.dumps(sprint_data, indent=2)},
            ],
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def analyze_sprint(sprint_data: dict) -> str:
    """Route to the configured AI provider."""
    if AI_PROVIDER == "anthropic":
        return analyze_with_anthropic(sprint_data)
    return analyze_with_openai(sprint_data)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate AI-powered sprint retrospective reports from Jira data."
    )
    parser.add_argument(
        "--from-file",
        type=str,
        help="Path to a JSON file with sprint data (skip Jira API call).",
    )
    parser.add_argument(
        "--board-id",
        type=int,
        help="Jira board ID to pull sprints from.",
    )
    parser.add_argument(
        "--sprint-id",
        type=int,
        help="Specific sprint ID to analyze. If omitted, uses the most recent closed sprint.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path. Defaults to stdout.",
    )
    parser.add_argument(
        "--export-data",
        type=str,
        default=None,
        help="Export the flattened sprint data to JSON (useful for debugging or demo).",
    )
    args = parser.parse_args()

    # ---- Load sprint data ----
    if args.from_file:
        print(f"[INFO] Loading sprint data from {args.from_file}", file=sys.stderr)
        with open(args.from_file) as f:
            sprint_data = json.load(f)
    else:
        if not all([JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
            print(
                "[ERROR] Set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN env vars, "
                "or use --from-file with a JSON file.",
                file=sys.stderr,
            )
            sys.exit(1)

        jira = JiraClient(JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN)

        board_id = args.board_id
        if not board_id:
            boards = jira.get_boards()
            if not boards:
                print("[ERROR] No Scrum boards found.", file=sys.stderr)
                sys.exit(1)
            board_id = boards[0]["id"]
            print(f"[INFO] Using board: {boards[0]['name']} (id={board_id})", file=sys.stderr)

        if args.sprint_id:
            sprint_id = args.sprint_id
            sprints = jira.get_sprints(board_id, state="closed")
            sprint = next((s for s in sprints if s["id"] == sprint_id), None)
            if not sprint:
                sprint = {"id": sprint_id, "name": f"Sprint {sprint_id}"}
        else:
            sprints = jira.get_sprints(board_id, state="closed")
            if not sprints:
                print("[ERROR] No closed sprints found.", file=sys.stderr)
                sys.exit(1)
            sprint = sprints[-1]
            sprint_id = sprint["id"]

        print(f"[INFO] Analyzing sprint: {sprint.get('name', sprint_id)}", file=sys.stderr)
        issues = jira.get_sprint_issues(sprint_id)
        sprint_data = flatten_sprint_data(sprint, issues)

    # ---- Optional data export ----
    if args.export_data:
        with open(args.export_data, "w") as f:
            json.dump(sprint_data, f, indent=2)
        print(f"[INFO] Sprint data exported to {args.export_data}", file=sys.stderr)

    # ---- AI analysis ----
    if not AI_API_KEY:
        print(
            "[ERROR] Set AI_API_KEY env var (OpenAI or Anthropic key).",
            file=sys.stderr,
        )
        sys.exit(1)

    print("[INFO] Sending data to AI for analysis...", file=sys.stderr)
    report = analyze_sprint(sprint_data)

    # ---- Output ----
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"[INFO] Report saved to {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
