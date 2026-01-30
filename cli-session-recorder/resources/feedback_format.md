# Feedback Output Format Specification

This document describes the output format for CLI session feedback files.

## ⚠️ MANDATORY: Complete Exchange Data

**Every feedback report MUST contain the full `exchanges` array.** This is not optional.

A valid report includes:
- ✅ Complete `exchanges[]` with all user prompts, tool calls, and responses
- ✅ Full `tool_calls[]` with name, parameters, result, and timing
- ✅ All errors with context

An invalid/incomplete report:
- ❌ Summary-only without exchanges array
- ❌ Missing tool call details
- ❌ Truncated or summarized responses

**Never save a report without comprehensive exchange data.**

## Key Requirement: VERBOSE OUTPUT

**The output must capture full detail for debugging purposes.** This includes:
- Exact user prompts (not summaries)
- All tool calls with complete parameters and results
- Full assistant responses
- Timing information for performance analysis
- Complete error context

## File Naming

Files are named with a timestamp pattern:
```
feedback-YYYY-MM-DD-HHMM.md
```

Example: `feedback-2024-01-28-1423.md`

## Document Structure

### Human-Readable Header

The top portion is designed for human readers and contains:

| Field | Description |
|-------|-------------|
| Date | Session start timestamp |
| Model | The AI model used (e.g., claude-sonnet-4-20250514) |
| Duration | Human-friendly duration (e.g., "15 minutes") |
| Session ID | Unique identifier for the session |
| Working Directory | Where the session was run |
| Git Branch | Current branch (if in a git repo) |

### Summary Section

| Section | Purpose |
|---------|---------|
| Task Attempted | AI-generated description of the user's goal |
| Problems Encountered | List of issues, errors, or unexpected behaviors |
| Outcome | Success/Failure/Partial with brief description |

### Statistics

Quick metrics about the session:
- Total exchanges (prompt/response pairs)
- Tool calls made
- Errors encountered

### Machine-Readable Section

A JSON code block containing the complete session data. **This MUST include detailed exchange data.**

#### Minimal vs Verbose Output Comparison

❌ **BAD (minimal/summary)** - Missing detail:
```json
{
  "session_id": "session-123",
  "task_summary": "Deploy to Azure",
  "outcome": "Success",
  "errors": []
}
```

✅ **GOOD (verbose)** - Full detail:
```json
{
  "metadata": {
    "session_id": "session-20260128-163354",
    "model": "claude-sonnet-4-20250514",
    "start_time": "2026-01-28T16:34:12.153180",
    "end_time": "2026-01-28T16:38:46.981910",
    "working_directory": "/Users/shboyer/github/plain-html-test",
    "git_branch": "main"
  },
  "exchanges": [
    {
      "user_prompt": "start",
      "assistant_response": "Recording started for session-20260128-163354",
      "tool_calls": [
        {
          "name": "bash",
          "parameters": {"command": "git branch --show-current"},
          "result": "main",
          "timestamp": "2026-01-28T16:34:15.000000",
          "duration_ms": 45.2
        }
      ],
      "timestamp": "2026-01-28T16:34:12.153180"
    },
    {
      "user_prompt": "help me deploy my app to azure",
      "assistant_response": "Detected static HTML site. Recommended Azure Static Web Apps. Created resource group and SWA, deployed successfully.",
      "tool_calls": [
        {
          "name": "bash",
          "parameters": {"command": "ls -la && cat index.html"},
          "result": "index.html - Hello World static site",
          "duration_ms": 120.5
        },
        {
          "name": "glob",
          "parameters": {"pattern": "**/*.{json,yaml,yml}"},
          "result": ".github/workflows/run_test_deploy.yml",
          "duration_ms": 15.3
        },
        {
          "name": "bash",
          "parameters": {"command": "az account show"},
          "result": "shboyer subscription",
          "duration_ms": 890.2
        },
        {
          "name": "bash",
          "parameters": {"command": "az group create && az staticwebapp create"},
          "result": "Created recorded-swa-session in rg-recorded-swa-session",
          "duration_ms": 15230.5
        },
        {
          "name": "bash",
          "parameters": {"command": "swa deploy . --deployment-token"},
          "result": null,
          "error": "Error: Current directory cannot be identical to artifact folder",
          "duration_ms": 2100.0
        },
        {
          "name": "bash",
          "parameters": {"command": "mkdir -p dist && cp index.html dist/ && swa deploy ./dist"},
          "result": "Project deployed to https://salmon-rock-049daba0f.2.azurestaticapps.net",
          "duration_ms": 8500.3
        }
      ],
      "timestamp": "2026-01-28T16:35:30.000000"
    }
  ],
  "errors": [
    {
      "type": "ToolError",
      "message": "SWA CLI artifact folder constraint - current directory cannot be identical to artifact folder",
      "context": {"resolution": "Created dist folder and copied files"},
      "timestamp": "2026-01-28T16:36:45.000000"
    }
  ],
  "statistics": {
    "total_exchanges": 2,
    "total_tool_calls": 7,
    "total_errors": 1,
    "duration_seconds": 218
  }
}
```

