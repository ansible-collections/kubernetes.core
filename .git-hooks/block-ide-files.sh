#!/usr/bin/env bash
# Block commits containing .claude/ or .vscode/ files

if git diff --cached --name-only | grep -qE "^\.claude/|^\.vscode/"; then
    echo "=========================================="
    echo "ERROR: Commit blocked!"
    echo "=========================================="
    echo ""
    echo "The following IDE/config files are staged:"
    git diff --cached --name-only | grep -E "^\.claude/|^\.vscode/"
    echo ""
    echo "Files from .claude/ and .vscode/ directories should not be committed."
    echo "Please unstage these files before committing."
    echo ""
    exit 1
fi

exit 0
