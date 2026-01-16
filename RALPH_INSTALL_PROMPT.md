# Minimal Prompt: Install Ralph Wiggum for Cursor

Copy and paste this prompt into a new Cursor instance:

---

**Install and configure Ralph Wiggum for Cursor from https://github.com/agrimsingh/ralph-wiggum-cursor**

1. Clone or download the repository scripts to `.cursor/ralph-scripts/` directory
2. Make all scripts executable (`chmod +x .cursor/ralph-scripts/*.sh`)
3. Verify `cursor-agent` CLI is installed (`cursor-agent --version`)
4. Initialize Ralph in this project (create `.ralph/` directory with required files)
5. Create a simple test `RALPH_TASK.md` to verify it works
6. Test with `ralph-once.sh` to confirm installation

Requirements:
- Git repository (already initialized)
- `cursor-agent` CLI installed
- `jq` installed (for stream-parser)
- Optional: `gum` for enhanced UI

Verify installation by running `.cursor/ralph-scripts/ralph-once.sh` with a simple test task.

---
