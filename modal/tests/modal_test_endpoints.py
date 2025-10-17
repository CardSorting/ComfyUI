#!/usr/bin/env python3
"""
ComfyUI on Modal - Endpoint Testing Tool

Interactive tool to test your deployed ComfyUI API endpoints.
Makes sure everything is working correctly.

Usage:
    python modal_test_endpoints.py
    python modal_test_endpoints.py <endpoint-url>
"""

import sys
import requests
import json
import time
from datetime import datetime

# Colors for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_test(name, passed, details=""):
    """Print test result"""
    if passed:
        print(f"{Colors.GREEN}✓{Colors.END} {Colors.BOLD}{name}{Colors.END}")
        if details:
            print(f"  {Colors.CYAN}{details}{Colors.END}")
    else:
        print(f"{Colors.RED}✗{Colors.END} {Colors.BOLD}{name}{Colors.END}")
        if details:
            print(f"  {Colors.RED}{details}{Colors.END}")

def test_basic_connectivity(endpoint):
    """Test if the endpoint is reachable"""
    print_info("Testing basic connectivity...")
    
    try:
        response = requests.get(endpoint, timeout=10)
        if response.status_code in [200, 404]:  # 404 is ok, means server is up
            print_test("Basic Connectivity", True, f"Server is responding (HTTP {response.status_code})")
            return True
        else:
            print_test("Basic Connectivity", False, f"Unexpected status code: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print_test("Basic Connectivity", False, "Connection timeout - server may be cold starting")
        print_info("Try again in a minute if this is a fresh deployment")
        return False
    except requests.exceptions.ConnectionError as e:
        print_test("Basic Connectivity", False, f"Cannot connect to server: {e}")
        return False
    except Exception as e:
        print_test("Basic Connectivity", False, f"Error: {e}")
        return False

def test_system_stats(endpoint):
    """Test /system_stats endpoint"""
    print_info("Testing /system_stats endpoint...")
    
    try:
        response = requests.get(f"{endpoint}/system_stats", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print_test("System Stats Endpoint", True, "API is responding correctly")
            
            # Show some useful info
            if isinstance(data, dict):
                print(f"\n  {Colors.BOLD}System Information:{Colors.END}")
                
                system_info = data.get('system', {})
                if system_info:
                    if 'os' in system_info:
                        print(f"  • OS: {system_info['os']}")
                    if 'python_version' in system_info:
                        print(f"  • Python: {system_info['python_version']}")
                
                devices = data.get('devices', [])
                if devices:
                    print(f"  • Devices: {', '.join(devices)}")
            
            return True
        else:
            print_test("System Stats Endpoint", False, f"HTTP {response.status_code}: {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print_test("System Stats Endpoint", False, "Request timeout")
        return False
    except Exception as e:
        print_test("System Stats Endpoint", False, f"Error: {e}")
        return False

def test_object_info(endpoint):
    """Test /object_info endpoint"""
    print_info("Testing /object_info endpoint...")
    
    try:
        response = requests.get(f"{endpoint}/object_info", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict):
                node_count = len(data)
                print_test("Object Info Endpoint", True, f"Found {node_count} node types")
                
                # Show some example nodes
                if node_count > 0:
                    sample_nodes = list(data.keys())[:5]
                    print(f"\n  {Colors.BOLD}Sample nodes available:{Colors.END}")
                    for node in sample_nodes:
                        print(f"  • {node}")
                    
                    if node_count > 5:
                        print(f"  • ... and {node_count - 5} more")
                
                return True
            else:
                print_test("Object Info Endpoint", False, "Unexpected response format")
                return False
        else:
            print_test("Object Info Endpoint", False, f"HTTP {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print_test("Object Info Endpoint", False, "Request timeout")
        return False
    except Exception as e:
        print_test("Object Info Endpoint", False, f"Error: {e}")
        return False

def test_queue(endpoint):
    """Test /queue endpoint"""
    print_info("Testing /queue endpoint...")
    
    try:
        response = requests.get(f"{endpoint}/queue", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict):
                pending = len(data.get('queue_pending', []))
                running = len(data.get('queue_running', []))
                
                print_test("Queue Endpoint", True, f"Pending: {pending}, Running: {running}")
                return True
            else:
                print_test("Queue Endpoint", False, "Unexpected response format")
                return False
        else:
            print_test("Queue Endpoint", False, f"HTTP {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print_test("Queue Endpoint", False, "Request timeout")
        return False
    except Exception as e:
        print_test("Queue Endpoint", False, f"Error: {e}")
        return False

def test_history(endpoint):
    """Test /history endpoint"""
    print_info("Testing /history endpoint...")
    
    try:
        response = requests.get(f"{endpoint}/history", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict):
                history_count = len(data)
                print_test("History Endpoint", True, f"History has {history_count} entries")
                return True
            else:
                print_test("History Endpoint", False, "Unexpected response format")
                return False
        else:
            print_test("History Endpoint", False, f"HTTP {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print_test("History Endpoint", False, "Request timeout")
        return False
    except Exception as e:
        print_test("History Endpoint", False, f"Error: {e}")
        return False

def check_models(endpoint):
    """Check if any models are loaded"""
    print_info("Checking for available models...")
    
    try:
        # Get object info which includes available models
        response = requests.get(f"{endpoint}/object_info", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Look for checkpoint loader nodes
            checkpoint_nodes = [k for k in data.keys() if 'checkpoint' in k.lower() or 'loader' in k.lower()]
            
            if checkpoint_nodes:
                print_test("Model Check", True, f"ComfyUI is ready to load models")
                print(f"\n  {Colors.BOLD}Available loader nodes:{Colors.END}")
                for node in checkpoint_nodes[:3]:
                    print(f"  • {node}")
                
                print_warning("\n  Note: To add models, use:")
                print("  modal volume put comfyui-models model.safetensors /checkpoints/model.safetensors")
                return True
            else:
                print_test("Model Check", False, "No checkpoint loader nodes found")
                return False
        else:
            print_test("Model Check", False, "Could not check models")
            return False
    except Exception as e:
        print_test("Model Check", False, f"Error: {e}")
        return False

def test_simple_workflow(endpoint):
    """Test submitting a very simple workflow"""
    print_info("Testing workflow submission (if you want to test)...")
    
    print(f"\n{Colors.YELLOW}To test a real workflow:{Colors.END}")
    print("  1. Export a workflow from ComfyUI as API format")
    print("  2. Save it as workflow.json")
    print(f"  3. Run: {Colors.BOLD}python modal_test_endpoints.py {endpoint} workflow.json{Colors.END}")
    
    return None  # Neutral result

def run_all_tests(endpoint):
    """Run all tests"""
    print_header(f"Testing ComfyUI Endpoint")
    
    print(f"{Colors.BOLD}Endpoint:{Colors.END} {endpoint}")
    print(f"{Colors.BOLD}Time:{Colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    
    # Test 1: Basic connectivity
    print_header("Test 1: Basic Connectivity")
    results['connectivity'] = test_basic_connectivity(endpoint)
    
    if not results['connectivity']:
        print_error("\nCannot connect to endpoint. Check:")
        print("  • Is the URL correct?")
        print("  • Is the deployment running? (modal app list)")
        print("  • Is it still starting up? (wait a minute and try again)")
        return results
    
    # Test 2: System stats
    print_header("Test 2: System Stats")
    results['system_stats'] = test_system_stats(endpoint)
    
    # Test 3: Object info
    print_header("Test 3: Node Information")
    results['object_info'] = test_object_info(endpoint)
    
    # Test 4: Queue
    print_header("Test 4: Queue System")
    results['queue'] = test_queue(endpoint)
    
    # Test 5: History
    print_header("Test 5: History")
    results['history'] = test_history(endpoint)
    
    # Test 6: Model check
    print_header("Test 6: Model Availability")
    results['models'] = check_models(endpoint)
    
    # Test 7: Workflow (informational)
    print_header("Test 7: Workflow Submission")
    test_simple_workflow(endpoint)
    
    return results

def print_summary(results, endpoint):
    """Print test summary"""
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    total = passed + failed
    
    if total == 0:
        print_warning("No tests completed")
        return
    
    percentage = (passed / total) * 100
    
    print(f"{Colors.BOLD}Results:{Colors.END}")
    print(f"  • Passed: {Colors.GREEN}{passed}{Colors.END}")
    print(f"  • Failed: {Colors.RED}{failed}{Colors.END}")
    print(f"  • Success Rate: {percentage:.1f}%\n")
    
    if percentage == 100:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! Your ComfyUI is working perfectly!{Colors.END}\n")
        print(f"{Colors.BOLD}Next steps:{Colors.END}")
        print("  1. Add models: modal volume put comfyui-models model.safetensors /checkpoints/model.safetensors")
        print("  2. Submit workflows to: " + endpoint + "/prompt")
        print("  3. Check the guides: START_HERE.md, MODAL_QUICKSTART.md")
    elif percentage >= 80:
        print(f"{Colors.GREEN}✓ Most tests passed! Your ComfyUI is mostly working.{Colors.END}\n")
        print(f"{Colors.BOLD}Issues to fix:{Colors.END}")
        for test, result in results.items():
            if result is False:
                print(f"  • {test}")
    else:
        print(f"{Colors.RED}⚠ Several tests failed. Your ComfyUI may have issues.{Colors.END}\n")
        print(f"{Colors.BOLD}Troubleshooting:{Colors.END}")
        print("  • Check deployment: modal app logs comfyui --follow")
        print("  • Check status: modal app show comfyui")
        print("  • Redeploy: modal deploy modal_app.py")

def test_workflow_file(endpoint, workflow_file):
    """Test submitting a workflow from a file"""
    print_header("Testing Workflow Submission")
    
    print_info(f"Loading workflow from: {workflow_file}")
    
    try:
        with open(workflow_file, 'r') as f:
            workflow = json.load(f)
        
        print_success(f"Loaded workflow with {len(workflow)} nodes")
    except FileNotFoundError:
        print_error(f"File not found: {workflow_file}")
        return False
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        return False
    except Exception as e:
        print_error(f"Error loading workflow: {e}")
        return False
    
    print_info("Submitting workflow to API...")
    
    try:
        response = requests.post(
            f"{endpoint}/prompt",
            json={"prompt": workflow},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            prompt_id = result.get('prompt_id')
            
            print_success(f"Workflow queued successfully!")
            print(f"  Prompt ID: {prompt_id}")
            
            # Try to monitor execution
            print_info("\nMonitoring execution (30 seconds max)...")
            
            start_time = time.time()
            max_wait = 30
            
            while time.time() - start_time < max_wait:
                try:
                    history_response = requests.get(f"{endpoint}/history/{prompt_id}", timeout=5)
                    
                    if history_response.status_code == 200:
                        history = history_response.json()
                        
                        if prompt_id in history:
                            status = history[prompt_id].get('status', {})
                            
                            if status.get('completed'):
                                print_success("\n✓ Workflow completed successfully!")
                                
                                outputs = history[prompt_id].get('outputs', {})
                                if outputs:
                                    print(f"\n  {Colors.BOLD}Outputs:{Colors.END}")
                                    for node_id, output in outputs.items():
                                        print(f"  • Node {node_id}: {output}")
                                
                                return True
                            elif 'error' in status:
                                print_error(f"\n✗ Workflow failed: {status.get('error')}")
                                return False
                    
                    time.sleep(2)
                    print(".", end="", flush=True)
                    
                except Exception:
                    pass
            
            print_warning("\n\nWorkflow is still running after 30 seconds.")
            print_info("Check status later with:")
            print(f"  curl {endpoint}/history/{prompt_id}")
            
            return None  # Unknown status
            
        else:
            print_error(f"Failed to submit workflow: HTTP {response.status_code}")
            print(f"  {response.text[:500]}")
            return False
            
    except Exception as e:
        print_error(f"Error submitting workflow: {e}")
        return False

def get_endpoint_from_modal():
    """Try to get endpoint URL from Modal CLI"""
    print_info("Fetching your endpoint URL from Modal...")
    
    try:
        import subprocess
        
        # Get app info from Modal
        result = subprocess.run(
            ["modal", "app", "show", "comfyui"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Parse the output to find the web endpoint
            for line in result.stdout.split('\n'):
                if 'web_url' in line.lower() or 'endpoint' in line.lower():
                    # Try to extract URL
                    import re
                    urls = re.findall(r'https://[^\s]+', line)
                    if urls:
                        endpoint = urls[0].rstrip('/')
                        print_success(f"Found your endpoint: {endpoint}")
                        return endpoint
            
            # If not found in output, try another method
            # Look for URL pattern in the output
            import re
            urls = re.findall(r'https://[^\s]+\.modal\.run[^\s]*', result.stdout)
            if urls:
                endpoint = urls[0].rstrip('/')
                print_success(f"Found your endpoint: {endpoint}")
                return endpoint
        
        print_warning("Could not auto-detect endpoint from Modal CLI")
        return None
        
    except FileNotFoundError:
        print_warning("Modal CLI not found. Install with: pip install modal")
        return None
    except Exception as e:
        print_warning(f"Could not auto-detect endpoint: {e}")
        return None

def save_endpoint(endpoint):
    """Save endpoint to a local cache file"""
    try:
        import json
        cache_file = ".modal_endpoint_cache.json"
        
        with open(cache_file, 'w') as f:
            json.dump({
                "endpoint": endpoint,
                "timestamp": datetime.now().isoformat()
            }, f)
    except Exception:
        pass  # Ignore errors in caching

def load_cached_endpoint():
    """Load endpoint from cache if available"""
    try:
        import json
        cache_file = ".modal_endpoint_cache.json"
        
        with open(cache_file, 'r') as f:
            data = json.load(f)
            return data.get('endpoint')
    except Exception:
        return None

def main():
    """Main function"""
    
    print_header("ComfyUI Modal Endpoint Tester")
    
    # Get endpoint URL
    endpoint = None
    
    # Method 1: From command line argument
    if len(sys.argv) >= 2:
        endpoint = sys.argv[1].rstrip('/')
        print_info(f"Using endpoint from command line: {endpoint}")
    else:
        # Method 2: Try to fetch from Modal CLI
        print_info("No endpoint provided, attempting auto-detection...")
        endpoint = get_endpoint_from_modal()
        
        # Method 3: Try cached endpoint
        if not endpoint:
            cached = load_cached_endpoint()
            if cached:
                print_info(f"Found cached endpoint: {cached}")
                use_cached = input(f"{Colors.BOLD}Use this endpoint? [Y/n]: {Colors.END}").strip().lower()
                if use_cached != 'n':
                    endpoint = cached
        
        # Method 4: Ask user
        if not endpoint:
            print("\n" + "=" * 70)
            print("Enter your Modal endpoint URL")
            print("(Get it from: modal app show comfyui)")
            print("Example: https://workspace--comfyui-fastapi-app.modal.run")
            print("=" * 70)
            endpoint = input(f"\n{Colors.BOLD}Endpoint URL: {Colors.END}").strip().rstrip('/')
            
            if not endpoint:
                print_error("No endpoint provided. Exiting.")
                print_info("\nTo get your endpoint URL, run: modal app show comfyui")
                return
    
    # Save endpoint for future use
    save_endpoint(endpoint)
    
    # Validate URL
    if not endpoint.startswith('http'):
        print_error("Invalid URL. Must start with http:// or https://")
        return
    
    # Display endpoint info
    print(f"\n{Colors.BOLD}{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}")
    print(f"{Colors.BOLD}📍 Your ComfyUI Endpoint:{Colors.END}")
    print(f"{Colors.GREEN}{endpoint}{Colors.END}")
    print(f"{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}\n")
    
    # Check for workflow file
    workflow_file = sys.argv[2] if len(sys.argv) >= 3 else None
    
    if workflow_file:
        # Test specific workflow
        test_workflow_file(endpoint, workflow_file)
    else:
        # Run all standard tests
        results = run_all_tests(endpoint)
        
        # Print summary
        print_summary(results, endpoint)
    
    print(f"\n{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}")
    print(f"{Colors.BOLD}For more help:{Colors.END}")
    print("  • Check logs: modal app logs comfyui --follow")
    print("  • View status: modal app show comfyui")
    print("  • Read guides: START_HERE.md, MODAL_QUICKSTART.md")
    print(f"{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Testing cancelled by user.{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}An error occurred: {e}{Colors.END}")
        sys.exit(1)

