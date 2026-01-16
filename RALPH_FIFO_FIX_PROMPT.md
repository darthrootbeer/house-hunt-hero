# Fix: Ralph Script Hanging on FIFO Read

## Problem Description

The Ralph Wiggum scripts (`ralph-setup.sh`, `ralph-once.sh`, `ralph-loop.sh`) hang immediately after the user confirms to proceed. The script creates a log file and then freezes. If the user presses Ctrl-C, everything resumes normally.

## Root Cause

The hang occurs in the `run_iteration()` function in `.cursor/ralph-scripts/ralph-common.sh` around line 590. The issue is a **blocking FIFO (named pipe) read**:

1. The script creates a FIFO: `mkfifo "$fifo"`
2. It starts the agent/parser process in the background
3. It immediately tries to read from the FIFO: `while IFS= read -r line < "$fifo"`
4. **Reading from a FIFO blocks until a writer opens it**
5. If the parser hasn't opened the FIFO for writing yet, the read blocks indefinitely
6. This causes the entire script to freeze

When Ctrl-C is pressed, it interrupts the blocking read, which is why things resume.

## The Fix

Move the FIFO read to a background process and have the main script poll a signal file instead:

1. Start the agent/parser process in background (as before)
2. Start a **background process** to read from the FIFO (this can block without affecting the main script)
3. Have the background reader write signals to a temporary file
4. Have the main script poll that file instead of reading the FIFO directly

## Implementation

In `.cursor/ralph-scripts/ralph-common.sh`, find the `run_iteration()` function around line 530-630. Replace the blocking FIFO read section with this pattern:

```bash
# Start parser in background, reading from cursor-agent
(
  eval "$cmd \"$prompt\"" 2>&1 | "$script_dir/stream-parser.sh" "$workspace" > "$fifo"
) &
local agent_pid=$!

# Read signals from parser using a background process to avoid blocking
# The FIFO read blocks until a writer opens it, so we read in background
local signal=""
local signal_file
signal_file=$(mktemp)

# Background process to read from FIFO (this will block until writer opens it, but doesn't block main script)
(
  while IFS= read -r line < "$fifo" 2>/dev/null || true; do
    [[ -z "$line" ]] && continue
    echo "$line" >> "$signal_file"
    # Break on terminal signals
    case "$line" in
      "ROTATE"|"GUTTER"|"COMPLETE")
        break
        ;;
    esac
  done
) &
local reader_pid=$!

# Poll signal file while agent is running
while kill -0 $agent_pid 2>/dev/null; do
  if [[ -s "$signal_file" ]]; then
    local line
    line=$(tail -1 "$signal_file" 2>/dev/null | head -1)
    
    case "$line" in
      "ROTATE")
        printf "\r\033[K" >&2
        echo "🔄 Context rotation triggered - stopping agent..." >&2
        kill $agent_pid 2>/dev/null || true
        kill $reader_pid 2>/dev/null || true
        signal="ROTATE"
        break
        ;;
      "WARN")
        printf "\r\033[K" >&2
        echo "⚠️  Context warning - agent should wrap up soon..." >&2
        ;;
      "GUTTER")
        printf "\r\033[K" >&2
        echo "🚨 Gutter detected - agent may be stuck..." >&2
        signal="GUTTER"
        ;;
      "COMPLETE")
        printf "\r\033[K" >&2
        echo "✅ Agent signaled completion!" >&2
        signal="COMPLETE"
        ;;
    esac
  fi
  sleep 0.5
done

# Cleanup reader process
kill $reader_pid 2>/dev/null || true
wait $reader_pid 2>/dev/null || true
rm -f "$signal_file"
```

## Key Changes

1. **Background FIFO reader**: The blocking read happens in a background process (`&`), so it doesn't freeze the main script
2. **Signal file**: The background reader writes signals to a temp file instead of the main script reading directly
3. **Polling loop**: The main script polls the signal file while the agent runs, checking every 0.5 seconds
4. **Cleanup**: Properly kill and wait for the reader process, then remove the temp file

## Verification

After applying the fix:
1. Run `bash -n .cursor/ralph-scripts/ralph-common.sh` to verify syntax
2. Test with `ralph-setup.sh` - it should no longer hang after confirmation
3. The script should start the agent immediately without requiring Ctrl-C

## Why This Works

- The FIFO read still blocks, but now it's in a background process
- The main script continues executing and can respond to events
- Polling the signal file is non-blocking (just file I/O checks)
- The background reader will eventually unblock when the parser opens the FIFO for writing
