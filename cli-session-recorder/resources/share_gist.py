#!/usr/bin/env python3
"""
Share feedback via GitHub Gist using the gh CLI.
"""

import subprocess
import json
from pathlib import Path
from typing import Optional


def create_gist(
    filepath: Path,
    description: Optional[str] = None,
    public: bool = False
) -> Optional[str]:
    """
    Create a GitHub Gist from a feedback file.
    
    Args:
        filepath: Path to the feedback file
        description: Gist description (defaults to filename)
        public: Whether the gist should be public (default: private/secret)
    
    Returns:
        URL of the created gist, or None if failed
    """
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        return None
    
    if description is None:
        description = f"CLI Session Feedback - {filepath.name}"
    
    cmd = ["gh", "gist", "create", str(filepath), "--desc", description]
    
    if public:
        cmd.append("--public")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        gist_url = result.stdout.strip()
        return gist_url
    except subprocess.CalledProcessError as e:
        print(f"Error creating gist: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: 'gh' CLI not found. Install it from https://cli.github.com/")
        return None


def list_gists(limit: int = 10) -> list[dict]:
    """List recent gists."""
    try:
        result = subprocess.run(
            ["gh", "gist", "list", "--limit", str(limit), "--json", "id,description,url,createdAt"],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        return []


def delete_gist(gist_id: str) -> bool:
    """Delete a gist by ID."""
    try:
        subprocess.run(
            ["gh", "gist", "delete", gist_id, "--yes"],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: share_gist.py <filepath> [--public] [--description 'desc']")
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    public = "--public" in sys.argv
    
    desc = None
    if "--description" in sys.argv:
        desc_idx = sys.argv.index("--description") + 1
        if desc_idx < len(sys.argv):
            desc = sys.argv[desc_idx]
    
    url = create_gist(filepath, description=desc, public=public)
    if url:
        print(f"Gist created: {url}")
    else:
        sys.exit(1)
