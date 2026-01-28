#!/usr/bin/env python3
"""
Share feedback via GitHub Issue using the gh CLI.
"""

import subprocess
import re
from pathlib import Path
from typing import Optional


def extract_summary_for_issue(feedback_content: str) -> tuple[str, str]:
    """
    Extract title and body from feedback content for issue creation.
    
    Returns:
        Tuple of (title, body)
    """
    lines = feedback_content.split('\n')
    
    # Extract task summary for title
    title = "CLI Session Feedback"
    in_task_section = False
    task_lines = []
    
    for line in lines:
        if "### Task Attempted" in line:
            in_task_section = True
            continue
        elif line.startswith("###") and in_task_section:
            break
        elif in_task_section and line.strip():
            task_lines.append(line.strip())
    
    if task_lines:
        # Use first 80 chars of task as title
        task_text = " ".join(task_lines)
        title = f"Feedback: {task_text[:80]}{'...' if len(task_text) > 80 else ''}"
    
    # For body, include summary section only (not full JSON)
    # Find where machine-readable section starts
    body = feedback_content
    json_marker = "## Full Session Data (Machine Readable)"
    if json_marker in body:
        body = body.split(json_marker)[0]
        body += "\n\n*Full session data available in attached file or gist.*"
    
    return title, body


def create_issue(
    repo: str,
    filepath: Path,
    title: Optional[str] = None,
    labels: Optional[list[str]] = None,
    assignee: Optional[str] = None
) -> Optional[str]:
    """
    Create a GitHub Issue from a feedback file.
    
    Args:
        repo: Repository in owner/repo format
        filepath: Path to the feedback file
        title: Issue title (auto-generated if not provided)
        labels: List of labels to apply
        assignee: GitHub username to assign
    
    Returns:
        URL of the created issue, or None if failed
    """
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        return None
    
    content = filepath.read_text()
    auto_title, body = extract_summary_for_issue(content)
    
    if title is None:
        title = auto_title
    
    cmd = [
        "gh", "issue", "create",
        "--repo", repo,
        "--title", title,
        "--body", body
    ]
    
    if labels:
        for label in labels:
            cmd.extend(["--label", label])
    
    if assignee:
        cmd.extend(["--assignee", assignee])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        issue_url = result.stdout.strip()
        return issue_url
    except subprocess.CalledProcessError as e:
        print(f"Error creating issue: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: 'gh' CLI not found. Install it from https://cli.github.com/")
        return None


def get_repo_from_remote() -> Optional[str]:
    """Try to detect repo from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        url = result.stdout.strip()
        
        # Parse GitHub URL formats
        patterns = [
            r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$',
            r'github\.com/([^/]+/[^/]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1).rstrip('.git')
        
        return None
    except subprocess.CalledProcessError:
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: share_issue.py <filepath> [--repo owner/repo] [--label label1] [--assignee user]")
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    
    # Parse arguments
    repo = None
    labels = []
    assignee = None
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--repo" and i + 1 < len(sys.argv):
            repo = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--label" and i + 1 < len(sys.argv):
            labels.append(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--assignee" and i + 1 < len(sys.argv):
            assignee = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    # Try to auto-detect repo if not specified
    if repo is None:
        repo = get_repo_from_remote()
        if repo is None:
            print("Error: Could not detect repository. Please specify with --repo owner/repo")
            sys.exit(1)
        print(f"Detected repository: {repo}")
    
    url = create_issue(repo, filepath, labels=labels or None, assignee=assignee)
    if url:
        print(f"Issue created: {url}")
    else:
        sys.exit(1)
