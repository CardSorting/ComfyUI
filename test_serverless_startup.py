#!/usr/bin/env python3
"""
Test script to verify serverless startup without custom node errors.

This script simulates the serverless environment startup and verifies that
problematic custom nodes (like comfyui-impact-pack) are properly disabled.
"""

import sys
import os
import subprocess
import time

def test_headless_startup():
    """Test ComfyUI headless startup with custom nodes disabled"""
    print("=" * 60)
    print("Testing ComfyUI Headless Startup (Serverless Mode)")
    print("=" * 60)
    
    # Set environment for headless mode
    env = os.environ.copy()
    env['COMFYUI_HEADLESS'] = '1'
    env['DISABLE_PROGRESS_BARS'] = '1'
    
    # Command to start ComfyUI with custom nodes disabled
    cmd = [
        sys.executable,
        'main.py',
        '--headless',
        '--listen', '127.0.0.1',
        '--port', '8189',  # Use different port for testing
        '--disable-all-custom-nodes',
        '--whitelist-custom-nodes', 'websocket_image_save.py',
    ]
    
    print(f"\n✓ Command: {' '.join(cmd)}\n")
    print("Starting ComfyUI (this may take 30-60 seconds)...\n")
    
    # Start ComfyUI process
    try:
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Collect output for analysis
        success_indicators = []
        error_indicators = []
        cv2_errors = []
        impact_pack_errors = []
        
        # Monitor output for 30 seconds
        start_time = time.time()
        timeout = 30
        
        while time.time() - start_time < timeout:
            # Check if process is still running
            if process.poll() is not None:
                print(f"Process exited with code {process.returncode}")
                break
            
            # Read output line by line
            line = process.stderr.readline()
            if line:
                line = line.strip()
                
                # Check for error indicators
                if 'cv2' in line.lower():
                    cv2_errors.append(line)
                    print(f"❌ CV2 Error: {line}")
                
                if 'impact-pack' in line.lower() or 'impact-subpack' in line.lower():
                    impact_pack_errors.append(line)
                    if 'FAILED' in line or 'ERROR' in line:
                        print(f"❌ Impact Pack Error: {line}")
                    else:
                        print(f"ℹ️  Impact Pack: {line}")
                
                # Check for success indicators
                if 'Import times for custom nodes' in line:
                    success_indicators.append('custom_nodes_loaded')
                    print(f"✓ {line}")
                
                if 'websocket_image_save.py' in line:
                    success_indicators.append('whitelist_loaded')
                    print(f"✓ {line}")
                
                if 'Starting server' in line or 'To see the GUI' in line:
                    success_indicators.append('server_started')
                    print(f"✓ Server started")
                    break
        
        # Terminate the process
        print("\n\nShutting down test server...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        
        # Analyze results
        print("\n" + "=" * 60)
        print("Test Results")
        print("=" * 60)
        
        success = True
        
        # Check for CV2 errors (should be none)
        if cv2_errors:
            print(f"\n❌ FAILED: Found {len(cv2_errors)} CV2-related errors")
            print("   This means the custom nodes are still being loaded!")
            for error in cv2_errors[:3]:  # Show first 3
                print(f"   - {error}")
            success = False
        else:
            print("\n✓ PASSED: No CV2 errors detected")
        
        # Check for Impact Pack errors (should be skipped, not failed)
        if impact_pack_errors:
            failed_imports = [e for e in impact_pack_errors if 'IMPORT FAILED' in e or 'ERROR' in e]
            if failed_imports:
                print(f"\n❌ FAILED: Impact Pack attempted to load and failed")
                for error in failed_imports[:2]:
                    print(f"   - {error}")
                success = False
            else:
                print("\n✓ PASSED: Impact Pack properly skipped (not loaded)")
        else:
            print("\n✓ PASSED: No Impact Pack errors (properly disabled)")
        
        # Check for success indicators
        if success_indicators:
            print(f"\n✓ PASSED: Found {len(success_indicators)} success indicators:")
            for indicator in success_indicators:
                print(f"   - {indicator}")
        else:
            print("\n⚠️  WARNING: No success indicators found")
            print("   The server may not have started properly")
            success = False
        
        print("\n" + "=" * 60)
        if success:
            print("✓ ALL TESTS PASSED")
            print("Serverless startup is working correctly!")
        else:
            print("❌ TESTS FAILED")
            print("Custom nodes are not properly disabled.")
            print("Please review the configuration.")
        print("=" * 60)
        
        return success
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        if 'process' in locals():
            process.terminate()
            process.wait()
        return False
    
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        if 'process' in locals():
            process.terminate()
            process.wait()
        return False

if __name__ == "__main__":
    print("""
This test verifies that ComfyUI starts in headless mode without
attempting to load custom nodes that require missing dependencies (cv2).

NOTE: This test will start ComfyUI on port 8189 and run for ~30 seconds.
""")
    
    input("Press Enter to start the test...")
    
    success = test_headless_startup()
    sys.exit(0 if success else 1)

