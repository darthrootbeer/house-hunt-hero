#!/bin/bash
# Quick test to see if cursor-agent is authenticated

echo "Testing cursor-agent authentication..."
echo "If you see 'Press any key to sign in...', you need to authenticate first."
echo ""

# Try a simple command with timeout
timeout 3 cursor-agent -p "echo test" 2>&1 | grep -q "Press any key" && {
    echo "❌ cursor-agent requires authentication"
    echo ""
    echo "To fix:"
    echo "  1. Run: cursor-agent -p 'test'"
    echo "  2. Follow the sign-in prompts"
    echo "  3. Then try ralph-once.sh again"
    exit 1
} || {
    echo "✓ cursor-agent appears to be authenticated"
    exit 0
}
