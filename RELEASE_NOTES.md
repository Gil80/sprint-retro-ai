# Release Notes - 0.1.0
**Release Date:** 2026-03-04

## Highlights
This first release of **pm-ai-toolkit** gives project and product managers an AI-powered way to automate two of their most repetitive workflows: sprint retrospectives and release notes. Instead of manually combing through Jira tickets or Git history, you can now generate a structured, high-quality first draft in seconds and spend your time on insight, prioritization, and storytelling instead of formatting.

## New Features
- **Sprint Retrospective Analyzer (`scrips/retro_analyzer.py`)**  
  Connects to Jira (or a local JSON export) to pull issues from a completed sprint and generate a full retrospective report, including sprint summary, what went well / didn’t go well, patterns, risks, and concrete action items—ready to paste into Confluence or your team workspace.
- **Release Notes Generator (`scrips/release_notes.py`)**  
  Reads Git commit history or Jira fixVersions and turns them into user-facing release notes grouped by category, translating developer-centric messages into language stakeholders and customers can understand.
- **Multiple Input Modes for Both Tools**  
  Support for **Git mode**, **Jira mode**, and **file/JSON mode**, so you can run the toolkit locally against live systems or plug it into CI pipelines using pre-exported data.
- **Demo Data & Quick-Start Commands**  
  Bundled example JSON files and copy‑pasteable CLI commands so you can try out retrospectives and release notes end-to-end without touching production Jira projects or repos.

## Improvements
- **User-Focused Prompt Tuning**  
  AI prompts are optimized for PMs and non-technical stakeholders, emphasizing clarity, narrative flow, and actionable insights over raw technical detail.
- **Consistent Output Structure**  
  Standardized headings, sections, and terminology across retrospective reports and release notes so artifacts feel like part of a cohesive PM toolkit.
- **Configurable AI Provider & Jira Integration**  
  Simple environment-variable-based configuration for choosing OpenAI or Anthropic and for securely wiring in Jira credentials.

## Other Changes
- **Project Structure & Examples**  
  Established the initial project layout (`scrips/`, `examples/`, `requirements.txt`) and included demo sprint and commit JSON files to showcase typical workflows.
- **Licensing & Documentation**  
  Added MIT license and a detailed `README` explaining use cases, setup steps, configuration, and sample outputs for both tools.

