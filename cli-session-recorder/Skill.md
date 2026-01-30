---
name: cli-session-recorder
description: Record CLI sessions and share structured feedback with developer teams. Use when users want to capture their Copilot CLI session for feedback, bug reports, or sharing with teammates. Triggers on phrases like "record this session", "start recording", "capture feedback", "share this session", "stop recording", "save feedback", or when users mention wanting to report issues or share their CLI experience.
---

# CLI Session Recorder

Record CLI sessions and generate shareable feedback with human-readable summaries and machine-readable data.

## ⚠️ MANDATORY: Comprehensive Output

**EVERY saved report MUST include the complete `exchanges` array with:**
- All user prompts (verbatim)
- All tool calls with full parameters AND results
- All assistant responses
- All errors with context
- Timing information

**This is NOT optional.** A report without detailed exchanges is incomplete and useless for debugging. Never save a summary-only report.

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

# Initialize recorder with optional debug log parsing
recorder = SessionRecorder(
    session_id=f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
    model="claude-sonnet-4-20250514",  # from context
    log_dir=".logs"  # Optional: path to Copilot debug logs
)
recorder.start_recording(git_branch=branch, capture_environment=True)
```

### During the Session (VERBOSE CAPTURE)

**IMPORTANT**: Capture EVERY exchange with full verbosity. This is critical for debugging and feedback analysis.

For **EACH** exchange, you MUST capture:
- The exact user prompt (verbatim)
- ALL tool calls with:
  - Full tool name
  - Complete parameters object
  - Full result/output (truncate only if >2000 chars)
  - Timing information
  - Retry counts
- The complete assistant response
- Any errors with full context
- Exchange timing

```python
# When user sends a prompt - capture EXACTLY what they typed
recorder.add_user_prompt("help me deploy my app to azure")

# For EVERY tool call - capture full details
recorder.start_tool_call()  # Start timing
recorder.add_tool_call(
    name="bash",
    parameters={
        "command": "ls -la && cat index.html",
        "description": "List files and view content"
    },
    result="total 8\n-rw-r--r--  1 user  staff  123 Jan 28 index.html\n<!DOCTYPE html>...",
    retry_count=0
)

recorder.start_tool_call()
recorder.add_tool_call(
    name="glob",
    parameters={"pattern": "**/*.{json,yaml,yml}"},
    result=".github/workflows/run_test_deploy.yml",
    retry_count=0
)

recorder.start_tool_call()
recorder.add_tool_call(
    name="bash",
    parameters={"command": "az group create --name rg-myapp --location eastus2"},
    result='{"id": "/subscriptions/.../resourceGroups/rg-myapp", "location": "eastus2", "name": "rg-myapp"}',
    retry_count=0
)

# Capture COMPLETE assistant response
recorder.add_assistant_response(
    "I detected a static HTML site. I'll deploy it to Azure Static Web Apps.\n\n"
    "Created resource group `rg-myapp` and deploying..."
)

# When errors occur - capture FULL context
recorder.add_error(
    error_type="ToolError",
    message="SWA CLI artifact folder constraint - current directory cannot be identical to artifact folder",
    context={
        "tool": "bash",
        "command": "swa deploy . --deployment-token ...",
        "resolution": "Created dist folder and copied files"
    }
)
```

### Verbose Capture Checklist

For each turn, ensure you record:

| Item | Required | Details |
|------|----------|---------|
| User prompt | ✅ Yes | Exact text, no summarization |
| Tool name | ✅ Yes | Full tool identifier |
| Tool parameters | ✅ Yes | Complete parameters object |
| Tool result | ✅ Yes | Full output (truncate >2000 chars with "[truncated]") |
| Tool timing | ✅ Yes | Use `start_tool_call()` before each call |
| Tool errors | ✅ Yes | Include if tool failed |
| Assistant response | ✅ Yes | Complete response text |
| Exchange timestamp | ✅ Auto | Captured automatically |

### Stopping Recording

When the user says "stop recording" or "save feedback":

1. Stop the recorder
2. Scrub sensitive data
3. Ask for summary information
4. Generate the feedback file **with FULL exchange data**

```python
recorder.stop_recording()
recorder.scrub_sensitive_data()
```

### Generating Feedback (ALWAYS COMPREHENSIVE)

**⚠️ CRITICAL**: The generated feedback MUST always include the complete `exchanges` array with all tool calls, parameters, and results. This is mandatory, not optional.

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

### Quick Reference - Verbose Output

The output MUST include detailed exchange data like this example:

```markdown
# CLI Session Feedback
**Date**: 2024-01-28 14:23
**Model**: claude-sonnet-4-20250514
**Duration**: 15 minutes

## Summary
### Task Attempted
Deploy a static HTML website to Azure using Azure Static Web Apps.

### Problems Encountered
- SWA CLI artifact folder constraint error - current directory cannot be identical to artifact folder
- Required creating a separate `dist` folder and copying files

### Outcome
**Success** - Static site deployed to https://salmon-rock-049daba0f.2.azurestaticapps.net

## Statistics
- **Total Exchanges**: 2
- **Tool Calls**: 7
- **Errors**: 1

---

