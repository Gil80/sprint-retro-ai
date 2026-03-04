# Release Notes AI — Detailed Code Explanation

---

## Step 1 — The Big Picture

Before any code, here's what this program does in plain English:

1. **Input** — it reads a list of Git commits (like "fixed login bug", "added export button") from a file
2. **Process** — it organizes those commits into categories (features, bug fixes, improvements)
3. **AI call** — it sends that organized data to an AI (OpenAI or Anthropic) with instructions: *"turn this into professional release notes"*
4. **Output** — it prints clean, formatted Markdown that a PM can paste directly into Confluence, WordPress, or an email to users

Think of it as a translator: **developer language → user language**, automated.

---

## Step 2 — The Dependencies (lines 18–26)

```python
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime

import requests
```

These are the tools the script borrows before it starts working. Think of them like apps on your phone — you don't build them, you just use them.

| Import | What it is | What this script uses it for |
|---|---|---|
| `argparse` | Reads command-line flags | Handles `--from-file`, `--version`, `--git`, etc. |
| `json` | Reads/writes JSON files | Loads the `commits_example.json` file |
| `os` | Talks to the operating system | Reads environment variables like `AI_API_KEY` |
| `re` | Regular expressions (pattern matching) | Parses commit messages like `feat(auth): add SSO` |
| `subprocess` | Runs other programs | Executes the `git log` command |
| `sys` | Controls the Python process itself | Prints errors, exits with error codes |
| `datetime` | Handles dates and times | Stamps the release date on the output |
| `requests` | Makes HTTP calls over the internet | Calls the OpenAI/Anthropic API |

The only one that isn't built into Python is `requests` — that's why `requirements.txt` exists. You run `pip install requests` once and Python downloads it.

---

## Step 3 — Configuration (lines 32–36)

```python
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
```

These 5 lines read **environment variables** — think of them as settings that live outside the code, on your computer.

**Why outside the code?**
Imagine you hardcoded your API key directly in the script:
```python
AI_API_KEY = "sk-abc123mysecretkey"
```
The moment you push that to GitHub, the whole world can see it and use your paid account. Environment variables solve this — the secret stays on your machine, never in the code.

`os.getenv("AI_API_KEY", "")` means:
- *"Look for a variable called `AI_API_KEY` on this computer"*
- *"If it doesn't exist, use an empty string `""` as the default"*

The last line is slightly different:
```python
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
```
The default here is `"openai"` — so if you don't set anything, the script assumes you're using OpenAI. If you want Anthropic instead, you set `AI_PROVIDER=anthropic` before running.

---

## Step 4 — Reading the Example File (lines 258–261)

```python
if args.from_file:
    print(f"[INFO] Loading data from {args.from_file}", file=sys.stderr)
    with open(args.from_file) as f:
        data = json.load(f)
```

**`with open(args.from_file) as f:`**
Opens the JSON file. The `with` keyword is important — it automatically closes the file when done, even if something crashes. Think of it like an automatic door that always closes behind you.

**`data = json.load(f)`**
Reads the file contents and converts it from raw text into a Python dictionary — a structured object the script can work with. After this line, `data` looks like:
```python
{
  "source": "git",
  "commits": {
    "feat": [ {...}, {...} ],
    "fix":  [ {...}, {...} ],
    ...
  }
}
```

**`file=sys.stderr`**
The `[INFO]` messages print to `stderr` (the error channel) instead of `stdout` (the main output). This means if you save the release notes to a file with `--output`, only the actual notes go in — not the `[INFO]` lines. Clean separation.

---

## Step 5 — Parsing Commit Messages (lines 72–102)

```python
def parse_conventional_commits(commits: list[dict]) -> dict:
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
```

### The categories dictionary

```python
categories = {
    "feat": [],
    "fix": [],
    ...
}
```

This is just a set of empty buckets at the start. Every commit will end up in one of them. `feat` = new features, `fix` = bug fixes, `perf` = performance improvements, and so on. Anything that doesn't fit goes into `"other"`.

### The regex pattern

```python
pattern = re.compile(r"^(\w+)(?:\(([^)]*)\))?:\s*(.+)")
```

Using a real example: `feat(auth): add SSO login with Google OAuth`

The pattern is looking for 3 pieces:

| Piece | Pattern part | What it captures | Example |
|---|---|---|---|
| **Type** | `(\w+)` | One or more word characters | `feat` |
| **Scope** | `(?:\(([^)]*)\))?` | Optional text in parentheses | `auth` |
| **Description** | `(.+)` | Everything after the colon | `add SSO login with Google OAuth` |

The `?` after the scope group means it's **optional** — so `fix: crash on login` (no scope) still works fine.

