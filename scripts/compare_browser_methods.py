#!/usr/bin/env python3
"""
Compare Cursor MCP browser tools vs agent-browser CLI for web scraping.
Runs both tests and generates a comparison report.
"""

import json
import time
from datetime import datetime
from test_cursor_browser_scraping import run_cursor_browser_test
from test_agent_browser_scraping import run_agent_browser_test


def generate_comparison_report(cursor_results: dict, agent_results: dict) -> str:
    """Generate a detailed comparison report"""
    
    report = []
    report.append("# Browser Scraping Method Comparison Report")
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("\n" + "=" * 80)
    
    # Executive Summary
    report.append("\n## Executive Summary")
    report.append("\nThis report compares two browser automation methods for web scraping:")
    report.append("1. **Cursor MCP Browser Tools** - Integrated browser automation via MCP")
    report.append("2. **agent-browser CLI** - Standalone command-line browser automation tool")
    
    # Performance Comparison
    report.append("\n## Performance Comparison")
    report.append("\n| Metric | Cursor MCP | agent-browser | Winner |")
    report.append("|--------|------------|---------------|--------|")
    
    cursor_time = cursor_results.get("total_time", 0)
    agent_time = agent_results.get("total_time", 0)
    
    if cursor_time < agent_time:
        time_winner = "Cursor MCP"
        time_diff = f"{((agent_time - cursor_time) / agent_time * 100):.1f}% faster"
    else:
        time_winner = "agent-browser"
        time_diff = f"{((cursor_time - agent_time) / cursor_time * 100):.1f}% faster"
    
    report.append(f"| Total Time | {cursor_time:.2f}s | {agent_time:.2f}s | {time_winner} ({time_diff}) |")
    
    cursor_steps = len(cursor_results.get("steps", []))
    agent_steps = len(agent_results.get("steps", []))
    report.append(f"| Steps Executed | {cursor_steps} | {agent_steps} | {'Cursor MCP' if cursor_steps < agent_steps else 'agent-browser'} |")
    
    cursor_errors = len(cursor_results.get("errors", []))
    agent_errors = len(agent_results.get("errors", []))
    error_winner = "Cursor MCP" if cursor_errors < agent_errors else "agent-browser" if agent_errors < cursor_errors else "Tie"
    report.append(f"| Errors | {cursor_errors} | {agent_errors} | {error_winner} |")
    
    # Feature Comparison
    report.append("\n## Feature Comparison")
    report.append("\n### Cursor MCP Browser Tools")
    report.append("\n**Strengths:**")
    report.append("- ✅ Integrated directly into Cursor IDE")
    report.append("- ✅ No separate installation required")
    report.append("- ✅ Native MCP protocol integration")
    report.append("- ✅ Can be called programmatically from Python")
    report.append("- ✅ Access to browser console and network requests")
    
    report.append("\n**Limitations:**")
    report.append("- ⚠️ Requires Cursor IDE environment")
    report.append("- ⚠️ Less flexible for standalone scripts")
    report.append("- ⚠️ May have rate limiting in IDE context")
    
    report.append("\n### agent-browser CLI")
    report.append("\n**Strengths:**")
    report.append("- ✅ Standalone tool - works anywhere")
    report.append("- ✅ Rich command set (snapshot, semantic locators, state management)")
    report.append("- ✅ JSON output for parsing")
    report.append("- ✅ Session management for parallel browsers")
    report.append("- ✅ State save/load for authentication")
    report.append("- ✅ Semantic locators (find by role, text, label)")
    report.append("- ✅ Can be used in CI/CD pipelines")
    report.append("- ✅ Works outside of Cursor")
    
    report.append("\n**Limitations:**")
    report.append("- ⚠️ Requires separate installation")
    report.append("- ⚠️ Command-line interface (less programmatic)")
    report.append("- ⚠️ Subprocess overhead")
    
    # Use Case Recommendations
    report.append("\n## Use Case Recommendations")
    report.append("\n### Use Cursor MCP Browser Tools when:")
    report.append("- ✅ You're working within Cursor IDE")
    report.append("- ✅ You need quick interactive debugging")
    report.append("- ✅ You want to inspect network requests/console")
    report.append("- ✅ You're building Cursor-specific workflows")
    report.append("- ✅ You need programmatic access from Python in Cursor")
    
    report.append("\n### Use agent-browser CLI when:")
    report.append("- ✅ You need standalone automation scripts")
    report.append("- ✅ You're building CI/CD pipelines")
    report.append("- ✅ You need semantic locators (find by role/text)")
    report.append("- ✅ You need state management (save/load auth)")
    report.append("- ✅ You need parallel browser sessions")
    report.append("- ✅ You're working outside Cursor IDE")
    report.append("- ✅ You need JSON output for parsing")
    report.append("- ✅ You're building adapter tests (like in this project)")
    
    # Detailed Results
    report.append("\n## Detailed Test Results")
    
    report.append("\n### Cursor MCP Browser Tools")
    report.append(f"\n- **Total Time**: {cursor_time:.2f}s")
    report.append(f"- **Steps**: {cursor_steps}")
    report.append(f"- **Errors**: {cursor_errors}")
    if cursor_results.get("data_extracted"):
        report.append("\n**Data Extracted:**")
        for key, value in cursor_results["data_extracted"].items():
            report.append(f"  - {key}: {value}")
    
    report.append("\n### agent-browser CLI")
    report.append(f"\n- **Total Time**: {agent_time:.2f}s")
    report.append(f"- **Steps**: {agent_steps}")
    report.append(f"- **Errors**: {agent_errors}")
    if agent_results.get("data_extracted"):
        report.append("\n**Data Extracted:**")
        for key, value in agent_results["data_extracted"].items():
            if isinstance(value, str) and len(value) > 100:
                report.append(f"  - {key}: {value[:100]}...")
            else:
                report.append(f"  - {key}: {value}")
    
    # Step-by-Step Comparison
    report.append("\n## Step-by-Step Comparison")
    report.append("\n| Step | Cursor MCP | agent-browser | Notes |")
    report.append("|------|------------|---------------|-------|")
    
    max_steps = max(cursor_steps, agent_steps)
    for i in range(max_steps):
        cursor_step = cursor_results.get("steps", [])[i] if i < cursor_steps else None
        agent_step = agent_results.get("steps", [])[i] if i < agent_steps else None
        
        cursor_info = f"{cursor_step['step']} ({cursor_step['duration']:.2f}s)" if cursor_step else "-"
        agent_info = f"{agent_step['step']} ({agent_step['duration']:.2f}s)" if agent_step else "-"
        
        notes = []
        if cursor_step and agent_step:
            if cursor_step['duration'] < agent_step['duration']:
                notes.append("Cursor faster")
            elif agent_step['duration'] < cursor_step['duration']:
                notes.append("agent-browser faster")
        
        report.append(f"| {i+1} | {cursor_info} | {agent_info} | {'; '.join(notes) if notes else ''} |")
    
    # Conclusion
    report.append("\n## Conclusion")
    report.append("\nBoth methods are effective for browser automation, but serve different purposes:")
    report.append("\n- **For this project (house-hunt-hero)**: agent-browser is likely better suited")
    report.append("  because adapters need to run standalone, work in CI/CD, and benefit from")
    report.append("  semantic locators and state management.")
    report.append("\n- **For interactive debugging in Cursor**: MCP browser tools are more convenient")
    report.append("  for quick inspection and testing within the IDE.")
    report.append("\n**Recommendation**: Use agent-browser for adapter development and testing,")
    report.append("and Cursor MCP tools for quick interactive debugging when needed.")
    
    return "\n".join(report)


def main():
    """Run both tests and generate comparison report"""
    print("\n" + "=" * 80)
    print("BROWSER SCRAPING METHOD COMPARISON")
    print("=" * 80)
    
    # Run Cursor browser test
    print("\n[1/3] Running Cursor MCP Browser Tools test...")
    cursor_results = run_cursor_browser_test()
    
    print("\n" + "-" * 80)
    
    # Run agent-browser test
    print("\n[2/3] Running agent-browser CLI test...")
    agent_results = run_agent_browser_test()
    
    print("\n" + "-" * 80)
    
    # Generate comparison report
    print("\n[3/3] Generating comparison report...")
    report = generate_comparison_report(cursor_results, agent_results)
    
    # Save report
    report_path = f"reports/browser-method-comparison-{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"\n✓ Report saved to: {report_path}")
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print(report.split("## Conclusion")[0])  # Print summary before conclusion
    
    return report_path


if __name__ == "__main__":
    main()
