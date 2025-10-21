#!/usr/bin/env python3
"""
Platform Benchmark Tool
Compare cold start times and performance across different deployment platforms
"""

import time
import requests
import json
import statistics
from datetime import datetime
from typing import Dict, List, Tuple


class PlatformBenchmark:
    """Benchmark different serverless platforms"""
    
    def __init__(self):
        self.results = {}
    
    def test_modal(self, endpoint_url: str, api_key: str, workflow: dict, num_tests: int = 5) -> Dict:
        """Test Modal endpoint"""
        print(f"\n{'='*60}")
        print("Testing Modal")
        print(f"{'='*60}")
        
        cold_starts = []
        warm_starts = []
        
        for i in range(num_tests):
            print(f"\nTest {i+1}/{num_tests}")
            
            # Wait for cold start (Modal scales down after 5 minutes by default)
            if i > 0:
                print("Waiting 6 minutes for cold start...")
                time.sleep(360)
            
            # Measure request time
            start_time = time.time()
            
            try:
                response = requests.post(
                    endpoint_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"workflow": workflow},
                    timeout=300
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                if response.status_code == 200:
                    print(f"✓ Success: {duration:.2f}s")
                    cold_starts.append(duration)
                else:
                    print(f"✗ Failed: {response.status_code}")
                    
            except Exception as e:
                print(f"✗ Error: {e}")
        
        return {
            "platform": "Modal",
            "cold_starts": cold_starts,
            "avg_cold_start": statistics.mean(cold_starts) if cold_starts else 0,
            "min_cold_start": min(cold_starts) if cold_starts else 0,
            "max_cold_start": max(cold_starts) if cold_starts else 0,
        }
    
    def test_runpod(self, endpoint_id: str, api_key: str, workflow: dict, num_tests: int = 5) -> Dict:
        """Test RunPod endpoint"""
        print(f"\n{'='*60}")
        print("Testing RunPod")
        print(f"{'='*60}")
        
        base_url = "https://api.runpod.ai/v2"
        cold_starts = []
        
        for i in range(num_tests):
            print(f"\nTest {i+1}/{num_tests}")
            
            # Wait for cold start
            if i > 0:
                print("Waiting 2 minutes for cold start...")
                time.sleep(120)
            
            start_time = time.time()
            
            try:
                # Submit job
                response = requests.post(
                    f"{base_url}/{endpoint_id}/run",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": {
                            "workflow": workflow
                        }
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    job_data = response.json()
                    job_id = job_data.get("id")
                    
                    # Poll for completion
                    while True:
                        status_response = requests.get(
                            f"{base_url}/{endpoint_id}/status/{job_id}",
                            headers={"Authorization": f"Bearer {api_key}"}
                        )
                        
                        status_data = status_response.json()
                        status = status_data.get("status")
                        
                        if status == "COMPLETED":
                            end_time = time.time()
                            duration = end_time - start_time
                            print(f"✓ Success: {duration:.2f}s")
                            cold_starts.append(duration)
                            break
                        elif status == "FAILED":
                            print(f"✗ Failed: {status_data.get('error')}")
                            break
                        
                        time.sleep(1)
                else:
                    print(f"✗ Failed to submit: {response.status_code}")
                    
            except Exception as e:
                print(f"✗ Error: {e}")
        
        return {
            "platform": "RunPod",
            "cold_starts": cold_starts,
            "avg_cold_start": statistics.mean(cold_starts) if cold_starts else 0,
            "min_cold_start": min(cold_starts) if cold_starts else 0,
            "max_cold_start": max(cold_starts) if cold_starts else 0,
        }
    
    def test_generic_endpoint(self, name: str, endpoint_url: str, headers: dict, 
                            payload: dict, num_tests: int = 5, 
                            cooldown_seconds: int = 180) -> Dict:
        """Test any generic endpoint"""
        print(f"\n{'='*60}")
        print(f"Testing {name}")
        print(f"{'='*60}")
        
        cold_starts = []
        
        for i in range(num_tests):
            print(f"\nTest {i+1}/{num_tests}")
            
            # Wait for cold start
            if i > 0:
                print(f"Waiting {cooldown_seconds}s for cold start...")
                time.sleep(cooldown_seconds)
            
            start_time = time.time()
            
            try:
                response = requests.post(
                    endpoint_url,
                    headers=headers,
                    json=payload,
                    timeout=300
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                if response.status_code == 200:
                    print(f"✓ Success: {duration:.2f}s")
                    cold_starts.append(duration)
                else:
                    print(f"✗ Failed: {response.status_code} - {response.text[:100]}")
                    
            except Exception as e:
                print(f"✗ Error: {e}")
        
        return {
            "platform": name,
            "cold_starts": cold_starts,
            "avg_cold_start": statistics.mean(cold_starts) if cold_starts else 0,
            "min_cold_start": min(cold_starts) if cold_starts else 0,
            "max_cold_start": max(cold_starts) if cold_starts else 0,
        }
    
    def compare_results(self, results: List[Dict]):
        """Print comparison of all results"""
        print(f"\n\n{'='*80}")
        print("BENCHMARK RESULTS SUMMARY")
        print(f"{'='*80}\n")
        
        # Sort by average cold start time
        sorted_results = sorted(results, key=lambda x: x['avg_cold_start'])
        
        # Print table header
        print(f"{'Platform':<20} {'Avg Cold Start':<20} {'Min':<15} {'Max':<15}")
        print(f"{'-'*70}")
        
        # Print results
        for result in sorted_results:
            platform = result['platform']
            avg = result['avg_cold_start']
            min_time = result['min_cold_start']
            max_time = result['max_cold_start']
            
            print(f"{platform:<20} {avg:>6.2f}s {'':<13} {min_time:>6.2f}s {'':<8} {max_time:>6.2f}s")
        
        # Calculate improvements
        if len(sorted_results) > 1:
            print(f"\n{'='*80}")
            print("IMPROVEMENT ANALYSIS")
            print(f"{'='*80}\n")
            
            baseline = sorted_results[-1]  # Slowest
            
            for result in sorted_results[:-1]:
                improvement = ((baseline['avg_cold_start'] - result['avg_cold_start']) / 
                             baseline['avg_cold_start'] * 100)
                speedup = baseline['avg_cold_start'] / result['avg_cold_start']
                
                print(f"{result['platform']} vs {baseline['platform']}:")
                print(f"  → {improvement:.1f}% faster")
                print(f"  → {speedup:.1f}x speedup")
                print()
        
        # Cost estimation
        print(f"{'='*80}")
        print("ESTIMATED MONTHLY COSTS (1000 requests/day, 30s execution on A100)")
        print(f"{'='*80}\n")
        
        for result in sorted_results:
            platform = result['platform']
            avg_cold = result['avg_cold_start']
            total_time = avg_cold + 30  # 30s execution
            
            # Rough pricing (adjust based on actual rates)
            price_per_hour = {
                "Modal": 2.5,
                "RunPod": 2.18,
                "Inferless": 2.0,
            }.get(platform, 2.2)
            
            hours_per_month = (total_time * 1000 * 30) / 3600
            monthly_cost = hours_per_month * price_per_hour
            
            print(f"{platform:<20} ${monthly_cost:>8.2f}/month")
        
        # Save results to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'results': results
            }, f, indent=2)
        
        print(f"\n✓ Results saved to {filename}")