After the match, these 3 pieces are pulled out:
```python
ctype = match.group(1).lower()   # "feat"
scope = match.group(2) or ""     # "auth"
description = match.group(3)     # "add SSO login with Google OAuth"
```

### The `{**commit, ...}` syntax

```python
entry = {**commit, "scope": scope, "description": description}
```

The `**` means *"copy everything from this dictionary, then add more keys"*. So `entry` ends up with the original commit data (hash, author, date) **plus** the newly extracted scope and description. Think of it like photocopying a form and then filling in two extra blank fields.

### What comes out

After this function runs, the messy list of commits is now neatly sorted:

```python
{
  "feat": [
    { "hash": "a1b2c3d4", "description": "add SSO login with Google OAuth", "scope": "auth", ... },
    { "hash": "e5f6g7h8", "description": "real-time notification bell", "scope": "dashboard", ... },
  ],
  "fix": [
    { "hash": "u1v2w3x4", "description": "session not persisting after browser refresh", ... },
  ],
  ...
}
```

This sorted structure is exactly what gets sent to the AI in the next step.

---

## Step 6 — The AI Call (lines 155–231)

### Part A — The System Prompt (lines 155–187)

```python
SYSTEM_PROMPT = """You are a technical writer for a software product.
Generate professional release notes from the provided data.

Your output MUST follow this Markdown structure:

# Release Notes - {version}
**Release Date:** {date}

## Highlights
...

Rules:
- Write for end users, not developers
- Be concise: one line per item
- Skip trivial commits (typo fixes, merge commits, version bumps)
- Do not invent changes that are not in the data
- If a section has no items, omit it entirely"""
```

This is stored in a variable called `SYSTEM_PROMPT`. Think of it as the **job description you give the AI before the conversation starts**. It tells the AI:
- What role to play ("you are a technical writer")
- What format to follow (the exact Markdown structure)
- What rules to respect ("don't invent things", "write for users not developers")

The AI reads this first, before it sees any of your commit data. It sets the context for everything that follows.

### Part B — Building the payload (lines 190–193)

```python
def generate_release_notes(data: dict, version: str = "Unknown") -> str:
    payload = {"version": version, "date": datetime.now().strftime("%Y-%m-%d"), **data}
    user_content = json.dumps(payload, indent=2)
```

**`{"version": version, "date": datetime.now().strftime("%Y-%m-%d"), **data}`**
Builds one combined dictionary with three things merged together:
- The version number you passed in (`"2.4.0"`)
- Today's date, formatted as `"2026-03-04"` (the `strftime` formats the date — `%Y` = 4-digit year, `%m` = month, `%d` = day)
- Everything from the `data` dict (all the sorted commits)

**`user_content = json.dumps(payload, indent=2)`**
Converts the Python dictionary back into a JSON text string, nicely indented. This is what actually gets sent to the AI — not a Python object, but plain text the API can receive. `indent=2` makes it readable with 2-space indentation.

### Part C — The actual HTTP call (lines 214–231)

```python
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
```

**`requests.post(...)`**
Sends an HTTP POST request — the same type of request your browser sends when you submit a form. Here it's sending data to OpenAI's servers over the internet.

**`"Authorization": f"Bearer {AI_API_KEY}"`**
This is how you prove to OpenAI that you're allowed to use their API. `Bearer` is the standard word for this type of token authentication — like showing your ID at a door.

**`"Content-Type": "application/json"`**
Tells OpenAI what format the data is in — JSON. Without this, the server doesn't know how to read what you sent.

**`"model": "gpt-4o"`**
Which AI model to use. GPT-4o is OpenAI's most capable model at the time this was written.

**`"temperature": 0.3`**
Controls how creative vs predictable the AI is. Scale goes from 0 (very consistent, almost robotic) to 1 (very creative, unpredictable). `0.3` is intentionally low — you want release notes to be factual and consistent, not creative.

**`"messages": [{"role": "system", ...}, {"role": "user", ...}]`**
The conversation sent to the AI. Two parts:
- `"system"` — the instructions (the prompt you wrote)
- `"user"` — the actual data (the JSON of sorted commits)

**`resp.raise_for_status()`**
If the API returned an error (like 401 Unauthorized or 429 Too Many Requests), this line throws an exception immediately instead of silently continuing with broken data.

**`return resp.json()["choices"][0]["message"]["content"]`**
Digs into the API response to extract just the text. The OpenAI response is a nested JSON object — this navigates through it like `response → choices → first choice → message → content` to get the actual release notes text.

---

## Step 7 — The CLI (lines 238–304)

CLI stands for **Command Line Interface** — it's what makes the script usable from the terminal instead of having to edit the code every time you want to change something.

