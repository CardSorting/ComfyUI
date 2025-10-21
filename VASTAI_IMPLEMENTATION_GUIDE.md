# Vast.ai Implementation Guide for ComfyUI

## 🎯 Why Vast.ai?

**Cost Savings: 50-70% cheaper than RunPod!**

| GPU Type | Vast.ai | RunPod | Savings |
|----------|---------|---------|---------|
| RTX 4090 | $0.15-0.40/hr | $0.44-0.69/hr | **50-70%** |
| RTX 3090 | $0.10-0.30/hr | $0.35-0.50/hr | **60-70%** |
| A100 80GB | $0.73-1.61/hr | $2.18/hr | **26-65%** |
| A100 40GB | $0.60-1.20/hr | $1.50/hr | **20-60%** |

**Monthly Cost Example (1000 req/day, 30s per req):**
- RunPod: ~$785/month
- **Vast.ai: ~$250-400/month** 
- **💰 Savings: $385-535/month (50-68%)**

---

## ⚠️ Important Trade-offs

### Vast.ai Advantages ✅
- **50-70% cheaper** than RunPod
- **Wide GPU selection** from many providers
- **Flexible pricing** (on-demand, interruptible, reserved)
- **No vendor lock-in** - marketplace model

### Vast.ai Disadvantages ❌
- **NOT serverless** - requires manual instance management
- **Manual scaling** - no auto-scale from 0 to N
- **Variable cold starts** - 30s-2min for instance startup
- **Network performance varies** - depends on provider
- **More hands-on management** - less automated than RunPod
- **Interruptible instances** - can be paused if outbid (for lowest prices)

### The Real Trade-off
**Vast.ai = Lower Cost, Higher Management Effort**
- Best for: Steady workload, dedicated instances, cost-sensitive projects
- Not ideal for: Bursty traffic, auto-scaling, truly serverless needs

**RunPod Serverless = Higher Cost, Zero Management**
- Best for: Variable traffic, auto-scaling, production APIs
- Cold starts: 200ms-12s vs Vast.ai's 30s-2min

---

## 🚀 Quick Start Guide

### Step 1: Create Vast.ai Account

1. Go to https://vast.ai
2. Sign up for an account
3. Add payment method (credit card)
4. Add initial credit ($10-20 to start)

### Step 2: Prepare ComfyUI Docker Image

Create `Dockerfile.vastai`:

```dockerfile
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy ComfyUI files
COPY . /workspace/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose ComfyUI port
EXPOSE 8188

# Start ComfyUI
CMD ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
```

Build and push to Docker Hub:

```bash
# Build the image
docker build -f Dockerfile.vastai -t YOUR_USERNAME/comfyui:latest .

# Login to Docker Hub
docker login

# Push to Docker Hub
docker push YOUR_USERNAME/comfyui:latest
```

### Step 3: Find and Rent a GPU Instance

#### Using Vast.ai Web Interface

1. **Go to**: https://vast.ai/console/create/
2. **Filter by GPU type**: 
   - For SDXL: RTX 3090 or RTX 4090
   - For large models: A100
3. **Sort by price**: "$/hour" (ascending)
4. **Check provider reliability**:
   - Look for high "Machine Score" (>0.9)
   - Check "Reliability" rating
   - Prefer "Direct Port Mapping" for better network access
5. **Select instance type**:
   - **On-Demand**: Fixed price, guaranteed availability
   - **Interruptible**: Cheaper but can be paused if outbid

#### Recommended Filters

```
GPU: RTX 4090
VRAM: >= 24GB
Disk Space: >= 50GB
Download Speed: >= 100 Mbps
Direct Port Mapping: Yes
Reliability: >= 0.95
```

### Step 4: Configure and Launch Instance

1. **Click "RENT"** on your chosen instance
2. **Select image type**: "Run Docker Image"
3. **Docker image**: `YOUR_USERNAME/comfyui:latest`
4. **Disk space**: 50-100GB (for models)
5. **On-start script** (optional):
   ```bash
   #!/bin/bash
   cd /workspace
   # Download models if needed
   python3 main.py --listen 0.0.0.0 --port 8188
   ```
6. **Launch the instance**

### Step 5: Access Your ComfyUI Instance

1. **Wait for instance to start** (30s-2min)
2. **Get connection info** from Vast.ai dashboard:
   - SSH: `ssh root@<IP> -p <PORT>`
   - Direct Access: `http://<IP>:<PORT>`
3. **Access ComfyUI**: 
   - Open browser: `http://<VAST_IP>:8188`

