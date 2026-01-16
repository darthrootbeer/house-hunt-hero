#!/usr/bin/env python3
"""
Batch diagnostic runner for multiple platforms.

Generates diagnostic reports (screenshots, HTML, network logs, console errors)
for platforms returning zero properties or specified platforms.

Usage:
    python scripts/run_diagnostics.py --platforms maine_listings realty_of_maine
    python scripts/run_diagnostics.py --all-empty
    python scripts/run_diagnostics.py --all
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright

from src.ingestion.registry import get_adapters


def get_adapter_search_url(adapter):
    """Get search URL from adapter."""
    for attr in ['SEARCH_URL', 'search_url', 'BASE_URL', 'base_url']:
        url = getattr(adapter, attr, None)
        if url:
            return url
    return None


def capture_diagnostics(adapter, adapter_id):
    """
    Capture diagnostic information for a platform.
    
    Returns dict with:
    - screenshot_path: Path to screenshot file
    - html_path: Path to HTML snapshot file
    - network_requests: List of network requests
    - console_messages: List of console messages
    - timing_metrics: Dict of timing information
    - error: Error message if capture failed
    """
    diagnostics_dir = Path(f"reports/diagnostics/{adapter_id}")
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    
    diagnostics = {
        'screenshot_path': None,
        'html_path': None,
        'network_requests': [],
        'console_messages': [],
        'timing_metrics': {},
        'error': None,
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            # Capture network requests
            network_requests = []
            def handle_request(request):
                if request.resource_type in ['xhr', 'fetch', 'document']:
                    network_requests.append({
                        'url': request.url,
                        'method': request.method,
                        'type': request.resource_type,
                    })
            page.on('request', handle_request)
            
            # Capture console messages
            console_messages = []
            def handle_console(msg):
                if msg.type in ['error', 'warning']:
                    console_messages.append({
                        'type': msg.type,
                        'text': msg.text,
                    })
            page.on('console', handle_console)
            
            # Get search URL from adapter
            search_url = get_adapter_search_url(adapter)
            if not search_url:
                diagnostics['error'] = 'No search URL found'
                return diagnostics
            
            # Navigate and capture timing
            start_time = time.time()
            page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
            page_load_time = time.time() - start_time
            
            # Wait for potential dynamic content
            wait_start = time.time()
            try:
                page.wait_for_load_state('networkidle', timeout=10000)
            except:
                pass
            network_idle_time = time.time() - wait_start
            
            # Capture screenshot
            screenshot_path = diagnostics_dir / 'screenshot.png'
            page.screenshot(path=str(screenshot_path), full_page=True)
            diagnostics['screenshot_path'] = str(screenshot_path)
            
            # Capture HTML snapshot
            html_path = diagnostics_dir / 'page.html'
            html_content = page.content()
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            diagnostics['html_path'] = str(html_path)
            
            # Store captured data
            diagnostics['network_requests'] = network_requests
            diagnostics['console_messages'] = console_messages
            diagnostics['timing_metrics'] = {
                'page_load_seconds': round(page_load_time, 2),
                'network_idle_seconds': round(network_idle_time, 2),
                'total_seconds': round(page_load_time + network_idle_time, 2),
            }
            
            browser.close()
            
    except Exception as e:
        diagnostics['error'] = f"{type(e).__name__}: {str(e)[:200]}"
    
    return diagnostics


def save_diagnostic_report(adapter_id, diagnostics):
    """Save a diagnostic report for an adapter."""
    diagnostics_dir = Path(f"reports/diagnostics/{adapter_id}")
    report_path = diagnostics_dir / 'diagnostic_report.md'
    
    lines = [
        f"# Diagnostic Report: {adapter_id}",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    
    if diagnostics['error']:
        lines.extend([
            "## Error",
            "",
            f"⚠️ Diagnostic capture failed: {diagnostics['error']}",
            "",
        ])
    else:
        lines.extend([
            "## Timing Metrics",
            "",
        ])
        
        if diagnostics['timing_metrics']:
            for key, value in diagnostics['timing_metrics'].items():
                lines.append(f"- **{key.replace('_', ' ').title()}:** {value}s")
        
        lines.extend([
            "",
            "## Files Captured",
            "",
        ])
        
        if diagnostics['screenshot_path']:
            lines.append(f"- Screenshot: `{diagnostics['screenshot_path']}`")
        if diagnostics['html_path']:
            lines.append(f"- HTML: `{diagnostics['html_path']}`")
        
        lines.extend([
            "",
            "## Network Requests",
            "",
        ])
        
        if diagnostics['network_requests']:
            lines.append(f"Total: {len(diagnostics['network_requests'])}")
            lines.append("")
            for req in diagnostics['network_requests'][:20]:
                lines.append(f"- `{req['method']}` {req['type']}: {req['url'][:100]}")
        else:
            lines.append("- No network requests captured")
        
        lines.extend([
            "",
            "## Console Messages",
            "",
        ])
        
        if diagnostics['console_messages']:
            lines.append(f"Total: {len(diagnostics['console_messages'])}")
            lines.append("")
            for msg in diagnostics['console_messages'][:20]:
                lines.append(f"- **{msg['type'].upper()}:** {msg['text'][:200]}")
        else:
            lines.append("- No console errors or warnings")
        
        lines.append("")
    
    with open(report_path, 'w') as f:
        f.write("\n".join(lines))


def analyze_common_issues(results):
    """Analyze common issues across platforms."""
    issues = {
        'anti_bot': [],
        'console_errors': [],
        'slow_loading': [],
        'network_issues': [],
    }
    
    for adapter_id, diagnostics in results.items():
        if diagnostics['error']:
            if 'timeout' in diagnostics['error'].lower():
                issues['slow_loading'].append(adapter_id)
            else:
                issues['network_issues'].append(adapter_id)
            continue
        
        # Check for anti-bot indicators
        console_msgs = ' '.join(m['text'].lower() for m in diagnostics.get('console_messages', []))
        if any(keyword in console_msgs for keyword in ['cloudflare', 'captcha', 'blocked', 'bot']):
            issues['anti_bot'].append(adapter_id)
        
        # Check for console errors
        if diagnostics.get('console_messages'):
            issues['console_errors'].append(adapter_id)
        
        # Check for slow loading
        timing = diagnostics.get('timing_metrics', {})
        if timing.get('total_seconds', 0) > 15:
            issues['slow_loading'].append(adapter_id)
    
    return issues


def generate_summary_report(results, issues):
    """Generate summary report of all diagnostics."""
    lines = [
        "# Diagnostic Summary Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Platforms Analyzed:** {len(results)}",
        "",
        "---",
        "",
        "## Overview",
        "",
    ]
    
    successful = len([r for r in results.values() if not r.get('error')])
    failed = len([r for r in results.values() if r.get('error')])
    
    lines.extend([
        f"- **{successful}** platforms captured successfully",
        f"- **{failed}** platforms failed to capture",
        "",
        "---",
        "",
        "## Common Issues",
        "",
    ])
    
    if issues['anti_bot']:
        lines.extend([
            f"### 🛡️ Anti-Bot Protection Detected ({len(issues['anti_bot'])})",
            "",
            "These platforms appear to use anti-bot protection (Cloudflare, CAPTCHA, etc.):",
            "",
        ])
        for adapter_id in issues['anti_bot']:
            lines.append(f"- {adapter_id}")
        lines.extend(["", "**Recommendation:** Use stealth browser settings or delay between requests", ""])
    
    if issues['console_errors']:
        lines.extend([
            f"### ⚠️ Console Errors ({len(issues['console_errors'])})",
            "",
            "These platforms have JavaScript errors or warnings:",
            "",
        ])
        for adapter_id in issues['console_errors']:
            lines.append(f"- {adapter_id}")
        lines.extend(["", "**Recommendation:** Review console messages for clues about page structure", ""])
    
    if issues['slow_loading']:
        lines.extend([
            f"### 🐌 Slow Loading ({len(issues['slow_loading'])})",
            "",
            "These platforms take >15 seconds to load:",
            "",
        ])
        for adapter_id in issues['slow_loading']:
            lines.append(f"- {adapter_id}")
        lines.extend(["", "**Recommendation:** Increase timeout or optimize wait conditions", ""])
    
    if issues['network_issues']:
        lines.extend([
            f"### 🔌 Network Issues ({len(issues['network_issues'])})",
            "",
            "These platforms failed to load due to timeouts or connection errors:",
            "",
        ])
        for adapter_id in issues['network_issues']:
            error = results[adapter_id].get('error', 'Unknown error')
            lines.append(f"- {adapter_id}: {error[:100]}")
        lines.extend(["", "**Recommendation:** Check URL validity and network connectivity", ""])
    
    lines.extend([
        "",
        "---",
        "",
        "## Next Steps",
        "",
        "1. Review individual diagnostic reports in `reports/diagnostics/{adapter_id}/`",
        "2. Check screenshots for page structure",
        "3. Inspect HTML for correct selectors",
        "4. Address common issues flagged above",
        "5. Use `scripts/inspect_platform.py` for interactive investigation",
        "",
    ])
    
    return "\n".join(lines)


def run_diagnostics(adapter_names):
    """Run diagnostics for specified adapters."""
    all_adapters = get_adapters()
    
    # Filter to specified adapters
    adapters_to_run = [a for a in all_adapters if a.source_id in adapter_names]
    
    if not adapters_to_run:
        print(f"Error: No adapters found matching: {', '.join(adapter_names)}")
        return
    
    print("="*70)
    print("BATCH DIAGNOSTIC RUNNER")
    print("="*70)
    print(f"Running diagnostics for {len(adapters_to_run)} platforms")
    print()
    
    results = {}
    
    for i, adapter in enumerate(adapters_to_run, 1):
        adapter_id = adapter.source_id
        print(f"[{i}/{len(adapters_to_run)}] {adapter_id}...", end=" ", flush=True)
        
        diagnostics = capture_diagnostics(adapter, adapter_id)
        results[adapter_id] = diagnostics
        
        if diagnostics['error']:
            print(f"❌ {diagnostics['error'][:50]}")
        else:
            save_diagnostic_report(adapter_id, diagnostics)
            print("✅ Complete")
    
    print()
    print("="*70)
    print("GENERATING SUMMARY REPORT")
    print("="*70)
    
    # Analyze common issues
    issues = analyze_common_issues(results)
    
    # Generate summary report
    summary = generate_summary_report(results, issues)
    summary_path = Path("reports/diagnostics_summary.md")
    with open(summary_path, 'w') as f:
        f.write(summary)
    
    print(f"📊 Summary report saved: {summary_path}")
    
    # Print summary
    print()
    print("Summary:")
    print(f"  ✅ Successful: {len([r for r in results.values() if not r.get('error')])}")
    print(f"  ❌ Failed: {len([r for r in results.values() if r.get('error')])}")
    print(f"  🛡️  Anti-bot: {len(issues['anti_bot'])}")
    print(f"  ⚠️  Console errors: {len(issues['console_errors'])}")
    print(f"  🐌 Slow loading: {len(issues['slow_loading'])}")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run diagnostics for multiple platforms',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_diagnostics.py --platforms maine_listings realty_of_maine
  python scripts/run_diagnostics.py --all
        """
    )
    parser.add_argument(
        '--platforms',
        nargs='+',
        help='List of platform adapter names to diagnose'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run diagnostics on all adapters (WARNING: slow)'
    )
    
    args = parser.parse_args()
    
    if args.all:
        # Get all adapters
        all_adapters = get_adapters()
        adapter_names = [a.source_id for a in all_adapters]
        run_diagnostics(adapter_names)
    elif args.platforms:
        run_diagnostics(args.platforms)
    else:
        parser.print_help()
        print("\nError: Must specify --platforms or --all")
        sys.exit(1)


if __name__ == "__main__":
    main()
