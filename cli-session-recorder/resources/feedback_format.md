# Feedback Output Format Specification

This document describes the output format for CLI session feedback files.

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

A JSON code block containing the complete session data:

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