### Step 6: Set Up API Access

Create a simple API wrapper `api_server.py`:

```python
from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# Your Vast.ai instance IP and port
COMFYUI_HOST = "http://localhost:8188"

@app.route('/generate', methods=['POST'])
def generate():
    """API endpoint to generate images with ComfyUI"""
    try:
        workflow = request.json.get('workflow')
        
        # Forward to ComfyUI
        response = requests.post(
            f"{COMFYUI_HOST}/prompt",
            json={"prompt": workflow}
        )
        
        return jsonify(response.json())
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Run it on your Vast.ai instance:
```bash
pip install flask
python api_server.py
```

---

## 🔧 Advanced Configuration

### Option A: Using Vast.ai CLI

Install Vast.ai CLI:
```bash
pip install vastai
```

Configure API key:
```bash
vastai set api-key YOUR_API_KEY
```

Search for instances:
```bash
# Find RTX 4090 instances under $0.30/hr
vastai search offers \
  --type on-demand \
  --gpu_name "RTX 4090" \
  --price_max 0.30 \
  --min_upload 100
```

Create instance:
```bash
vastai create instance <INSTANCE_ID> \
  --image YOUR_USERNAME/comfyui:latest \
  --disk 50 \
  --label "comfyui-production"
```

Connect via SSH:
```bash
vastai ssh <INSTANCE_ID>
```

Stop instance:
```bash
vastai stop instance <INSTANCE_ID>
```

Destroy instance:
```bash
vastai destroy instance <INSTANCE_ID>
```

### Option B: Automated Instance Management

Create `vastai_manager.py`:

```python
import subprocess
import json
import time

class VastAIManager:
    """Manage Vast.ai instances for ComfyUI"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        subprocess.run(['vastai', 'set', 'api-key', api_key])
    
    def find_best_instance(self, gpu_name="RTX 4090", max_price=0.30):
        """Find the best available instance"""
        result = subprocess.run(
            ['vastai', 'search', 'offers', 
             '--type', 'on-demand',
             '--gpu_name', gpu_name,
             '--price_max', str(max_price),
             '--min_upload', '100',
             '--raw'],
            capture_output=True,
            text=True
        )
        
        offers = json.loads(result.stdout)
        
        # Sort by price and reliability
        best_offers = sorted(
            offers,
            key=lambda x: (x['dph_total'], -x.get('reliability', 0))
        )
        
        return best_offers[0] if best_offers else None
    
    def create_instance(self, offer_id, docker_image, disk_size=50):
        """Create a new instance"""
        result = subprocess.run(
            ['vastai', 'create', 'instance', str(offer_id),
             '--image', docker_image,
             '--disk', str(disk_size),
             '--raw'],
            capture_output=True,
            text=True
        )
        
        instance = json.loads(result.stdout)
        return instance
    
    def wait_for_instance(self, instance_id, timeout=300):
        """Wait for instance to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = subprocess.run(
                ['vastai', 'show', 'instance', str(instance_id), '--raw'],
                capture_output=True,
                text=True
            )
            
            instance = json.loads(result.stdout)
            
            if instance.get('actual_status') == 'running':
                return instance
            
            time.sleep(5)
        
        raise TimeoutError(f"Instance {instance_id} did not start within {timeout}s")
    
    def get_instance_url(self, instance_id):
        """Get the URL to access ComfyUI"""
        result = subprocess.run(
            ['vastai', 'show', 'instance', str(instance_id), '--raw'],
            capture_output=True,
            text=True
        )
        
        instance = json.loads(result.stdout)
        ip = instance.get('public_ipaddr')
        port = instance.get('ports', {}).get('8188/tcp', [{}])[0].get('HostPort')
        
        return f"http://{ip}:{port}" if ip and port else None
    
    def stop_instance(self, instance_id):
        """Stop a running instance"""
        subprocess.run(['vastai', 'stop', 'instance', str(instance_id)])
    
    def destroy_instance(self, instance_id):
        """Destroy an instance"""
        subprocess.run(['vastai', 'destroy', 'instance', str(instance_id)])


