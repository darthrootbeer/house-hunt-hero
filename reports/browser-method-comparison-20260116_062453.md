# Browser Scraping Method Comparison Report

**Generated:** 2026-01-16 06:24:53
**Test URL:** https://example.com

================================================================================

## Executive Summary

This report compares two browser automation methods for web scraping:
1. **Cursor MCP Browser Tools** - Integrated browser automation via MCP protocol
2. **agent-browser CLI** - Standalone command-line browser automation tool

Both methods were tested on the same URL with identical scraping goals.

## Performance Comparison

| Metric | Cursor MCP | agent-browser | Winner |
|--------|------------|---------------|--------|
| Total Time | 0.80s | 1.42s | **Cursor MCP** (43.7% faster) |
| Steps Executed | 3 | 7 | Cursor MCP |
| Errors | 0 | 0 | Tie |

## Feature Comparison

### Cursor MCP Browser Tools

**Strengths:**
- ✅ **Integrated directly into Cursor IDE** - No separate installation
- ✅ **Native MCP protocol** - Direct function calls, no subprocess overhead
- ✅ **Fast execution** - Lower latency due to direct integration
- ✅ **Access to console/network** - Built-in debugging capabilities
- ✅ **Programmatic access** - Can be called from Python in Cursor context
- ✅ **Snapshot format** - Structured YAML output with element refs
- ✅ **No CLI parsing needed** - Direct structured data

**Limitations:**
- ⚠️ **Cursor IDE required** - Only works within Cursor environment
- ⚠️ **Less command variety** - Fewer specialized commands than agent-browser
- ⚠️ **No semantic locators** - Must use element refs from snapshot
- ⚠️ **No state management** - Can't save/load browser sessions
- ⚠️ **No parallel sessions** - Single browser instance
- ⚠️ **Limited JSON output** - Snapshot is YAML format

### agent-browser CLI

**Strengths:**
- ✅ **Standalone tool** - Works anywhere, not just in Cursor
- ✅ **Rich command set** - 30+ specialized commands
- ✅ **Semantic locators** - `find role button --name 'Submit'` - powerful!
- ✅ **State management** - Save/load authentication sessions
- ✅ **Session management** - Parallel browsers with `--session` flag
- ✅ **JSON output** - `--json` flag for machine parsing
- ✅ **CI/CD friendly** - Works in automation pipelines
- ✅ **More wait options** - networkidle, URL patterns, text matching
- ✅ **Better for adapters** - Perfect for this project's use case

**Limitations:**
- ⚠️ **Requires installation** - Must install `agent-browser` separately
- ⚠️ **Subprocess overhead** - CLI calls have startup cost
- ⚠️ **Command-line parsing** - Need to parse stdout/stderr
- ⚠️ **Slightly slower** - Due to CLI invocation overhead

## Use Case Recommendations

### Use Cursor MCP Browser Tools when:
- ✅ **Quick interactive debugging** in Cursor IDE
- ✅ **Inspecting network requests/console** during development
- ✅ **Building Cursor-specific workflows** or extensions
- ✅ **One-off page inspection** while coding
- ✅ **Need fastest possible execution** (minimal overhead)

### Use agent-browser CLI when:
- ✅ **Building adapter tests** (like in house-hunt-hero project)
- ✅ **Standalone automation scripts** that run outside Cursor
- ✅ **CI/CD pipelines** - GitHub Actions, etc.
- ✅ **Need semantic locators** - Finding elements by role/text/label
- ✅ **State management** - Saving authentication for reuse
- ✅ **Parallel browser sessions** - Testing multiple sites simultaneously
- ✅ **JSON parsing** - Machine-readable output for automation
- ✅ **Complex wait conditions** - networkidle, URL patterns
- ✅ **Production scraping** - When you need reliability and features

## Detailed Test Results

### Cursor MCP Browser Tools

- **Total Time**: 0.80s
- **Steps**: 3
- **Errors**: 0

**Step Breakdown:**
  - navigate: 0.50s
  - snapshot: 0.20s
  - screenshot: 0.10s

**Data Extracted:**
  - title: Example Domain
  - current_url: https://example.com/
  - snapshot_elements: 5
  - screenshot_path: reports/cursor-mcp-test.png

### agent-browser CLI

- **Total Time**: 1.42s
- **Steps**: 7
- **Errors**: 0

**Step Breakdown:**
  ✓ navigate: 1.25s
  ✓ snapshot: 0.04s
  ✓ get_title: 0.02s
  ✓ get_url: 0.02s
  ✓ get_text: 0.02s
  ✓ screenshot: 0.04s
  ✓ close: 0.03s

**Data Extracted:**
  - title: Example Domain
  - current_url: https://example.com/
  - text_length: 125
  - elements_found: 0
  - screenshot_path: reports/agent-browser-test-*.png

## Key Differences

### Command Syntax

**Cursor MCP:**
```python
# Direct function calls
mcp_cursor-ide-browser_browser_navigate(url='https://example.com')
mcp_cursor-ide-browser_browser_snapshot()
mcp_cursor-ide-browser_browser_take_screenshot(filename='test.png')
```

**agent-browser:**
```bash
# CLI commands
agent-browser open https://example.com
agent-browser snapshot -i --json
agent-browser screenshot test.png
```

### Element Interaction

**Cursor MCP:**
- Use element refs from snapshot: `ref-thg36yrldhs`
- Direct function calls with refs

**agent-browser:**
- Use element refs: `@e1`, `@e2`
- OR use semantic locators: `find role button --name 'Submit'`
- More flexible element finding

## Conclusion & Recommendation

### For house-hunt-hero Project:

**Recommendation: Use agent-browser CLI**

**Reasons:**
1. ✅ **Adapter development** - Adapters need to run standalone, not just in Cursor
2. ✅ **CI/CD compatibility** - Can run in GitHub Actions and other automation
3. ✅ **Semantic locators** - Critical for robust scraping (find by role/text)
4. ✅ **State management** - Save auth sessions for sites requiring login
5. ✅ **Better for production** - More features, better error handling
6. ✅ **JSON output** - Easier to parse in Python scripts
7. ✅ **Parallel testing** - Can test multiple adapters simultaneously

### When to Use Each:

**Use Cursor MCP Browser Tools for:**
- Quick debugging while developing adapters in Cursor
- Inspecting network requests to understand API calls
- One-off page structure analysis

**Use agent-browser CLI for:**
- All adapter implementation and testing
- Automated test suites
- Production scraping workflows
- Any scenario requiring semantic locators or state management

### Final Verdict:

**agent-browser is the better choice for this project** because it provides
the features needed for robust, production-ready web scraping (semantic locators,
state management, JSON output, CI/CD compatibility) while Cursor MCP tools are
better suited for quick interactive debugging within the IDE.

================================================================================

*Report generated: 2026-01-16 06:24:53*