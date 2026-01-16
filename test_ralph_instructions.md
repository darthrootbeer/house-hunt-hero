# How to Test Ralph Wiggum

## Option 1: Test with Simple Task (Recommended)

1. **Create a simple test task:**
   ```bash
   cp RALPH_TEST_TASK.md RALPH_TASK.md
   ```

2. **Run a single iteration:**
   ```bash
   .cursor/ralph-scripts/ralph-once.sh
   ```

3. **Review the results:**
   - Check if `test_ralph_works.txt` was created
   - Check git log: `git log -1 --oneline`
   - Check progress: `cat .ralph/progress.md`
   - Check activity: `tail -20 .ralph/activity.log`

4. **Clean up after testing:**
   ```bash
   git reset --hard HEAD~1  # Undo the test commit
   rm test_ralph_works.txt  # Remove test file
   ```

## Option 2: Test with Current Task (More Realistic)

1. **Run a single iteration on your actual task:**
   ```bash
   .cursor/ralph-scripts/ralph-once.sh
   ```

2. **Review what Ralph did:**
   - Check git diff: `git diff HEAD~1`
   - Check which files were modified
   - Review `.ralph/progress.md` for what was accomplished

3. **If satisfied, continue with full loop:**
   ```bash
   .cursor/ralph-scripts/ralph-setup.sh
   ```

## What to Look For

✅ **Success indicators:**
- Files were created/modified
- Git commits were made
- `.ralph/progress.md` was updated
- No errors in `.ralph/errors.log`

⚠️ **Warning signs:**
- GUTTER signal in activity log
- Same command failing repeatedly
- No commits made
- Errors in `.ralph/errors.log`

## Monitoring During Execution

In another terminal, watch the activity log:
```bash
tail -f .ralph/activity.log
```

You'll see:
- Tool calls (READ, WRITE, SHELL)
- Token usage with health indicators (🟢🟡🔴)
- Any errors or warnings