## Full Session Data (Machine Readable)
```json
{
  "metadata": {...},
  "exchanges": [
    {
      "user_prompt": "start",
      "assistant_response": "Recording started for session-20240128-142312",
      "tool_calls": [
        {
          "name": "bash",
          "parameters": {"command": "git branch --show-current"},
          "result": "main",
          "timestamp": "2024-01-28T14:23:15",
          "duration_ms": 45.2
        }
      ],
      "timestamp": "2024-01-28T14:23:12"
    },
    {
      "user_prompt": "help me deploy my app to azure",
      "assistant_response": "Detected static HTML site. Recommended Azure Static Web Apps. Created resource group and SWA, deployed successfully.",
      "tool_calls": [
        {
          "name": "bash",
          "parameters": {"command": "ls -la && cat index.html"},
          "result": "index.html - Hello World static site",
          "timestamp": "2024-01-28T14:23:30",
          "duration_ms": 120.5
        },
        {
          "name": "glob",
          "parameters": {"pattern": "**/*.{json,yaml,yml}"},
          "result": ".github/workflows/run_test_deploy.yml",
          "timestamp": "2024-01-28T14:23:32",
          "duration_ms": 15.3
        },
        {
          "name": "bash",
          "parameters": {"command": "az account show"},
          "result": "shboyer subscription",
          "timestamp": "2024-01-28T14:23:35",
          "duration_ms": 890.2
        },
        {
          "name": "bash",
          "parameters": {"command": "az group create && az staticwebapp create"},
          "result": "Created recorded-swa-session in rg-recorded-swa-session",
          "timestamp": "2024-01-28T14:24:00",
          "duration_ms": 15230.5
        },
        {
          "name": "bash",
          "parameters": {"command": "swa deploy . --deployment-token"},
          "result": null,
          "error": "Current directory cannot be identical to artifact folder",
          "timestamp": "2024-01-28T14:24:30",
          "duration_ms": 2100.0
        },
        {
          "name": "bash",
          "parameters": {"command": "mkdir -p dist && cp index.html dist/ && swa deploy ./dist"},
          "result": "Project deployed to https://salmon-rock-049daba0f.2.azurestaticapps.net",
          "timestamp": "2024-01-28T14:25:00",
          "duration_ms": 8500.3
        }
      ],
      "timestamp": "2024-01-28T14:23:28"
    }
  ],
  "errors": [
    {
      "type": "ToolError",
      "message": "SWA CLI artifact folder constraint - current directory cannot be identical to artifact folder",
      "context": {"resolution": "Created dist folder and copied files"},
      "timestamp": "2024-01-28T14:24:32"
    }
  ],
  "statistics": {
    "total_exchanges": 2,
    "total_tool_calls": 7,
    "total_errors": 1,
    "duration_seconds": 218,
    "tool_performance": {
      "avg_duration_ms": 3843.0,
      "tool_usage": {"bash": 5, "glob": 1}
    }
  }
}
```

## Guidelines

1. **Always scrub sensitive data** before sharing - the recorder does this automatically but verify no secrets leak
2. **Generate meaningful summaries** - don't just echo back what happened, synthesize the key points
3. **Be specific about problems** - vague feedback isn't helpful to developers
4. **Include context** - working directory, git branch, and model info help reproduce issues
5. **Respect user privacy** - don't share without explicit consent

## Verbose/Debug Mode Best Practices

To ensure maximum detail in recordings:

### Capture Everything

1. **User Input**: Record the exact prompt text, not a summary
2. **Tool Invocations**: Every tool call with full parameters
3. **Tool Responses**: Complete output (truncate only if necessary)
4. **Errors**: Full error messages with stack traces if available
5. **Timing**: How long each operation took

### What Verbose Output Looks Like

For each exchange, the output should show:

```
Exchange #2:
├── User: "help me deploy my app to azure"
├── Tools:
│   ├── bash(command="ls -la && cat index.html") → "total 8\n-rw-r--r--..."
│   ├── glob(pattern="**/*.{json,yaml,yml}") → ".github/workflows/..."
│   ├── bash(command="az account show") → "shboyer subscription"
│   ├── bash(command="az group create...") → "Created rg-..."
│   ├── bash(command="swa deploy .") → ERROR: "artifact folder constraint"
│   └── bash(command="mkdir -p dist && cp...") → "deployed to https://..."
├── Assistant: "Detected static HTML site..."
└── Duration: 2m 15s
```

### Common Issues That Reduce Verbosity

| Issue | Problem | Fix |
|-------|---------|-----|
| Summarized prompts | "User asked about deployment" | Record exact: "help me deploy my app to azure" |
| Missing tool params | `{...}` or empty | Include full parameters object |
| Truncated results | "..." | Keep full output, truncate only >2000 chars |
| Missing errors | Error not recorded | Always call `add_error()` on failures |
| No timing | `null` duration | Always call `start_tool_call()` before each tool |

### Debug Log Integration

If Copilot debug logs are available (typically in `~/.copilot/logs/`), the recorder can parse them:

```python
recorder = SessionRecorder(
    session_id="session-123",
    model="claude-sonnet-4-20250514",
    log_dir="~/.copilot/logs"  # Parse debug logs for extra detail
)
```

This adds `debug_logs` to the output with API calls, timing, token usage, and errors from the log files.
