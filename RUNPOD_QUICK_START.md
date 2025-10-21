# RunPod Serverless - Quick Start Checklist

## ✅ What I've Created For You

I've set up a complete RunPod Serverless implementation in the `runpod/` directory:

```
runpod/
├── runpod_handler.py         # Main serverless handler
├── Dockerfile                # Docker container definition
├── requirements-runpod.txt   # Dependencies
├── deploy.sh                 # Automated deployment script ⭐
├── test_runpod.py           # Testing script
└── README.md                # Detailed documentation
```

## 🚀 Deployment Steps (30 minutes)

### Step 1: Prerequisites (5 minutes)

- [ ] **Docker Hub account**: https://hub.docker.com (free signup)
- [ ] **RunPod account**: https://www.runpod.io (sign up, add payment method)
- [ ] **Docker installed**: Check with `docker --version`
- [ ] **Docker logged in**: Run `docker login`

### Step 2: Build & Deploy Docker Image (15 minutes)

```bash
# Set your Docker Hub username
export DOCKER_USERNAME=your_actual_dockerhub_username

# Run the automated deployment
cd /Users/bozoegg/ComfyUIAlt
./runpod/deploy.sh
```

This will:
- Build the Docker image (~10-15 minutes first time)
- Push to Docker Hub
- Display your next steps

### Step 3: Deploy to RunPod (5 minutes)

1. **Go to RunPod Console**:
   - https://www.runpod.io/console/serverless

2. **Click "New Endpoint"**

3. **Configure Your Endpoint**:
   ```
   Name: comfyui-api
   Docker Image: your_dockerhub_username/comfyui-runpod:latest
   GPU Type: RTX 4090 (recommended) or RTX 3090 (cheaper)
   Min Workers: 0
   Max Workers: 3
   Idle Timeout: 60 seconds
   Container Disk: 20 GB
   ```

4. **Click "Deploy"** and wait ~2-5 minutes

5. **Copy your credentials**:
   - Endpoint ID (e.g., `abc123def456`)
   - API Key (from your account settings)

### Step 4: Test Your Deployment (5 minutes)

```bash
# Test with the included script
python runpod/test_runpod.py YOUR_ENDPOINT_ID YOUR_API_KEY

# You should see:
# ✓ Job submitted successfully!
# ✓ Job completed successfully!
# ✓ Saved: runpod_test_output/output_001.png
```

## 💰 Expected Costs

**RTX 4090 @ $0.50/hr:**
- 100 requests/day: ~$15/month
- 1000 requests/day: ~$146/month
- 5000 requests/day: ~$729/month

**Savings vs Modal: ~52%**

## ⚡ Performance

- **Cold start**: 5-12 seconds (vs Modal's 30-120s)
- **Auto-scaling**: 0 to 100+ instances
- **API response**: Fast and reliable

## 📝 What You Need

Before starting, have ready:

1. **Docker Hub username** (create at https://hub.docker.com)
2. **RunPod account** (create at https://www.runpod.io)
3. **Payment method** added to RunPod
4. **~30 minutes** of time

## 🔧 Customization (Optional)

### Add Your Models

Edit `runpod/Dockerfile` to include your models:

```dockerfile
# Add before CMD line
RUN cd /app/models/checkpoints && \
    wget https://huggingface.co/stabilityai/sdxl-turbo/resolve/main/sd_xl_turbo_1.0_fp16.safetensors && \
    wget https://your-other-model-url/model.safetensors
```

Then rebuild and redeploy.

### Use Your Workflows

Replace the test workflow in `runpod/test_runpod.py` or provide your own:

```bash
python runpod/test_runpod.py ENDPOINT_ID API_KEY your_workflow.json
```

## 🐛 Troubleshooting

### "Docker not found"
```bash
# Install Docker: https://docs.docker.com/get-docker/
# Then verify: docker --version
```

### "Permission denied" on deploy.sh
```bash
chmod +x runpod/deploy.sh
```

### "Not logged into Docker Hub"
```bash
docker login
# Enter your Docker Hub credentials
```

### Build takes too long
- Normal! First build: 10-15 minutes
- Subsequent builds: 2-5 minutes (cached layers)

### Deployment fails on RunPod
1. Check Docker image exists: https://hub.docker.com
2. Verify image name exactly matches
3. Check RunPod status page

## 📚 Full Documentation

- **Detailed guide**: `runpod/README.md`
- **Migration guide**: `RUNPOD_MIGRATION_GUIDE.md`
- **Decision guide**: `RUNPOD_VS_VASTAI_DECISION.md`

## 🎯 Next Steps After Deployment

1. **Test with your real workflows**: Replace test workflow
2. **Monitor costs**: Check RunPod dashboard
3. **Optimize workers**: Adjust min/max based on traffic
4. **Add models**: Include models you actually need
5. **Integrate with your app**: Use the API in production

## ⏱️ Timeline

- **Setup time**: 30 minutes
- **First Docker build**: 10-15 minutes
- **RunPod deployment**: 2-5 minutes
- **Total**: ~40-50 minutes first time

## 💡 Pro Tips

1. **Keep Docker Hub username handy** - you'll need it
2. **Save your RunPod credentials** - Endpoint ID and API Key
3. **Test locally first** - build Docker image and test it works
4. **Start small** - Use RTX 3090 for testing, scale to 4090 if needed
5. **Monitor costs** - Check RunPod dashboard daily at first

## 🚦 Status Check

Before starting, verify:

```bash
# Docker is installed and running
docker --version
docker ps

# You're logged into Docker Hub
docker info | grep Username

# You're in the right directory
pwd  # Should show .../ComfyUIAlt
ls runpod/  # Should show deploy.sh and other files
```

## 🎬 Ready to Start?

```bash
# Set your Docker Hub username
export DOCKER_USERNAME=your_dockerhub_username

# Run the deployment!
./runpod/deploy.sh
```

Then follow the on-screen instructions!

---

**Need help?** Check `runpod/README.md` for detailed documentation.

**Questions?** All the files are documented and ready to use.

**Ready when you are!** 🚀

