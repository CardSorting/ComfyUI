# Animagine XL V3.1 Setup Guide

## Overview

Animagine XL V3.1 is a high-quality anime-style image generation model based on SDXL 1.0. This guide will help you download and use it on your Modal ComfyUI instance.

## Quick Start

### Option 1: Automated Setup (Recommended)

Run the setup script that handles everything:

```bash
./setup_civitai_and_download_animagine.sh
```

This script will:
1. Check for Civitai API key
2. Deploy the updated Modal app with Civitai support
3. Download Animagine XL V3.1 (6.46 GB)
4. Download the recommended VAE (319 MB)

### Option 2: Manual Setup

#### Step 1: Get Your Civitai API Key

1. Visit https://civitai.com/user/account
2. Scroll to "API Keys" section
3. Click "Add API Key"
4. Name it (e.g., "Modal ComfyUI")
5. Copy the generated key

#### Step 2: Create Modal Secret

```bash
modal secret create civitai-api-key CIVITAI_API_KEY=YOUR_KEY_HERE
```

#### Step 3: Deploy Updated Modal App

```bash
modal deploy modal/apps/modal_app_fastapi.py
```

#### Step 4: Download the Model

```bash
# Main model (6.46 GB)
modal/scripts/modal_model_manager.sh download-url \
  "https://civitai.com/api/download/models/403131" \
  checkpoints \
  "animagineXLV31_v31.safetensors"

# Recommended VAE (319 MB)
modal/scripts/modal_model_manager.sh download-url \
  "https://civitai.com/api/download/models/403131?type=VAE" \
  vae \
  "sdxl_vae.safetensors"
```

## Testing the Model

### Run the Test Workflow

```bash
./run_workflow.sh test_workflow_animagine_xl.json
```

This workflow is pre-configured with optimal settings for Animagine XL V3.1.

## Recommended Settings

Based on the [official Civitai page](https://civitai.com/models/260267/animagine-xl-v31):

| Setting | Value |
|---------|-------|
| **Resolution** | 1024x1024 (or other SDXL aspect ratios) |
| **Steps** | 20-30 (28 recommended) |
| **CFG Scale** | 5-7 (6.0 recommended) |
| **Sampler** | Euler Ancestral (euler_a) |
| **Scheduler** | Normal |
| **Clip Skip** | 2 |

### Supported Resolutions

```
1024 x 1024 - 1:1 Square
1152 x 896  - 9:7
896 x 1152  - 7:9
1216 x 832  - 19:13
832 x 1216  - 13:19
1344 x 768  - 7:4 Horizontal
768 x 1344  - 4:7 Vertical
1536 x 640  - 12:5 Horizontal
640 x 1536  - 5:12 Vertical
```

## Prompt Guidelines

### Tag Ordering

For best results, follow this structure:

```
1girl/1boy, character name, from what series, everything else in any order
```

### Quality Modifiers (prepend these)

```
masterpiece, best quality, very aesthetic, absurdres
```

### Recommended Positive Prompt Format

```
masterpiece, best quality, very aesthetic, absurdres, [your detailed description with anime-style tags]
```

**Example:**
```
masterpiece, best quality, very aesthetic, absurdres, 1girl, beautiful anime character with long flowing hair, standing in a magical forest, glowing fireflies, ethereal lighting, detailed eyes, vibrant colors, fantasy atmosphere, intricate details, cinematic composition
```

### Recommended Negative Prompt

```
nsfw, lowres, (bad), text, error, fewer, extra, missing, worst quality, jpeg artifacts, low quality, watermark, unfinished, displeasing, oldest, early, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract]
```

## Special Tags

### Quality Modifiers

| Tag | Score Range |
|-----|-------------|
| masterpiece | > 95% |
| best quality | > 85% & ≤ 95% |
| great quality | > 75% & ≤ 85% |
| good quality | > 50% & ≤ 75% |
| normal quality | > 25% & ≤ 50% |
| low quality | > 10% & ≤ 25% |
| worst quality | ≤ 10% |

### Rating Modifiers

| Tag | Content Type |
|-----|--------------|
| safe | General |
| sensitive | Sensitive |
| nsfw | Questionable |
| explicit, nsfw | Explicit |

### Year Modifiers (Art Style)

| Tag | Year Range | Style |
|-----|------------|-------|
| newest | 2021-2024 | Modern anime |
| recent | 2018-2020 | Recent style |
| mid | 2015-2017 | Mid-2010s |
| early | 2011-2014 | Early 2010s |
| oldest | 2005-2010 | Vintage anime |

### Aesthetic Tags

| Tag | Score Range | Quality |
|-----|-------------|---------|
| very aesthetic | > 0.71 | Highly appealing |
| aesthetic | 0.45-0.71 | Appealing |
| displeasing | 0.27-0.45 | Less appealing |
| very displeasing | ≤ 0.27 | Unappealing |

## Model Details

- **Model Type:** Checkpoint (Diffusion-based text-to-image)
- **Base Model:** SDXL 1.0
- **Size:** 6.46 GB (fp16)
- **Developed by:** Cagliostro Research Lab in collaboration with SeaArt.ai
- **License:** Fair AI Public License 1.0-SD
- **Training:** 91,030 steps over 10 epochs on ~2.1M images

## Limitations

1. **Anime-Focused:** Designed specifically for anime-style images, not photorealistic content
2. **Prompt Format:** Optimized for Danbooru-style tags rather than natural language
3. **Detailed Prompts:** Works best with detailed, specific prompts
4. **NSFW Content:** May produce NSFW content even without explicit prompting

## Troubleshooting

### Model Not Found Error

Make sure the model was downloaded successfully:

```bash
modal/scripts/modal_model_manager.sh list
```

Look for `animagineXLV31_v31.safetensors` in the checkpoints folder.

### Blurry Images

- Ensure resolution is at least 1024x1024 (SDXL native resolution)
- Use the quality modifiers in your prompt
- Increase steps to 28-30
- Use CFG scale 6-7

### Poor Quality

- Start prompt with: `masterpiece, best quality, very aesthetic, absurdres`
- Use detailed descriptions with anime-specific tags
- Include the comprehensive negative prompt
- Ensure you're using `euler_ancestral` sampler

## References

- [Civitai Model Page](https://civitai.com/models/260267/animagine-xl-v31?modelVersionId=403131)
- [Modal Documentation](https://modal.com/docs)
- [ComfyUI Documentation](https://github.com/comfyanonymous/ComfyUI)

## Credits

- **Model:** Cagliostro Research Lab & SeaArt.ai
- **Base Model:** Stable Diffusion XL by Stability AI