### Setting up the argument parser (lines 239–253)

```python
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
```

**`argparse.ArgumentParser(...)`**
Creates an object that knows how to read what you type after `python release_notes.py`. It also auto-generates a `--help` page for free.

**`parser.add_argument("--version", ...)`**
Registers a flag. When you type `--version "2.4.0"` in the terminal, `args.version` becomes `"2.4.0"` in the code. The `default="1.0.0"` means if you forget to pass it, it falls back to `"1.0.0"`.

**`group = parser.add_mutually_exclusive_group(required=True)`**
Creates a group where **exactly one** of the options must be chosen — you can't use `--from-file` and `--git` at the same time, and you must use at least one. If you try to combine them, argparse automatically prints an error and stops. No extra code needed to enforce this.

**`action="store_true"`** (on the `--git` flag)
Unlike the other flags that accept a value, `--git` is just a switch — either it's there or it isn't. `store_true` means: *"if this flag is present, set it to True; otherwise False."*

**`args = parser.parse_args()`**
This single line reads everything the user typed and populates the `args` object. After this, `args.from_file`, `args.version`, `args.git`, etc. are all ready to use.

### The three input paths (lines 258–280)

```python
if args.from_file:
    with open(args.from_file) as f:
        data = json.load(f)

elif args.git:
    commits = get_git_commits(args.since_tag, args.until_tag, args.repo_path)
    data = {"source": "git", "commits": parse_conventional_commits(commits)}

elif args.jira_version:
    issues = get_jira_version_issues(args.jira_version)
    data = {"source": "jira", "version": args.jira_version, "issues": issues}
```

This is a simple decision tree — exactly one of these three branches runs, depending on which flag the user passed. All three branches end up producing `data`, a Python dictionary. After this block, the rest of the code doesn't care how the data was collected — it just works with `data`.

**This pattern has a name: normalization.** Three different sources (file, Git, Jira) all get converted into the same shape before being processed. Clean and predictable.

### The guard clause (lines 288–290)

```python
if not AI_API_KEY:
    print("[ERROR] Set AI_API_KEY env var.", file=sys.stderr)
    sys.exit(1)
```

This checks that the API key exists **before** trying to call the AI. Without this, the script would make the API call, get a 401 Unauthorized error, and crash with a confusing Python traceback. Instead it fails early with a clear, human-readable message.

`sys.exit(1)` stops the script completely. The `1` signals to the operating system that the program ended with an error (as opposed to `0` which means success).

### The final output (lines 295–300)

```python
if args.output:
    with open(args.output, "w") as f:
        f.write(notes)
    print(f"[INFO] Release notes saved to {args.output}", file=sys.stderr)
else:
    print(notes)
```

If the user passed `--output RELEASE_NOTES.md`, the notes get written to a file. Otherwise they print to the terminal. The `"w"` in `open(..., "w")` means write mode — it creates the file if it doesn't exist, or overwrites it if it does.

### The entry point (lines 303–304)

```python
if __name__ == "__main__":
    main()
```

This is a Python convention. It means: *"only run the `main()` function if this script was executed directly."* If another Python file imports this script as a module, `main()` won't run automatically. It's a safety guard that every well-written Python script has.

---

## Step 8 — The Example Data File (`commits_example.json`)

This file serves two purposes:
1. **Demo mode** — lets anyone try the tool without needing Git or Jira
2. **Documentation** — shows exactly what data structure the script expects

### The top level structure

```json
{
  "source": "git",
  "commits": {
    "feat": [...],
    "fix": [...],
    "perf": [...],
    "refactor": [...],
    "docs": [...],
    "chore": [...],
    "test": [...],
    "ci": [...],
    "other": []
  }
}
```

**`"source": "git"`**
Tells the AI where this data came from. The AI uses this context when writing — it knows to treat these as code commits, not Jira tickets.

**`"commits"`**
A dictionary where each key is a commit type. This is the output shape of `parse_conventional_commits()` from Step 5 — the example file was pre-sorted to simulate what that function produces. This is intentional: the file lets you skip the parsing step entirely and jump straight to the AI call.

### A single commit entry

```json
{
  "hash": "a1b2c3d4",
  "message": "feat(auth): add SSO login with Google OAuth",
  "author": "Noa K.",
  "date": "2026-02-20",
  "scope": "auth",
  "description": "add SSO login with Google OAuth"
}
```

