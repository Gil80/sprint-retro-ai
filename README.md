# Release Notes AI Generator

A command-line tool that generates professional, user-facing release notes from Git commit history or Jira fixVersion data using AI.

## Why I Built This

Writing release notes is one of those tasks that falls between engineering and product management. Developers write commit messages for other developers. Product managers need user-facing change descriptions. Someone has to translate between the two, and that someone was usually me.

This tool bridges the gap. Feed it a Git log or Jira version, and it produces clean, categorized release notes that are ready to publish to users, paste into WordPress, or add to Confluence.

## How It Works

```
┌──────────────┐     ┌──────────────┐     ┌───────────┐     ┌──────────────┐
│   Git Log    │────>│   Parse &    │────>│  AI Model │────>│   Release    │
│  (commits)   │     │  Categorize  │     │ Generation│     │    Notes     │
└──────────────┘     └──────────────┘     └───────────┘     │  (Markdown)  │
       OR                                                    └──────────────┘
┌──────────────┐
│    Jira      │──┘
│ fixVersion   │
└──────────────┘
```

**Three input modes:**

1. **Git mode** - Reads commit history from a local repo. Automatically parses [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `perf:`, etc.) and groups them by category.
2. **Jira mode** - Queries Jira for all issues with a specific fixVersion and generates notes from ticket data.
3. **File mode** - Reads from a JSON file (useful for demos, testing, or CI pipelines).

## Quick Start

### Demo mode (no Git/Jira needed)

```bash
git clone https://github.com/Gil80/release-notes-ai.git
cd release-notes-ai

pip install -r requirements.txt

export AI_API_KEY="your-openai-or-anthropic-key"
export AI_PROVIDER="openai"  # or "anthropic"

python release_notes.py --from-file sample_data/commits_example.json --version "2.4.0"
```

### Git mode

```bash
# Generate notes from the last tagged release to HEAD
python release_notes.py --git --since-tag v2.3.0 --version "2.4.0"

# Between two tags
python release_notes.py --git --since-tag v2.3.0 --until-tag v2.4.0 --version "2.4.0"

# From a different repo directory
python release_notes.py --git --repo-path /path/to/repo --since-tag v1.0.0 --version "1.1.0"

# Save to file
python release_notes.py --git --since-tag v2.3.0 --version "2.4.0" --output RELEASE_NOTES.md
```

### Jira mode

```bash
export JIRA_BASE_URL="https://yourcompany.atlassian.net"
export JIRA_EMAIL="your-email@company.com"
export JIRA_API_TOKEN="your-token"

python release_notes.py --jira-version "UP Phone 3.2" --version "3.2.0"
```

## Sample Output

```markdown
# Release Notes - 2.4.0
**Release Date:** 2026-02-24

## Highlights
This release introduces Single Sign-On with Google, real-time notifications,
and usage-based billing. We also resolved several stability issues including
session persistence and export timeouts.

## New Features
- **Google SSO Login** - Sign in with your Google account for faster, more secure access
- **Real-time Notifications** - See updates instantly with the new notification bell
- **CSV Report Export** - Download any report as CSV for offline analysis
- **Usage-based Billing** - New flexible billing tiers based on actual usage
- **API Rate Limiting** - Improved API stability with intelligent rate limiting

## Bug Fixes
- Fixed session not persisting after browser refresh
- Fixed chart tooltips displaying incorrect date format
- Resolved timeout when exporting datasets larger than 10,000 rows
- Fixed server error when filtering by empty date range

## Improvements
- Database query performance improved by 60% on event lookups
- Streamlined authentication token handling
```

## Configuration

| Environment Variable | Required | Description |
|---------------------|----------|-------------|
| `AI_API_KEY` | Yes | OpenAI or Anthropic API key |
| `AI_PROVIDER` | No | `openai` (default) or `anthropic` |
| `JIRA_BASE_URL` | For Jira mode | Your Jira instance URL |
| `JIRA_EMAIL` | For Jira mode | Jira account email |
| `JIRA_API_TOKEN` | For Jira mode | Jira API token |

## Conventional Commits

For best results with Git mode, use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(auth): add SSO login with Google
fix(export): timeout on large datasets
perf(db): optimize event query with composite index
docs: update API reference
```

The tool will still work with free-form commit messages, but categorization will be less accurate.

## Project Structure

```
release-notes-ai/
├── release_notes.py           # Main script
├── sample_data/
│   └── commits_example.json   # Demo data
├── requirements.txt
├── LICENSE
└── README.md
```

## License

MIT
