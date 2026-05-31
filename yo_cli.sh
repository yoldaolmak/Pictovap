#!/bin/bash
# YO OS Image Upload CLI

# Usage: yo_cli.sh "5 foto yo 21312"
#        yo_cli.sh "3 foto yo 21312 gezievreni"

if [ $# -eq 0 ]; then
    echo "YO OS — Image Upload CLI"
    echo ""
    echo "Usage:"
    echo "  yo upload <count> foto yo <post_id> [site]"
    echo ""
    echo "Examples:"
    echo "  yo upload 5 foto yo 21312"
    echo "  yo upload 3 foto yo 21312 gezievreni"
    echo "  yo upload 1 foto yo 50000"
    echo ""
    echo "Notes:"
    echo "  - Takes N most recent images from ~/Downloads/"
    echo "  - Applies YO Blue/Teal filter"
    echo "  - Generates semantic metadata (with Anthropic API)"
    echo "  - Uploads to WordPress and attaches to post"
    echo "  - User edits: insert images into content"
    exit 1
fi

COMMAND="$1"

# Require API key for vision metadata
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not set"
    echo "    Using fallback metadata (basic alt/title/caption)"
    echo ""
fi

# Run orchestrator
cd /Users/KemalKaya/photo_ai
python3 yo_orchestrator.py "$COMMAND"
