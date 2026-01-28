---
name: cli-session-recorder
description: Record CLI sessions and share structured feedback with developer teams. Use when users want to capture their Copilot CLI session for feedback, bug reports, or sharing with teammates. Triggers on phrases like "record this session", "start recording", "capture feedback", "share this session", "stop recording", "save feedback", or when users mention wanting to report issues or share their CLI experience.
---

# CLI Session Recorder

Record CLI sessions and generate shareable feedback with human-readable summaries and machine-readable data.

## Workflow

### Starting a Recording

When the user wants to record their session:

1. Generate a unique session ID (use timestamp or UUID)
2. Detect the current model from context
3. Get git branch if in a repository: `git branch --show-current`
4. Begin capturing all exchanges

```python
from resources.session_recorder import SessionRecorder
import subprocess

# Get git branch
try:
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True, check=True
    ).stdout.strip()
except:
    branch = None

# Initialize recorder
recorder = SessionRecorder(
    session_id=f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
    model="claude-sonnet-4-20250514"  # from context
)
recorder.start_recording(git_branch=branch)
```

### During the Session

For each exchange, capture:
- User prompts
- Tool calls and their results
- Assistant responses
- Any errors

```python
# When user sends a prompt
recorder.add_user_prompt("Fix the login bug")

# When tools are called
recorder.add_tool_call(
    name="grep",
    parameters={"pattern": "login", "path": "src/"},
    result="Found in auth.py:42"
)

# When responding
recorder.add_assistant_response("I found the issue...")

# When errors occur
recorder.add_error(
    error_type="ToolError",
    message="File not found",
    context={"path": "/missing/file.py"}
)
```

### Stopping Recording

When the user says "stop recording" or "save feedback":

1. Stop the recorder
2. Scrub sensitive data
3. Ask for summary information
4. Generate the feedback file

```python
recorder.stop_recording()
recorder.scrub_sensitive_data()
```

### Generating Feedback

When stopping the recording, **auto-generate** the summary by analyzing the recorded session:

1. **Task Summary**: Infer from the first user prompt and overall conversation flow
2. **Problems**: Identify from errors, retries, tool failures, or user corrections
3. **Outcome**: Determine from final exchanges - did the task complete successfully?

Then present to user for confirmation:

```
I've generated a summary of this session:

**Task**: Fix login authentication bug causing 401 errors
**Problems**: 
- Initial grep search returned too many results
- Had to inspect multiple files before finding the issue
**Outcome**: Success - Bug identified and fixed in src/auth.py

Accept this summary, or provide your own?
```

If user accepts, proceed. If they provide edits, use their version.

```python
from resources.format_feedback import format_feedback, save_feedback

# Auto-generated from session analysis
feedback = format_feedback(
    session=recorder.get_session_data(),
    task_summary="User attempted to fix authentication bug...",  # AI-generated
    problems=["Initial search returned too many results"],        # AI-detected
    outcome="Success - Bug fixed in auth.py"                      # AI-inferred
)

filepath = save_feedback(feedback, output_dir="./feedback/")
print(f"Saved to: {filepath}")
```

### Sharing Options

Present the user with sharing choices:

**1. Local file (default)**
```python
from resources.format_feedback import save_feedback
filepath = save_feedback(feedback)
```

**2. GitHub Gist**
```python
from resources.share_gist import create_gist
url = create_gist(filepath, public=False)
```

**3. GitHub Issue**
```python
from resources.share_issue import create_issue
url = create_issue("owner/repo", filepath, labels=["feedback"])
```

## Commands Reference

Both explicit commands and natural language work. **Use explicit commands if natural language isn't giving good results.**

| Command | Natural Language | Action |
|---------|------------------|--------|
| `/cli-session-recorder start` | "record this", "start recording" | Begin capturing session |
| `/cli-session-recorder stop` | "stop recording" | Stop and auto-generate summary |
| `/cli-session-recorder save` | "save feedback" | Save to local file |
| `/cli-session-recorder save --gist` | "share as gist" | Upload to GitHub Gist |
| `/cli-session-recorder save --issue` | "create issue", "report this" | Create GitHub Issue |
| `/cli-session-recorder status` | "show recording status" | Report if recording is active |

## Summary Generation

When stopping a recording, analyze the session to auto-generate:

| Field | How to Infer |
|-------|--------------|
| **Task** | First user prompt + overall goal from conversation |
| **Problems** | Errors, tool failures, retries, user corrections, "that's not right" |
| **Outcome** | Final state - did task complete? User satisfaction signals |

**Always present the generated summary and ask**: "Accept this summary, or provide your own?"

## Output Format

See [resources/feedback_format.md](resources/feedback_format.md) for the complete output specification.

### Quick Reference

```markdown
# CLI Session Feedback
**Date**: 2024-01-28 14:23
**Model**: claude-sonnet-4-20250514
**Duration**: 15 minutes

## Summary
### Task Attempted
[What the user was trying to do]

### Problems Encountered
- [Issues that arose]

### Outcome
[Success/Failure/Partial]

---

## Full Session Data (Machine Readable)
```json
{ "metadata": {...}, "exchanges": [...], "errors": [...] }
```

## Guidelines

1. **Always scrub sensitive data** before sharing - the recorder does this automatically but verify no secrets leak
2. **Generate meaningful summaries** - don't just echo back what happened, synthesize the key points
3. **Be specific about problems** - vague feedback isn't helpful to developers
4. **Include context** - working directory, git branch, and model info help reproduce issues
5. **Respect user privacy** - don't share without explicit consent