| Field | Where it comes from | What it's used for |
|---|---|---|
| `hash` | First 8 characters of the Git commit ID | Traceability — can look up the exact commit |
| `message` | The full original commit message | Sent to AI for context |
| `author` | The developer's name from Git | Not used by AI, but useful for debugging |
| `date` | When the commit was made | Helps AI understand chronology |
| `scope` | Extracted from `feat(auth):` → `auth` | Tells AI which part of the app was changed |
| `description` | Extracted from after the colon | The clean summary the AI focuses on |

### Why the categories matter

The file has commits spread across `feat`, `fix`, `perf`, `refactor`, `docs`, `chore`, `test`, `ci`. But look at what the AI actually produces:

```markdown
## New Features      ← from "feat"
## Bug Fixes         ← from "fix"
## Improvements      ← from "perf" and "refactor"
## Other Changes     ← from "docs", "chore", "ci"
```

The AI collapses 8 technical categories into 4 user-friendly sections. `test` commits disappear entirely — users don't care that you wrote tests. This is the translation the AI performs: **developer taxonomy → user-relevant groupings**.

### The realistic fake data — a deliberate choice

The example uses realistic developer names, real-sounding features (Google SSO, WebSocket notifications, usage-based billing), and plausible dates. This is intentional. When an interviewer or recruiter looks at this repo, the example data tells its own story — it reads like a real product team shipped a real release. That detail signals professional thinking.

---

## Step 9 — Interview Questions & Answers

### Q1: "Why Python? Why not JavaScript or another language?"

Python is the dominant language for AI/ML tooling and API integrations. The libraries needed — `requests` for HTTP calls, `argparse` for CLI, `json` for data handling — are either built in or one-line installs. For a data pipeline that calls external APIs and processes text, Python is the natural choice. It's also readable enough that a non-developer teammate could understand what the script does.

### Q2: "What happens if the AI returns something unexpected or the API is down?"

`raise_for_status()` catches HTTP errors — a 401 unauthorized, 429 rate limit, or 500 server error will all throw an exception with a clear message. If hardening this for production, you'd add retry logic with exponential backoff for transient failures, and validate the AI output against the expected Markdown structure before returning it. For a portfolio tool this is acceptable, but the gaps are known.

### Q3: "What is a REST API and how does this script use one?"

A REST API is a standardized way for two systems to communicate over the internet using HTTP — the same protocol browsers use. This script acts as a client: it sends a POST request to OpenAI's server with the commit data and instructions, and gets back the generated text. The API key in the Authorization header proves you're allowed to use the service. It's no different in principle from a web form submission — just structured as JSON instead of form fields.

### Q4: "What is the Conventional Commits standard and why did you use it?"

Conventional Commits is a widely adopted standard where commit messages follow the format `type(scope): description` — for example `feat(auth): add SSO login`. It was created to make commit history machine-readable. Tools like semantic-release and changelog generators all rely on it. It's used here because it gives the regex a reliable pattern to parse, which means the AI receives cleanly categorized data instead of a wall of free-form text. The tool still works with free-form commits — they just land in the `other` bucket.

### Q5: "Why did you set temperature to 0.3?"

Temperature controls the randomness of the AI output. At 0 it's completely deterministic — same input always produces the same output. At 1 it's highly creative and unpredictable. For release notes you want consistency and accuracy, not creativity. 0.3 gives slightly varied phrasing across runs while keeping the content factual and structured. At 0.8 the AI might start embellishing features or using dramatic language — the last thing you want in a changelog.

### Q6: "Could this be used maliciously or cause any security issues?"

Two main considerations. First, credentials — API keys and Jira tokens are read from environment variables, never hardcoded, so there's no risk of accidentally committing secrets to Git. Second, the data flow only goes from your internal systems outward to the AI provider — commit messages and Jira ticket summaries are sent to OpenAI or Anthropic. If a company has data residency requirements or can't send code details externally, a self-hosted model would be the alternative, or Anthropic's enterprise tier with data privacy guarantees.

### Q7: "How would you scale this if a team of 50 developers used it daily?"

A few things to add: rate limiting handling with automatic retries since OpenAI throttles heavy usage, a caching layer so identical commit sets don't trigger repeated API calls, and a web interface or Slack bot so developers don't need to run a Python script locally. A CI/CD integration would also make sense — so release notes are generated automatically when a version tag is pushed, with no human intervention needed. The core logic wouldn't change — just the delivery mechanism around it.

### Q8: "You're a PM, not a developer. How did you build this?"

AI-assisted development was used to help write the code — and that's transparent. But every decision was driven by the PM perspective: what the tool should do, why these specific input modes, how the prompt should be structured, what the output format should look like. Every line of this code can be read and explained, which the walkthrough above demonstrates. AI-assisted development is the reality of the industry right now — a PM who can direct AI to build working tools and understand the result is exactly the profile that high-performing teams need.