# Example usage
if __name__ == "__main__":
    manager = VastAIManager(api_key="YOUR_API_KEY")
    
    # Find best instance
    print("Finding best instance...")
    offer = manager.find_best_instance(gpu_name="RTX 4090", max_price=0.30)
    
    if offer:
        print(f"Found instance: {offer['gpu_name']} at ${offer['dph_total']:.2f}/hr")
        
        # Create instance
        instance = manager.create_instance(
            offer_id=offer['id'],
            docker_image="YOUR_USERNAME/comfyui:latest",
            disk_size=50
        )
        
        print(f"Created instance {instance['new_contract']}")
        
        # Wait for it to be ready
        print("Waiting for instance to start...")
        instance_data = manager.wait_for_instance(instance['new_contract'])
        
        # Get URL
        url = manager.get_instance_url(instance['new_contract'])
        print(f"ComfyUI available at: {url}")
    else:
        print("No suitable instances found")
```

---

## 💡 Cost Optimization Strategies

### Strategy 1: Use Interruptible Instances (Cheapest)

**Cost:** Up to 70% cheaper than on-demand
**Risk:** Can be paused if outbid
**Best for:** Development, testing, non-critical workloads

```bash
vastai search offers --type interruptible --gpu_name "RTX 4090"
```

### Strategy 2: Reserve Long-term (50% Savings)

**Cost:** Up to 50% off on-demand prices
**Commitment:** Weekly or monthly rental
**Best for:** Steady production workloads

```bash
# Search for monthly reserved instances
vastai search offers --type reserved --duration month
```

### Strategy 3: Scale Based on Demand

**Approach:** Start/stop instances based on traffic
- Use Vast.ai API to start instances when needed
- Stop instances during low-traffic periods
- Can save 60-80% vs always-on

### Strategy 4: Mix On-Demand and Interruptible

**Approach:** 
- 1-2 on-demand instances for baseline traffic
- Scale with interruptible instances for bursts
- Fallback to on-demand if interruptible gets paused

---

## 📊 Cost Comparison: Vast.ai vs Others

### Monthly Cost (1000 requests/day, 30s execution, RTX 4090)

| Platform | Cold Start | Execution | GPU Cost/hr | Monthly Cost | Savings |
|----------|-----------|-----------|-------------|--------------|---------|
| **Vast.ai (Interruptible)** | 60s | 30s | **$0.20** | **$250** | Baseline |
| **Vast.ai (On-Demand)** | 60s | 30s | **$0.30** | **$375** | -50% |
| RunPod Serverless | 5s | 30s | $0.50 | $437 | -75% |
| Modal | 60s | 30s | $2.50 | $1,650 | -560% |

### Actual Hourly Costs (November 2025)

**RTX 4090 (24GB VRAM):**
- Vast.ai Interruptible: $0.15-0.25/hr
- Vast.ai On-Demand: $0.25-0.40/hr
- RunPod: $0.44-0.69/hr
- Modal equivalent: ~$0.50-0.75/hr

**A100 80GB:**
- Vast.ai Interruptible: $0.73-1.20/hr
- Vast.ai On-Demand: $1.20-1.61/hr
- RunPod: $2.18/hr
- Modal: $2.50/hr

---

## 🎯 Best Practices

### 1. Choose Reliable Providers

**Filter criteria:**
- Machine Score: >= 0.9
- Reliability: >= 0.95
- Direct Port Mapping: Yes
- Recent activity: < 1 week ago

### 2. Use Persistent Storage

**Options:**
- Vast.ai persistent storage
- External S3/B2 for models
- Network volumes

**Setup:**
```bash
# Mount external storage
mkdir -p /workspace/models
# Download models from S3/B2
aws s3 sync s3://your-bucket/models /workspace/models
```

### 3. Monitor Instance Health

**Create health check script:**
```python
import requests
import time

def check_instance_health(url):
    try:
        response = requests.get(f"{url}/system_stats", timeout=5)
        return response.status_code == 200
    except:
        return False

while True:
    if not check_instance_health("http://YOUR_INSTANCE:8188"):
        print("Instance unhealthy - restart needed")
        # Trigger restart
    time.sleep(60)
```

### 4. Implement Auto-restart

**On instance failure:**
```bash
#!/bin/bash
# auto_restart.sh

while true; do
    python3 main.py --listen 0.0.0.0 --port 8188
    echo "ComfyUI crashed! Restarting in 5 seconds..."
    sleep 5
done
```

### 5. Load Balancing Across Multiple Instances

**For high traffic:**
```python
import random
import requests

# List of your Vast.ai instances
INSTANCES = [
    "http://instance1:8188",
    "http://instance2:8188",
    "http://instance3:8188",
]

def generate_image(workflow):
    # Simple round-robin
    instance = random.choice(INSTANCES)
    response = requests.post(f"{instance}/prompt", json={"prompt": workflow})
    return response.json()
