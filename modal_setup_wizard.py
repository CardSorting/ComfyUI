#!/usr/bin/env python3
"""
ComfyUI on Modal - Interactive Setup Wizard

This wizard will guide you through setting up ComfyUI on Modal.com step by step.
Just answer the questions and it will do everything for you!

Usage:
    python modal_setup_wizard.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# Colors for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
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
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def ask_yes_no(question, default=True):
    """Ask a yes/no question"""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{Colors.BOLD}{question} [{default_str}]: {Colors.END}").strip().lower()
    
    if not response:
        return default
    return response in ['y', 'yes']

def ask_choice(question, choices):
    """Ask user to choose from a list"""
    print(f"\n{Colors.BOLD}{question}{Colors.END}")
    for i, choice in enumerate(choices, 1):
        print(f"  {i}. {choice}")
    
    while True:
        try:
            response = input(f"\n{Colors.BOLD}Enter choice (1-{len(choices)}): {Colors.END}").strip()
            choice_num = int(response)
            if 1 <= choice_num <= len(choices):
                return choice_num - 1
            print_error(f"Please enter a number between 1 and {len(choices)}")
        except ValueError:
            print_error("Please enter a valid number")

def run_command(cmd, description, show_output=True):
    """Run a shell command and return success status"""
    print_info(f"{description}...")
    
    try:
        if show_output:
            result = subprocess.run(cmd, shell=True, check=True)
        else:
            result = subprocess.run(
                cmd, 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True
            )
        print_success(f"{description} - Done!")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"{description} - Failed!")
        if not show_output and e.stderr:
            print(e.stderr)
        return False

def check_modal_installed():
    """Check if modal CLI is installed"""
    try:
        subprocess.run(
            ["modal", "--version"], 
            capture_output=True, 
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_modal_authenticated():
    """Check if modal is authenticated"""
    try:
        result = subprocess.run(
            ["modal", "token", "show"], 
            capture_output=True, 
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Main wizard function"""
    
    # Welcome screen
    print_header("ComfyUI on Modal.com - Setup Wizard")
    
    print("""
Welcome! This wizard will help you deploy ComfyUI to Modal.com.

I'll guide you through:
  1. Installing Modal CLI
  2. Authenticating with Modal
  3. Choosing a GPU
  4. Deploying ComfyUI
  5. Adding model URLs
  6. Downloading models

Let's get started!
    """)
    
    if not ask_yes_no("Ready to begin?"):
        print("\nOkay, come back when you're ready!")
        return
    
    # Step 1: Check/Install Modal CLI
    print_header("Step 1: Modal CLI Installation")
    
    if check_modal_installed():
        print_success("Modal CLI is already installed!")
    else:
        print_info("Modal CLI is not installed.")
        if ask_yes_no("Would you like me to install it now?"):
            if not run_command("pip install modal", "Installing Modal CLI"):
                print_error("Failed to install Modal CLI. Please install it manually:")
                print("  pip install modal")
                return
        else:
            print_error("Modal CLI is required. Please install it manually:")
            print("  pip install modal")
            return
    
    # Step 2: Check/Setup Authentication
    print_header("Step 2: Modal Authentication")
    
    if check_modal_authenticated():
        print_success("You're already authenticated with Modal!")
    else:
        print_info("You need to authenticate with Modal.")
        print("\nThis will open your web browser to log in to Modal.")
        print("If you don't have a Modal account, you can create one for free.")
        
        if ask_yes_no("\nReady to authenticate?"):
            if not run_command("modal setup", "Setting up Modal authentication"):
                print_error("Authentication failed. Please try again later.")
                return
        else:
            print_error("Authentication is required. Please run: modal setup")
            return
    
    # Step 3: Choose GPU
    print_header("Step 3: GPU Selection")
    
    print("""
Choose the GPU you want to use:
(You can change this later by editing modal_app.py)
    """)
    
    gpu_options = [
        ("T4 (16GB)", "$0.60/hour", "Good for: Testing, SD 1.5"),
        ("A10G (24GB)", "$1.10/hour", "Good for: SDXL, Production (RECOMMENDED)"),
        ("A100 (40GB)", "$4.00/hour", "Good for: Large models, Video generation"),
    ]
    
    for i, (name, cost, use) in enumerate(gpu_options, 1):
        print(f"\n  {i}. {Colors.BOLD}{name}{Colors.END} - {cost}")
        print(f"     {use}")
    
    gpu_choice = ask_choice("\nWhich GPU would you like to use?", [opt[0] for opt in gpu_options])
    
    gpu_config = ["modal.gpu.T4()", "modal.gpu.A10G()", "modal.gpu.A100()"][gpu_choice]
    selected_gpu = gpu_options[gpu_choice][0]
    
    print_success(f"Selected: {selected_gpu}")
    
    # Update modal_app.py with GPU choice
    print_info("Updating modal_app.py with your GPU selection...")
    
    try:
        with open("modal_app.py", "r") as f:
            content = f.read()
        
        # Replace GPU_CONFIG line
        import re
        content = re.sub(
            r'GPU_CONFIG = modal\.gpu\.\w+\(\)',
            f'GPU_CONFIG = {gpu_config}',
            content
        )
        
        with open("modal_app.py", "w") as f:
            f.write(content)
        
        print_success("GPU configuration updated!")
    except Exception as e:
        print_warning(f"Couldn't automatically update GPU config: {e}")
        print_info(f"Please manually edit modal_app.py and set: GPU_CONFIG = {gpu_config}")
    
    # Step 4: Deploy ComfyUI
    print_header("Step 4: Deploy ComfyUI")
    
    print("""
Now I'll deploy ComfyUI to Modal. This will:
  - Build the container image
  - Create persistent storage volumes
  - Deploy your API endpoint

This takes about 5 minutes.
    """)
    
    if ask_yes_no("Deploy ComfyUI now?"):
        print("\n" + "=" * 70)
        if run_command("modal deploy modal_app.py", "Deploying ComfyUI to Modal"):
            print("\n")
            print_success("ComfyUI is now deployed!")
            print_info("Your API endpoint URL was shown above - save it!")
        else:
            print_error("Deployment failed. Check the errors above.")
            return
    else:
        print_info("Skipping deployment. You can deploy later with: modal deploy modal_app.py")
        return
    
    # Step 5: Add Model URLs
    print_header("Step 5: Add Your Models")
    
    print("""
Now let's add some AI models. You have two options:

  1. I'll help you download popular models from Hugging Face
  2. You can add your own model URLs manually later

What would you like to do?
    """)
    
    model_choice = ask_choice(
        "Choose an option",
        [
            "Download popular models now (SDXL, SD 1.5, VAE)",
            "I'll add my own models later",
            "Skip this step"
        ]
    )
    
    if model_choice == 0:
        # Option 1: Download popular models
        print_header("Downloading Popular Models")
        
        print("\nI'll download these models for you:")
        print("  • SDXL Base 1.0 (6.5GB)")
        print("  • Stable Diffusion 1.5 (4GB)")
        print("  • VAE (0.3GB)")
        print("\nTotal: ~11GB (takes about 10-15 minutes)")
        
        if ask_yes_no("\nProceed with download?"):
            # Create a temporary script to download models
            download_script = """
import modal
import urllib.request
import os

app = modal.App("download-models")
models_volume = modal.Volume.from_name("comfyui-models", create_if_missing=True)

@app.function(
    image=modal.Image.debian_slim(python_version="3.11"),
    volumes={"/models": models_volume},
    timeout=3600,
)
def download_models():
    models = [
        {
            "name": "SDXL Base 1.0",
            "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
            "path": "/models/checkpoints/sd_xl_base_1.0.safetensors"
        },
        {
            "name": "Stable Diffusion 1.5",
            "url": "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors",
            "path": "/models/checkpoints/sd_v1.5.safetensors"
        },
        {
            "name": "VAE",
            "url": "https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors",
            "path": "/models/vae/vae-ft-mse-840000.safetensors"
        },
    ]
    
    for model in models:
        os.makedirs(os.path.dirname(model["path"]), exist_ok=True)
        
        if os.path.exists(model["path"]):
            print(f"⏭️  {model['name']} already exists")
            continue
        
        print(f"📥 Downloading {model['name']}...")
        print(f"   From: {model['url']}")
        
        try:
            urllib.request.urlretrieve(model["url"], model["path"])
            size = os.path.getsize(model["path"]) / (1024**3)
            print(f"✅ Downloaded: {size:.2f} GB")
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    models_volume.commit()
    print("✅ All downloads complete!")

@app.local_entrypoint()
def main():
    download_models.remote()
"""
            
            # Write temporary script
            with open("_temp_download.py", "w") as f:
                f.write(download_script)
            
            print("\n" + "=" * 70)
            if run_command("modal run _temp_download.py", "Downloading models"):
                print_success("\nModels downloaded successfully!")
                # Clean up
                os.remove("_temp_download.py")
            else:
                print_error("Download failed. You can try again later.")
                if os.path.exists("_temp_download.py"):
                    os.remove("_temp_download.py")
        
    elif model_choice == 1:
        # Option 2: Manual later
        print_info("\nTo add models later:")
        print("  1. Edit modal_app.py")
        print("  2. Find the download_models() function")
        print("  3. Add your model URLs")
        print("  4. Run: modal run modal_app.py::download_models")
        print("\nOr check out MODAL_DOWNLOAD_MODELS_FROM_URL.md for detailed instructions")
    
    # Step 6: Test Deployment
    print_header("Step 6: Test Your Deployment")
    
    print("""
Your ComfyUI is now deployed! Let's verify it's working.
    """)
    
    if ask_yes_no("Run a quick test?"):
        endpoint = input(f"\n{Colors.BOLD}Enter your endpoint URL (from the deployment output): {Colors.END}").strip()
        
        if endpoint:
            print("\nTesting...")
            test_cmd = f"curl -s {endpoint}/system_stats"
            
            try:
                result = subprocess.run(
                    test_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and result.stdout:
                    print_success("✓ Your ComfyUI API is responding!")
                    print(f"\n{Colors.GREEN}Your endpoint: {endpoint}{Colors.END}")
                else:
                    print_warning("Couldn't reach the endpoint. It might still be starting up.")
                    print_info("Try again in a minute or two.")
            except Exception as e:
                print_warning(f"Test failed: {e}")
        else:
            print_info("You can test later with: curl <your-endpoint>/system_stats")
    
    # Final Summary
    print_header("🎉 Setup Complete!")
    
    print(f"""
{Colors.GREEN}Congratulations! Your ComfyUI is now running on Modal.com!{Colors.END}

{Colors.BOLD}What you have now:{Colors.END}
  ✓ ComfyUI deployed on Modal with {selected_gpu}
  ✓ Persistent storage for models
  ✓ HTTPS API endpoint
  ✓ Auto-scaling infrastructure

{Colors.BOLD}Next steps:{Colors.END}
  1. Save your endpoint URL from the deployment output above
  2. Test it: curl <your-endpoint>/system_stats
  3. Add more models if needed
  4. Start sending ComfyUI workflows to your API!

{Colors.BOLD}Useful commands:{Colors.END}
  • View logs:        modal app logs comfyui --follow
  • List volumes:     modal volume list
  • Check models:     modal volume ls comfyui-models /checkpoints
  • Redeploy:         modal deploy modal_app.py
  • Download models:  modal run modal_app.py::download_models

{Colors.BOLD}Documentation:{Colors.END}
  • Quick start:      MODAL_QUICKSTART.md
  • Full guide:       MODAL_DEPLOYMENT_GUIDE.md
  • Model management: MODAL_MODEL_MANAGEMENT.md
  • Download from URL: MODAL_DOWNLOAD_MODELS_FROM_URL.md

{Colors.BOLD}Need help?{Colors.END}
  • Run this wizard again: python modal_setup_wizard.py
  • Modal Discord: https://discord.gg/modal
  • Modal Docs: https://modal.com/docs

{Colors.GREEN}Happy generating! 🚀{Colors.END}
    """)
    
    # Save configuration
    config = {
        "gpu": selected_gpu,
        "deployed": True,
        "setup_date": subprocess.check_output(["date"], text=True).strip(),
    }
    
    with open(".modal_setup.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print_info("Setup configuration saved to .modal_setup.json")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelled by user.{Colors.END}")
        print("You can run this wizard again anytime: python modal_setup_wizard.py")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}An error occurred: {e}{Colors.END}")
        print("\nIf you need help, check the documentation or run the wizard again.")
        sys.exit(1)

