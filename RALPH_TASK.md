---
task: Create a simple test file to verify Ralph Wiggum works
test_command: "test -f test_ralph_works.txt && grep -q 'Ralph works!' test_ralph_works.txt && echo 'Test passed' || echo 'Test failed'"
---

# Test Task: Verify Ralph Wiggum Installation

This is a simple test task to verify that Ralph Wiggum is working correctly.

## Success Criteria

1. [x] Create a file named `test_ralph_works.txt` in the project root
2. [x] Write the text "Ralph works! Test completed successfully." to the file
3. [x] Commit the file to git with message "ralph: test task completed"
4. [x] Verify the file exists and contains the expected text

## Context

This is a minimal test to ensure:
- Ralph can read task files
- Ralph can create files
- Ralph can commit to git
- The loop completes successfully

## Expected Output

After running, you should see:
- A new file `test_ralph_works.txt` in the project root
- A git commit with the test file
- Updated `.ralph/progress.md` with completion status
