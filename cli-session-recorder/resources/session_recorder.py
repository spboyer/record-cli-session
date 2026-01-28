#!/usr/bin/env python3
"""
CLI Session Recorder - Captures and structures session data for feedback.
"""

import json
import os
import platform
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
from pathlib import Path


@dataclass
class ToolCall:
    """Represents a tool invocation during the session."""
    name: str
    parameters: dict
    result: Optional[str] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: Optional[float] = None
    retry_count: int = 0


@dataclass
class Exchange:
    """Represents a user prompt and assistant response pair."""
    user_prompt: str
    assistant_response: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    input_tokens_estimate: Optional[int] = None
    output_tokens_estimate: Optional[int] = None
    exchange_duration_ms: Optional[float] = None


@dataclass 
class EnvironmentContext:
    """Captures environment information for debugging."""
    os_name: str = ""
    os_version: str = ""
    shell: str = ""
    python_version: str = ""
    git_version: Optional[str] = None
    gh_cli_version: Optional[str] = None
    node_version: Optional[str] = None
    copilot_version: Optional[str] = None
    terminal: Optional[str] = None
    
    @classmethod
    def capture(cls) -> "EnvironmentContext":
        """Capture current environment context."""
        def run_cmd(cmd: list[str]) -> Optional[str]:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                return result.stdout.strip() if result.returncode == 0 else None
            except:
                return None
        
        return cls(
            os_name=platform.system(),
            os_version=platform.release(),
            shell=os.environ.get("SHELL", "unknown"),
            python_version=platform.python_version(),
            git_version=run_cmd(["git", "--version"]),
            gh_cli_version=run_cmd(["gh", "--version"]),
            node_version=run_cmd(["node", "--version"]),
            copilot_version=run_cmd(["copilot", "--version"]),
            terminal=os.environ.get("TERM_PROGRAM", os.environ.get("TERM", "unknown"))
        )


@dataclass
class SessionMetadata:
    """Session-level metadata."""
    session_id: str
    model: str = "unknown"
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    working_directory: str = ""
    git_branch: Optional[str] = None
    log_dir: Optional[str] = None


@dataclass
class SessionData:
    """Complete session recording."""
    metadata: SessionMetadata
    environment: Optional[EnvironmentContext] = None
    exchanges: list[Exchange] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    debug_logs: list[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "metadata": asdict(self.metadata),
            "environment": asdict(self.environment) if self.environment else None,
            "exchanges": [
                {
                    "user_prompt": e.user_prompt,
                    "assistant_response": e.assistant_response,
                    "tool_calls": [asdict(tc) for tc in e.tool_calls],
                    "timestamp": e.timestamp,
                    "input_tokens_estimate": e.input_tokens_estimate,
                    "output_tokens_estimate": e.output_tokens_estimate,
                    "exchange_duration_ms": e.exchange_duration_ms
                }
                for e in self.exchanges
            ],
            "errors": self.errors,
            "debug_logs": self.debug_logs,
            "statistics": self.get_statistics()
        }
    
    def get_statistics(self) -> dict:
        """Calculate session statistics."""
        total_tool_calls = sum(len(e.tool_calls) for e in self.exchanges)
        total_errors = len(self.errors)
        
        # Token estimates
        total_input_tokens = sum(e.input_tokens_estimate or 0 for e in self.exchanges)
        total_output_tokens = sum(e.output_tokens_estimate or 0 for e in self.exchanges)
        
        # Tool timing stats
        tool_durations = [
            tc.duration_ms for e in self.exchanges 
            for tc in e.tool_calls if tc.duration_ms is not None
        ]
        avg_tool_duration = sum(tool_durations) / len(tool_durations) if tool_durations else None
        
        # Tool usage breakdown
        tool_counts = {}
        for e in self.exchanges:
            for tc in e.tool_calls:
                tool_counts[tc.name] = tool_counts.get(tc.name, 0) + 1
        
        # Error breakdown
        error_types = {}
        for err in self.errors:
            err_type = err.get("type", "unknown")
            error_types[err_type] = error_types.get(err_type, 0) + 1
        
        return {
            "total_exchanges": len(self.exchanges),
            "total_tool_calls": total_tool_calls,
            "total_errors": total_errors,
            "duration_seconds": self._calculate_duration(),
            "token_estimates": {
                "total_input": total_input_tokens,
                "total_output": total_output_tokens,
                "total": total_input_tokens + total_output_tokens
            },
            "tool_performance": {
                "avg_duration_ms": avg_tool_duration,
                "tool_usage": tool_counts
            },
            "error_breakdown": error_types
        }
    
    def _calculate_duration(self) -> Optional[float]:
        """Calculate session duration in seconds."""
        if not self.metadata.end_time:
            return None
        try:
            start = datetime.fromisoformat(self.metadata.start_time)
            end = datetime.fromisoformat(self.metadata.end_time)
            return (end - start).total_seconds()
        except (ValueError, TypeError):
            return None