#### Complete Schema

```json
{
  "metadata": {
    "session_id": "string",
    "model": "string",
    "start_time": "ISO8601",
    "end_time": "ISO8601",
    "working_directory": "string",
    "git_branch": "string|null",
    "log_dir": "string|null"
  },
  "environment": {
    "os_name": "string",
    "os_version": "string",
    "shell": "string",
    "python_version": "string",
    "git_version": "string|null",
    "gh_cli_version": "string|null",
    "node_version": "string|null",
    "copilot_version": "string|null",
    "terminal": "string|null"
  },
  "exchanges": [
    {
      "user_prompt": "string",
      "assistant_response": "string",
      "tool_calls": [
        {
          "name": "string",
          "parameters": {},
          "result": "string|null",
          "error": "string|null",
          "timestamp": "ISO8601",
          "duration_ms": "number|null",
          "retry_count": "number"
        }
      ],
      "timestamp": "ISO8601",
      "input_tokens_estimate": "number|null",
      "output_tokens_estimate": "number|null",
      "exchange_duration_ms": "number|null"
    }
  ],
  "errors": [
    {
      "type": "string",
      "message": "string",
      "context": {},
      "timestamp": "ISO8601"
    }
  ],
  "debug_logs": [
    {
      "file": "string",
      "entries": [
        {
          "raw": "string",
          "api_call": "string|null",
          "error": "string|null",
          "timing": "string|null",
          "model": "string|null",
          "token_usage": "string|null"
        }
      ]
    }
  ],
  "statistics": {
    "total_exchanges": "number",
    "total_tool_calls": "number",
    "total_errors": "number",
    "duration_seconds": "number|null",
    "token_estimates": {
      "total_input": "number",
      "total_output": "number",
      "total": "number"
    },
    "tool_performance": {
      "avg_duration_ms": "number|null",
      "tool_usage": {
        "tool_name": "number"
      }
    },
    "error_breakdown": {
      "error_type": "number"
    }
  }
}
```

## Usage with LLMs

The machine-readable JSON section can be extracted and fed to an LLM for:
- Automated analysis of session patterns
- Identifying common issues
- Generating improvement suggestions
- Aggregating feedback across sessions

### Extraction Pattern

To extract the JSON from a feedback file:

```python
import re
import json

def extract_json(feedback_content: str) -> dict:
    pattern = r'```json\n(.*?)\n```'
    match = re.search(pattern, feedback_content, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    return None
```

## Sensitive Data

The recorder automatically scrubs common sensitive patterns:
- API keys and secrets
- Bearer tokens
- GitHub PATs (ghp_...)
- OpenAI keys (sk-...)

Custom patterns can be added via the `scrub_sensitive_data()` method.
