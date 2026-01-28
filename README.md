# CLI Session Recorder

A skill for GitHub Copilot CLI that records your sessions and generates shareable feedback for developer teams.

## Why Use This?

The `copilot --log-dir .logs --log-level debug` command produces debug logs that are hard to read and share. This skill creates **human-readable feedback** with an **AI-generated summary** plus **machine-readable data** for analysis.

## Installation

### Claude.ai / Claude Desktop

1. Download `cli-session-recorder.skill`
2. Go to **Settings** → **Skills**
3. Click **Upload Skill** and select the file

### GitHub Copilot CLI

```bash
# Clone and install to skills directory
gh repo clone spboyer/record-cli-session
mkdir -p ~/.copilot/skills
cp -r record-cli-session/cli-session-recorder ~/.copilot/skills/
```

Or as a one-liner:

```bash
gh repo clone spboyer/record-cli-session -- --depth 1 && cp -r record-cli-session/cli-session-recorder ~/.copilot/skills/ && rm -rf record-cli-session
```

## Usage

### 1. Start Recording

Use the explicit command or natural language:

```bash
/cli-session-recorder start
```

Or say: "record this session", "start recording", "capture feedback"

Copilot will confirm recording has started.

### 2. Work Normally

Just use Copilot as usual. Everything is captured automatically:
- Your prompts
- Copilot's responses
- Tool calls (grep, view, edit, bash, etc.)
- Errors and failures

### 3. Stop & Save

When you're done:

```bash
/cli-session-recorder stop
```

Or say: "stop recording", "save feedback"

Copilot will **auto-generate a summary**:

```
I've generated a summary of this session:

**Task**: Fix login authentication bug causing 401 errors
**Problems**: 
- Initial grep search returned too many results
- Had to inspect multiple files before finding the issue
**Outcome**: Success - Bug identified and fixed in src/auth.py

Accept this summary, or provide your own?
```

Just say "yes" to accept, or provide your own summary.

### 4. Share (Optional)

After saving, share via explicit commands:

```bash
/cli-session-recorder save           # Save to local file (default)
/cli-session-recorder save --gist    # Upload to GitHub Gist
/cli-session-recorder save --issue   # Create GitHub Issue
```

Or use natural language:

| Command | Result |
|---------|--------|
| *(default)* | Saves to `./feedback/feedback-YYYY-MM-DD-HHMM.md` |
| "share as gist" | Creates a GitHub Gist (private by default) |
| "create issue" | Opens a GitHub Issue in the current repo |

## Output Format

The feedback file has two sections:

### Human-Readable Summary
```markdown
# CLI Session Feedback
**Date**: 2024-01-28 14:23
**Model**: claude-sonnet-4-20250514
**Duration**: 15 minutes

## Summary
### Task Attempted
Fix login authentication bug causing 401 errors

### Problems Encountered
- Initial grep search returned too many results

### Outcome
Success - Bug identified and fixed in src/auth.py
```

### Machine-Readable Data
```json
{
  "metadata": { "session_id": "...", "model": "...", ... },
  "exchanges": [ { "user_prompt": "...", "assistant_response": "...", "tool_calls": [...] } ],
  "errors": [],
  "statistics": { "total_exchanges": 5, "total_tool_calls": 12 }
}
```

The JSON section can be fed to an LLM for automated analysis.

## Security

The recorder **automatically scrubs sensitive data** before saving:
- API keys and secrets
- Bearer tokens
- GitHub Personal Access Tokens
- OpenAI keys

Always review the output before sharing externally.

## Commands Quick Reference

Both explicit commands and natural language work. **Use explicit commands if natural language isn't giving good results.**

| Command | Natural Language | What Happens |
|---------|------------------|--------------|
| `/cli-session-recorder start` | "record this", "start recording" | Begin capturing |
| `/cli-session-recorder stop` | "stop recording" | Stop and generate summary |
| `/cli-session-recorder save` | "save feedback" | Save to local file |
| `/cli-session-recorder save --gist` | "share as gist" | Upload to GitHub Gist |
| `/cli-session-recorder save --issue` | "create issue", "report this" | Create GitHub Issue |
| `/cli-session-recorder status` | "show recording status" | Check if recording is active |

## File Structure

```
cli-session-recorder/
├── Skill.md              # Skill instructions for Claude
└── resources/
    ├── session_recorder.py    # Core recording logic
    ├── format_feedback.py     # Output generation
    ├── share_gist.py          # GitHub Gist integration
    ├── share_issue.py         # GitHub Issue integration
    └── feedback_format.md     # Output format spec
```

## Requirements

- `gh` CLI (for Gist/Issue sharing) - https://cli.github.com/
- Python 3.10+ (for scripts)

## License

Apache 2.0
