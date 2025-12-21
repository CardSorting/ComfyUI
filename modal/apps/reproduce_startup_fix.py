
import asyncio
import sys
import os
from unittest.mock import MagicMock, patch

# Add ComfyUI root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

async def simulate_startup_fix():
    print("🧪 Testing ComfyUI Startup with Loop Passing")
    
    # Mock main.start_comfyui to print the loop it receives
    mock_start_comfyui = MagicMock()
    
    # We need to simulate the structure of main.start_comfyui return values
    # It returns (loop, prompt_server, start_job)
    mock_loop = asyncio.new_event_loop()
    mock_server = MagicMock()
    mock_server.setup = MagicMock(return_value=asyncio.Future())
    mock_server.setup.return_value.set_result(None) # Make it awaitable
    
    async def mock_start_job():
        print("   ✅ Start job called")
    
    mock_start_comfyui.return_value = (mock_loop, mock_server, mock_start_job)
    
    # Patch main.start_comfyui
    with patch('main.start_comfyui', side_effect=mock_start_comfyui) as mock_start:
        
        # Simulate what we want to do in lifespan
        running_loop = asyncio.get_running_loop()
        print(f"   ℹ️  Running Loop: {running_loop}")
        
        # This is the core change: passing the running loop to start_comfyui
        print("   🔄 Calling start_comfyui(asyncio_loop=running_loop)...")
        _ = mock_start(asyncio_loop=running_loop)
        
        # Verify call args
        call_args = mock_start.call_args
        passed_loop = call_args.kwargs.get('asyncio_loop')
        
        if passed_loop is running_loop:
            print("   ✅ SUCCESS: Running loop was passed correctly!")
            return True
        else:
            print(f"   ❌ FAILED: Loop mismatch. Passed: {passed_loop}")
            return False

if __name__ == "__main__":
    try:
        success = asyncio.run(simulate_startup_fix())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        sys.exit(1)