def main():
    """Main benchmark function"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         SERVERLESS PLATFORM BENCHMARK TOOL                    ║
╚══════════════════════════════════════════════════════════════╝
    
This tool will benchmark different serverless platforms for
ComfyUI deployment and compare their cold start performance.

NOTE: Each platform test will take significant time due to 
      intentional cooldown periods to trigger cold starts.
    """)
    
    # Load test workflow
    try:
        with open("test_workflow_sdxl_turbo.json", "r") as f:
            workflow = json.load(f)
            print("✓ Loaded test workflow: test_workflow_sdxl_turbo.json")
    except FileNotFoundError:
        print("✗ Test workflow not found. Please create test_workflow_sdxl_turbo.json")
        return
    
    benchmark = PlatformBenchmark()
    results = []
    
    # Configure platforms to test
    print("\nConfigure platforms to test:")
    print("(Press Enter to skip a platform)\n")
    
    # Modal
    modal_endpoint = input("Modal endpoint URL: ").strip()
    if modal_endpoint:
        modal_key = input("Modal API key: ").strip()
        modal_result = benchmark.test_modal(modal_endpoint, modal_key, workflow, num_tests=3)
        results.append(modal_result)
    
    # RunPod
    runpod_endpoint = input("RunPod endpoint ID: ").strip()
    if runpod_endpoint:
        runpod_key = input("RunPod API key: ").strip()
        runpod_result = benchmark.test_runpod(runpod_endpoint, runpod_key, workflow, num_tests=3)
        results.append(runpod_result)
    
    # Generic endpoint (Inferless, ViewComfy, etc.)
    generic_name = input("Other platform name (e.g., Inferless): ").strip()
    if generic_name:
        generic_endpoint = input(f"{generic_name} endpoint URL: ").strip()
        generic_key = input(f"{generic_name} API key (if needed): ").strip()
        
        headers = {"Content-Type": "application/json"}
        if generic_key:
            headers["Authorization"] = f"Bearer {generic_key}"
        
        payload = {"workflow": workflow}
        
        generic_result = benchmark.test_generic_endpoint(
            generic_name, generic_endpoint, headers, payload, 
            num_tests=3, cooldown_seconds=180
        )
        results.append(generic_result)
    
    # Compare results
    if results:
        benchmark.compare_results(results)
    else:
        print("\n✗ No platforms configured for testing")


if __name__ == "__main__":
    main()

