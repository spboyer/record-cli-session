#!/usr/bin/env python3
"""
Format session data into human-readable summary + machine-readable JSON.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from session_recorder import SessionData, generate_filename


def format_duration(seconds: Optional[float]) -> str:
    """Format duration in human-readable form."""
    if seconds is None:
        return "Unknown"
    
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def generate_summary_section(session: SessionData, task_summary: str, problems: list[str], outcome: str) -> str:
    """Generate the human-readable summary section."""
    stats = session.get_statistics()
    duration = format_duration(stats.get("duration_seconds"))
    
    # Format timestamp
    try:
        start_dt = datetime.fromisoformat(session.metadata.start_time)
        date_str = start_dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        date_str = session.metadata.start_time
    
    # Build problems list
    problems_md = "\n".join(f"- {p}" for p in problems) if problems else "- None reported"
    
    summary = f"""# CLI Session Feedback

**Date**: {date_str}
**Model**: {session.metadata.model}
**Duration**: {duration}
**Session ID**: {session.metadata.session_id}
**Working Directory**: {session.metadata.working_directory}
"""
    
    if session.metadata.git_branch:
        summary += f"**Git Branch**: {session.metadata.git_branch}\n"
    
    summary += f"""
## Summary

### Task Attempted
{task_summary}

### Problems Encountered
{problems_md}

### Outcome
{outcome}

## Statistics
- **Total Exchanges**: {stats['total_exchanges']}
- **Tool Calls**: {stats['total_tool_calls']}
- **Errors**: {stats['total_errors']}

---
"""
    return summary


def generate_machine_readable_section(session: SessionData) -> str:
    """Generate the machine-readable JSON section."""
    json_data = json.dumps(session.to_dict(), indent=2)
    
    return f"""
## Full Session Data (Machine Readable)

The following JSON contains the complete session data for LLM analysis:

```json
{json_data}
```
"""


def format_feedback(
    session: SessionData,
    task_summary: str,
    problems: list[str],
    outcome: str
) -> str:
    """
    Generate complete feedback document.
    
    Args:
        session: The recorded session data
        task_summary: AI-generated description of what user was trying to do
        problems: List of issues, errors, unexpected behaviors
        outcome: Success/Failure/Partial description
    
    Returns:
        Complete Markdown feedback document
    """
    summary = generate_summary_section(session, task_summary, problems, outcome)
    machine_readable = generate_machine_readable_section(session)
    
    return summary + machine_readable


def save_feedback(
    content: str,
    output_dir: Optional[Path] = None,
    filename: Optional[str] = None
) -> Path:
    """
    Save feedback to a file.
    
    Args:
        content: The feedback content to save
        output_dir: Directory to save to (defaults to ./feedback/)
        filename: Custom filename (defaults to timestamp-based)
    
    Returns:
        Path to the saved file
    """
    if output_dir is None:
        output_dir = Path.cwd() / "feedback"
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        filename = generate_filename()
    
    filepath = output_dir / filename
    filepath.write_text(content)
    
    return filepath


if __name__ == "__main__":
    # Example usage with mock data
    from session_recorder import SessionRecorder
    
    recorder = SessionRecorder(session_id="demo-456", model="claude-sonnet-4-20250514")
    recorder.start_recording(git_branch="feature/login-fix")
    
    recorder.add_user_prompt("Fix the login bug where users get 401 errors")
    recorder.add_tool_call("grep", {"pattern": "401", "path": "src/"}, result="Found in auth.py:42")
    recorder.add_tool_call("view", {"path": "src/auth.py"}, result="def authenticate():\n  ...")
    recorder.add_assistant_response("I found the issue - the token validation is failing...")
    
    recorder.add_user_prompt("Apply the fix")
    recorder.add_tool_call("edit", {"path": "src/auth.py", "old_str": "...", "new_str": "..."})
    recorder.add_assistant_response("Fixed! The token now validates correctly.")
    
    recorder.stop_recording()
    
    feedback = format_feedback(
        session=recorder.get_session_data(),
        task_summary="User attempted to fix a login authentication bug causing 401 errors for users.",
        problems=["Initial grep search returned too many results", "Had to inspect multiple files"],
        outcome="Success - Bug was identified and fixed in src/auth.py"
    )
    
    print(feedback)
