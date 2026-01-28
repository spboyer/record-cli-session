#!/usr/bin/env python3
"""
CLI Session Recorder - Captures and structures session data for feedback.
"""

import json
import re
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


@dataclass
class Exchange:
    """Represents a user prompt and assistant response pair."""
    user_prompt: str
    assistant_response: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SessionMetadata:
    """Session-level metadata."""
    session_id: str
    model: str = "unknown"
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    working_directory: str = ""
    git_branch: Optional[str] = None
    

@dataclass
class SessionData:
    """Complete session recording."""
    metadata: SessionMetadata
    exchanges: list[Exchange] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "metadata": asdict(self.metadata),
            "exchanges": [
                {
                    "user_prompt": e.user_prompt,
                    "assistant_response": e.assistant_response,
                    "tool_calls": [asdict(tc) for tc in e.tool_calls],
                    "timestamp": e.timestamp
                }
                for e in self.exchanges
            ],
            "errors": self.errors,
            "statistics": self.get_statistics()
        }
    
    def get_statistics(self) -> dict:
        """Calculate session statistics."""
        total_tool_calls = sum(len(e.tool_calls) for e in self.exchanges)
        total_errors = len(self.errors)
        
        return {
            "total_exchanges": len(self.exchanges),
            "total_tool_calls": total_tool_calls,
            "total_errors": total_errors,
            "duration_seconds": self._calculate_duration()
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
    
    def __init__(self, session_id: str, model: str = "unknown"):
        self.session = SessionData(
            metadata=SessionMetadata(
                session_id=session_id,
                model=model,
                working_directory=str(Path.cwd())
            )
        )
        self._current_exchange: Optional[Exchange] = None
        self._recording = False
    
    def start_recording(self, git_branch: Optional[str] = None):
        """Begin recording the session."""
        self._recording = True
        self.session.metadata.git_branch = git_branch
        self.session.metadata.start_time = datetime.now().isoformat()
    
    def stop_recording(self):
        """Stop recording and finalize session."""
        self._recording = False
        self.session.metadata.end_time = datetime.now().isoformat()
    
    def is_recording(self) -> bool:
        """Check if recording is active."""
        return self._recording
    
    def add_user_prompt(self, prompt: str):
        """Record a user prompt."""
        if not self._recording:
            return
        self._current_exchange = Exchange(
            user_prompt=prompt,
            assistant_response=""
        )
    
    def add_assistant_response(self, response: str):
        """Record an assistant response."""
        if not self._recording or not self._current_exchange:
            return
        self._current_exchange.assistant_response = response
        self.session.exchanges.append(self._current_exchange)
        self._current_exchange = None
    
    def add_tool_call(self, name: str, parameters: dict, result: Optional[str] = None, error: Optional[str] = None):
        """Record a tool call within the current exchange."""
        if not self._recording or not self._current_exchange:
            return
        tool_call = ToolCall(
            name=name,
            parameters=parameters,
            result=result,
            error=error
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
    recorder = SessionRecorder(session_id="test-123", model="claude-sonnet-4-20250514")
    recorder.start_recording(git_branch="main")
    
    recorder.add_user_prompt("Help me fix this bug")
    recorder.add_tool_call("view", {"path": "/src/app.py"}, result="file contents...")
    recorder.add_assistant_response("I found the issue in line 42...")
    
    recorder.stop_recording()
    print(recorder.to_json())
