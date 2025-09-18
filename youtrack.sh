#!/usr/bin/env bash
# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export YOUTRACK_DEFAULT_PROJECT_KEY=AGI
exec python3 main.py "$@"