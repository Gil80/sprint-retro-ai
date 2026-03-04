#!/usr/bin/env python3
"""
Release Notes AI Generator
----------------------------
Reads Git commit history (or Jira fixed-version issues) and uses AI
to generate professional, user-facing release notes in Markdown.

Supports two input modes:
  1. Git log (local repo or provided JSON)
  2. Jira fixVersion query

Output: Markdown release notes grouped by category (Features, Fixes, Improvements).

Author: Gil Levy
License: MIT
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")

# ---------------------------------------------------------------------------
# Git log parser
# ---------------------------------------------------------------------------

def get_git_commits(since_tag: str | None = None, until_tag: str | None = None,
                    repo_path: str = ".") -> list[dict]:
    """Extract commits from local git repo."""
    cmd = ["git", "-C", repo_path, "log", "--pretty=format:%H|||%s|||%an|||%ai"]

    if since_tag and until_tag:
        cmd.append(f"{since_tag}..{until_tag}")
    elif since_tag:
        cmd.append(f"{since_tag}..HEAD")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"[ERROR] git log failed: {result.stderr}", file=sys.stderr)
        return []

    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("|||")
        if len(parts) >= 4:
            commits.append({
                "hash": parts[0][:8],
                "message": parts[1].strip(),
                "author": parts[2].strip(),
                "date": parts[3].strip(),
            })
    return commits


def parse_conventional_commits(commits: list[dict]) -> dict:
    """Group commits by conventional commit type."""
    categories = {
        "feat": [],
        "fix": [],
        "perf": [],
        "refactor": [],
        "docs": [],
        "chore": [],
        "test": [],
        "ci": [],
        "other": [],
    }

    pattern = re.compile(r"^(\w+)(?:\(([^)]*)\))?:\s*(.+)")

    for commit in commits:
        match = pattern.match(commit["message"])
        if match:
            ctype = match.group(1).lower()
            scope = match.group(2) or ""
            description = match.group(3)
            entry = {**commit, "scope": scope, "description": description}
            if ctype in categories:
                categories[ctype].append(entry)
            else:
                categories["other"].append(entry)
        else:
            categories["other"].append({**commit, "scope": "", "description": commit["message"]})

    return categories


# ---------------------------------------------------------------------------
# Jira fixVersion query
# ---------------------------------------------------------------------------

def get_jira_version_issues(version: str) -> list[dict]:
    """Fetch issues for a specific Jira fixVersion."""
    session = requests.Session()
    session.auth = (JIRA_EMAIL, JIRA_API_TOKEN)
    session.headers.update({"Accept": "application/json"})

    jql = f'fixVersion = "{version}" ORDER BY issuetype ASC, priority DESC'
    issues = []
    start = 0

    while True:
        resp = session.get(
            f"{JIRA_BASE_URL}/rest/api/2/search",
            params={
                "jql": jql,
                "startAt": start,
                "maxResults": 50,
                "fields": "summary,issuetype,priority,status,assignee,labels,resolution",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        for issue in data.get("issues", []):
            fields = issue["fields"]
            issues.append({
                "key": issue["key"],
                "summary": fields.get("summary", ""),
                "type": fields.get("issuetype", {}).get("name", ""),
                "priority": fields.get("priority", {}).get("name", ""),
                "status": fields.get("status", {}).get("name", ""),
                "assignee": (fields.get("assignee") or {}).get("displayName", "Unassigned"),
                "labels": fields.get("labels", []),
                "resolution": (fields.get("resolution") or {}).get("name", "Unresolved"),
            })
        if start + 50 >= data.get("total", 0):
            break
        start += 50

    return issues


# ---------------------------------------------------------------------------
# AI generation
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a technical writer for a software product.
Generate professional release notes from the provided data.

Your output MUST follow this Markdown structure:

# Release Notes - {version}
**Release Date:** {date}

## Highlights
Brief 2-3 sentence summary of the most impactful changes in this release.

## New Features
- Clear, user-facing description of each new feature
- Reference ticket keys where available

## Bug Fixes
- Description of each fix from the user's perspective
- Reference ticket keys where available

## Improvements
- Performance improvements, refactors, and enhancements
- Reference ticket keys where available

## Other Changes
- Documentation, CI/CD, dependency updates (keep brief)

Rules:
- Write for end users, not developers (unless it's an internal/developer tool)
- Be concise: one line per item
- Group related changes into single entries
- Skip trivial commits (typo fixes, merge commits, version bumps)
- Do not invent changes that are not in the data
- If a section has no items, omit it entirely"""


def generate_release_notes(data: dict, version: str = "Unknown") -> str:
    """Send data to AI and get formatted release notes."""
    payload = {"version": version, "date": datetime.now().strftime("%Y-%m-%d"), **data}
    user_content = json.dumps(payload, indent=2)

    if AI_PROVIDER == "anthropic":
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
                "messages": [{"role": "user", "content": user_content}],
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]
    else:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {AI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o",
                "temperature": 0.3,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate AI-powered release notes from Git commits or Jira fixVersion."
    )
    parser.add_argument("--version", type=str, default="1.0.0", help="Version label for the release notes.")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--from-file", type=str, help="Path to JSON file with commit/issue data.")
    group.add_argument("--git", action="store_true", help="Read commits from local git repo.")
    group.add_argument("--jira-version", type=str, help="Jira fixVersion to query.")

    parser.add_argument("--since-tag", type=str, help="Git tag to start from (for --git mode).")
    parser.add_argument("--until-tag", type=str, help="Git tag to end at (for --git mode).")
    parser.add_argument("--repo-path", type=str, default=".", help="Path to git repo (for --git mode).")
    parser.add_argument("--output", type=str, default=None, help="Output file path.")
    parser.add_argument("--export-data", type=str, help="Export parsed data to JSON.")

    args = parser.parse_args()

    # ---- Gather data ----
    if args.from_file:
        print(f"[INFO] Loading data from {args.from_file}", file=sys.stderr)
        with open(args.from_file) as f:
            data = json.load(f)
    elif args.git:
        print("[INFO] Reading git log...", file=sys.stderr)
        commits = get_git_commits(args.since_tag, args.until_tag, args.repo_path)
        if not commits:
            print("[ERROR] No commits found.", file=sys.stderr)
            sys.exit(1)
        print(f"[INFO] Found {len(commits)} commits.", file=sys.stderr)
        data = {"source": "git", "commits": parse_conventional_commits(commits)}
    elif args.jira_version:
        if not all([JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
            print("[ERROR] Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN env vars.", file=sys.stderr)
            sys.exit(1)
        print(f"[INFO] Querying Jira for fixVersion={args.jira_version}...", file=sys.stderr)
        issues = get_jira_version_issues(args.jira_version)
        if not issues:
            print("[ERROR] No issues found for this version.", file=sys.stderr)
            sys.exit(1)
        print(f"[INFO] Found {len(issues)} issues.", file=sys.stderr)
        data = {"source": "jira", "version": args.jira_version, "issues": issues}

    if args.export_data:
        with open(args.export_data, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[INFO] Data exported to {args.export_data}", file=sys.stderr)

    # ---- Generate ----
    if not AI_API_KEY:
        print("[ERROR] Set AI_API_KEY env var.", file=sys.stderr)
        sys.exit(1)

    print("[INFO] Generating release notes with AI...", file=sys.stderr)
    notes = generate_release_notes(data, args.version)

    if args.output:
        with open(args.output, "w") as f:
            f.write(notes)
        print(f"[INFO] Release notes saved to {args.output}", file=sys.stderr)
    else:
        print(notes)


if __name__ == "__main__":
    main()
