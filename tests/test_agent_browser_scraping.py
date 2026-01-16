#!/usr/bin/env python3
"""
Test web scraping using agent-browser CLI.
This test performs the same scraping task as the Cursor browser test.
"""

import subprocess
import json
import time
from typing import Dict, Any, List

def run_agent_browser_command(cmd: List[str]) -> Dict[str, Any]:
    """Run an agent-browser command and return results"""
    try:
        start = time.time()
        result = subprocess.run(
            ["agent-browser"] + cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        duration = time.time() - start
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": duration,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out",
            "duration": 30.0,
            "returncode": -1
        }
    except FileNotFoundError:
        return {
            "success": False,
            "stdout": "",
            "stderr": "agent-browser not found in PATH",
            "duration": 0.0,
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "duration": 0.0,
            "returncode": -1
        }


def test_agent_browser_scraping(url: str) -> Dict[str, Any]:
    """Scrape a page using agent-browser CLI"""
    results = {
        "method": "agent-browser CLI",
        "url": url,
        "start_time": time.time(),
        "steps": [],
        "data_extracted": {},
        "errors": []
    }
    
    try:
        # Step 1: Navigate to page
        nav_result = run_agent_browser_command(["open", url])
        results["steps"].append({
            "step": "navigate",
            "action": f"agent-browser open {url}",
            "duration": nav_result["duration"],
            "success": nav_result["success"]
        })
        
        if not nav_result["success"]:
            results["errors"].append(f"Navigation failed: {nav_result['stderr']}")
            return results
        
        # Step 2: Get interactive elements snapshot
        snapshot_result = run_agent_browser_command(["snapshot", "-i", "--json"])
        results["steps"].append({
            "step": "snapshot",
            "action": "agent-browser snapshot -i --json",
            "duration": snapshot_result["duration"],
            "success": snapshot_result["success"]
        })
        
        if snapshot_result["success"]:
            try:
                snapshot_data = json.loads(snapshot_result["stdout"])
                results["data_extracted"]["elements_found"] = len(snapshot_data.get("elements", []))
                results["data_extracted"]["snapshot_keys"] = list(snapshot_data.keys())
            except json.JSONDecodeError:
                results["data_extracted"]["snapshot_text"] = snapshot_result["stdout"][:200]
        
        # Step 3: Get page title
        title_result = run_agent_browser_command(["get", "title"])
        results["steps"].append({
            "step": "get_title",
            "action": "agent-browser get title",
            "duration": title_result["duration"],
            "success": title_result["success"]
        })
        
        if title_result["success"]:
            results["data_extracted"]["title"] = title_result["stdout"].strip()
        
        # Step 4: Get page URL
        url_result = run_agent_browser_command(["get", "url"])
        results["steps"].append({
            "step": "get_url",
            "action": "agent-browser get url",
            "duration": url_result["duration"],
            "success": url_result["success"]
        })
        
        if url_result["success"]:
            results["data_extracted"]["current_url"] = url_result["stdout"].strip()
        
        # Step 5: Get body text
        text_result = run_agent_browser_command(["get", "text", "body"])
        results["steps"].append({
            "step": "get_text",
            "action": "agent-browser get text body",
            "duration": text_result["duration"],
            "success": text_result["success"]
        })
        
        if text_result["success"]:
            text_content = text_result["stdout"].strip()
            results["data_extracted"]["text_length"] = len(text_content)
            results["data_extracted"]["text_preview"] = text_content[:200]
        
        # Step 6: Take screenshot
        screenshot_path = f"reports/agent-browser-test-{int(time.time())}.png"
        screenshot_result = run_agent_browser_command(["screenshot", screenshot_path])
        results["steps"].append({
            "step": "screenshot",
            "action": f"agent-browser screenshot {screenshot_path}",
            "duration": screenshot_result["duration"],
            "success": screenshot_result["success"]
        })
        
        if screenshot_result["success"]:
            results["data_extracted"]["screenshot_path"] = screenshot_path
        
        # Step 7: Close browser
        close_result = run_agent_browser_command(["close"])
        results["steps"].append({
            "step": "close",
            "action": "agent-browser close",
            "duration": close_result["duration"],
            "success": close_result["success"]
        })
        
    except Exception as e:
        results["errors"].append(f"Unexpected error: {str(e)}")
    
    results["total_time"] = time.time() - results["start_time"]
    return results


def run_agent_browser_test():
    """Run the agent-browser test"""
    print("=" * 60)
    print("AGENT-BROWSER CLI TEST")
    print("=" * 60)
    
    # Test with the same URL
    test_url = "https://example.com"
    
    results = test_agent_browser_scraping(test_url)
    
    print(f"\nMethod: {results['method']}")
    print(f"URL: {results['url']}")
    print(f"Total Time: {results['total_time']:.2f}s")
    print(f"\nSteps ({len(results['steps'])}):")
    for step in results['steps']:
        status = "✓" if step.get("success", False) else "✗"
        print(f"  {status} {step['step']}: {step['duration']:.2f}s")
    
    if results['data_extracted']:
        print(f"\nData Extracted:")
        for key, value in results['data_extracted'].items():
            if isinstance(value, str) and len(value) > 100:
                print(f"  - {key}: {value[:100]}...")
            else:
                print(f"  - {key}: {value}")
    
    if results['errors']:
        print(f"\nErrors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  - {error}")
    
    return results


if __name__ == "__main__":
    run_agent_browser_test()