class SessionRecorder:
    """Records CLI session exchanges for feedback generation."""
    
    def __init__(self, session_id: str, model: str = "unknown", log_dir: Optional[str] = None):
        self.session = SessionData(
            metadata=SessionMetadata(
                session_id=session_id,
                model=model,
                working_directory=str(Path.cwd()),
                log_dir=log_dir
            )
        )
        self._current_exchange: Optional[Exchange] = None
        self._exchange_start_time: Optional[float] = None
        self._tool_start_time: Optional[float] = None
        self._recording = False
        self._log_dir = log_dir
    
    def start_recording(self, git_branch: Optional[str] = None, capture_environment: bool = True):
        """Begin recording the session."""
        self._recording = True
        self.session.metadata.git_branch = git_branch
        self.session.metadata.start_time = datetime.now().isoformat()
        
        if capture_environment:
            self.session.environment = EnvironmentContext.capture()
    
    def stop_recording(self):
        """Stop recording and finalize session."""
        self._recording = False
        self.session.metadata.end_time = datetime.now().isoformat()
        
        # Parse debug logs if available
        if self._log_dir:
            self._parse_debug_logs()
    
    def is_recording(self) -> bool:
        """Check if recording is active."""
        return self._recording
    
    def add_user_prompt(self, prompt: str):
        """Record a user prompt."""
        if not self._recording:
            return
        self._exchange_start_time = time.time()
        self._current_exchange = Exchange(
            user_prompt=prompt,
            assistant_response="",
            input_tokens_estimate=self._estimate_tokens(prompt)
        )
    
    def add_assistant_response(self, response: str):
        """Record an assistant response."""
        if not self._recording or not self._current_exchange:
            return
        self._current_exchange.assistant_response = response
        self._current_exchange.output_tokens_estimate = self._estimate_tokens(response)
        
        if self._exchange_start_time:
            self._current_exchange.exchange_duration_ms = (time.time() - self._exchange_start_time) * 1000
        
        self.session.exchanges.append(self._current_exchange)
        self._current_exchange = None
        self._exchange_start_time = None
    
    def start_tool_call(self):
        """Mark the start of a tool call for timing."""
        self._tool_start_time = time.time()
    
    def add_tool_call(self, name: str, parameters: dict, result: Optional[str] = None, 
                      error: Optional[str] = None, retry_count: int = 0):
        """Record a tool call within the current exchange."""
        if not self._recording or not self._current_exchange:
            return
        
        duration_ms = None
        if self._tool_start_time:
            duration_ms = (time.time() - self._tool_start_time) * 1000
            self._tool_start_time = None
        
        tool_call = ToolCall(
            name=name,
            parameters=parameters,
            result=result,
            error=error,
            duration_ms=duration_ms,
            retry_count=retry_count
        )
        self._current_exchange.tool_calls.append(tool_call)
    
    def add_error(self, error_type: str, message: str, context: Optional[dict] = None):
        """Record an error that occurred during the session."""
        if not self._recording:
            return
        self.session.errors.append({
            "type": error_type,
            "message": message,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate (~4 chars per token for English)."""
        return len(text) // 4
    
    def _parse_debug_logs(self):
        """Parse Copilot CLI debug logs from log_dir."""
        if not self._log_dir:
            return
        
        log_path = Path(self._log_dir)
        if not log_path.exists():
            return
        
        # Find recent log files
        log_files = sorted(log_path.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
        
        for log_file in log_files[:5]:  # Last 5 log files
            try:
                content = log_file.read_text()
                # Extract relevant debug info
                self._extract_log_entries(content, log_file.name)
            except Exception as e:
                self.session.debug_logs.append({
                    "file": log_file.name,
                    "error": f"Failed to parse: {str(e)}"
                })
    
    def _extract_log_entries(self, content: str, filename: str):
        """Extract meaningful entries from debug log content."""
        entries = []
        
        # Look for API calls, errors, timing info
        patterns = {
            "api_call": r'(POST|GET)\s+\S+api\S*',
            "error": r'(ERROR|WARN|error|warning)[\s:]+(.+)',
            "timing": r'(\d+)ms',
            "model": r'model["\s:]+([a-zA-Z0-9\-\.]+)',
            "token_usage": r'(tokens?|usage)["\s:]+(\d+)',
        }
        
        for line in content.split('\n'):
            entry = {"raw": line[:500]}  # Truncate long lines
            for pattern_name, pattern in patterns.items():
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    entry[pattern_name] = match.group(0)
            
            if len(entry) > 1:  # Has more than just raw
                entries.append(entry)
        
        if entries:
            self.session.debug_logs.append({
                "file": filename,
                "entries": entries[:100]  # Limit entries
            })
    
    def get_session_data(self) -> SessionData:
        """Get the complete session data."""
        return self.session
    
    def to_json(self, indent: int = 2) -> str:
        """Export session as JSON string."""
        return json.dumps(self.session.to_dict(), indent=indent)
    
    def scrub_sensitive_data(self, patterns: Optional[list[str]] = None):
        """Remove sensitive data from the session recording."""
        default_patterns = [
            r'(?i)(api[_-]?key|apikey|secret|password|token|credential)["\']?\s*[:=]\s*["\']?[\w\-]+',
            r'(?i)bearer\s+[\w\-\.]+',
            r'ghp_[a-zA-Z0-9]{36}',  # GitHub PAT
            r'sk-[a-zA-Z0-9]{48}',   # OpenAI key pattern
        ]
        patterns = patterns or default_patterns
        
        def scrub_text(text: str) -> str:
            for pattern in patterns:
                text = re.sub(pattern, '[REDACTED]', text)
            return text
        
        for exchange in self.session.exchanges:
            exchange.user_prompt = scrub_text(exchange.user_prompt)
            exchange.assistant_response = scrub_text(exchange.assistant_response)
            for tool_call in exchange.tool_calls:
                if tool_call.result:
                    tool_call.result = scrub_text(tool_call.result)
                tool_call.parameters = {
                    k: scrub_text(str(v)) if isinstance(v, str) else v
                    for k, v in tool_call.parameters.items()
                }


def generate_filename(prefix: str = "feedback") -> str:
    """Generate a timestamp-based filename."""
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    return f"{prefix}-{timestamp}.md"


if __name__ == "__main__":
    # Example usage
    recorder = SessionRecorder(
        session_id="test-123", 
        model="claude-sonnet-4-20250514",
        log_dir=".logs"
    )
    recorder.start_recording(git_branch="main")
    
    recorder.add_user_prompt("Help me fix this bug")
    recorder.start_tool_call()
    recorder.add_tool_call("view", {"path": "/src/app.py"}, result="file contents...")
    recorder.add_assistant_response("I found the issue in line 42...")
    
    recorder.stop_recording()
    print(recorder.to_json())