```

---

## 🔒 Security Considerations

### 1. SSH Key Authentication

**Generate SSH key:**
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/vastai_key
```

**Add to Vast.ai:**
- Go to Account Settings
- Add SSH public key
- Use key for all connections

### 2. Firewall Configuration

**Only open necessary ports:**
- 8188: ComfyUI interface (can restrict to your IP)
- 5000: API server (if using wrapper)
- 22: SSH (change to non-standard port)

### 3. API Authentication

**Add API keys to your wrapper:**
```python
from functools import wraps
from flask import request, jsonify

API_KEYS = {"your-secret-key"}

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key not in API_KEYS:
            return jsonify({"error": "Invalid API key"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/generate', methods=['POST'])
@require_api_key
def generate():
    # Your code here
    pass
```

---

## 🐛 Troubleshooting

### Issue: Instance won't start

**Solutions:**
1. Check if image exists: `docker pull YOUR_IMAGE`
2. Verify disk space is sufficient (50GB+)
3. Try different provider
4. Check Vast.ai status page

### Issue: Slow network performance

**Solutions:**
1. Choose providers with "Direct Port Mapping"
2. Test download speed before renting
3. Use providers in same region as your users
4. Consider using CDN for model downloads

### Issue: Instance keeps getting paused (interruptible)

**Solutions:**
1. Increase your bid price
2. Switch to on-demand instances
3. Use reserved instances
4. Monitor market prices

### Issue: Can't access ComfyUI

**Solutions:**
1. Check if port 8188 is exposed
2. Verify firewall allows incoming connections
3. Check instance logs: `vastai ssh <ID> "tail -f /workspace/logs/comfyui.log"`
4. Restart ComfyUI process

---

## 📈 Performance Optimization

### 1. Pre-download Models

**In your Docker image:**
```dockerfile
# Download common models during build
RUN mkdir -p /workspace/models/checkpoints && \
    wget https://huggingface.co/.../model.safetensors \
    -O /workspace/models/checkpoints/model.safetensors
```

### 2. Use Model Caching

**Mount persistent volume:**
```bash
# When creating instance, mount persistent storage
--env="MODEL_DIR=/models"
```

### 3. Optimize Docker Image

**Multi-stage build:**
```dockerfile
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04 as base
# Install only runtime dependencies

FROM base as final
COPY --from=base /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
# Copy only necessary files
```

---

## 🎬 Migration from Modal/RunPod

### Step 1: Export Current Workflows
```bash
# Export your workflows
cp /path/to/modal/workflows /path/to/vastai/workflows
```

### Step 2: Test on Vast.ai
1. Rent a test instance
2. Deploy ComfyUI
3. Run your workflows
4. Verify outputs

### Step 3: Gradual Migration
1. Week 1: 10% traffic to Vast.ai
2. Week 2: 50% traffic to Vast.ai
3. Week 3: 100% traffic to Vast.ai
4. Week 4: Decommission old platform

---

## 📞 Support Resources

- **Vast.ai Documentation**: https://vast.ai/docs/
- **Vast.ai Discord**: https://discord.gg/vastai
- **CLI Documentation**: https://github.com/vast-ai/vast-python
- **Forum**: https://vast.ai/forum/

---

## ✅ Quick Checklist

- [ ] Created Vast.ai account
- [ ] Added payment method
- [ ] Built ComfyUI Docker image
- [ ] Pushed to Docker Hub
- [ ] Found suitable GPU instance
- [ ] Launched test instance
- [ ] Accessed ComfyUI interface
- [ ] Tested workflow execution
- [ ] Set up API wrapper
- [ ] Configured monitoring
- [ ] Tested with production workflow
- [ ] Calculated actual costs
- [ ] Made migration decision

---

## 💰 Expected Results

**Cost Savings:**
- Modal → Vast.ai: **85% savings** ($1,650 → $250/month)
- RunPod → Vast.ai: **50% savings** ($785 → $375/month)

**Trade-offs:**
- ❌ No auto-scaling (manual management)
- ❌ Longer cold starts (30-60s vs RunPod's 200ms-12s)
- ✅ Much lower cost (50-85% savings)
- ✅ Wide GPU selection

**Best For:**
- Steady workload
- Cost-sensitive projects
- Development/testing
- Long-running instances

**Not Ideal For:**
- Bursty traffic
- Auto-scaling requirements
- Sub-second cold starts
- Fully managed solutions

---

**Ready to start?** Follow the Quick Start Guide above! 🚀

