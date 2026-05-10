# Agent Task: Deploy Qwen3.5-27B on Vast.ai

## Objective
Launch a Vast.ai GPU instance with Qwen3.5-27B language model running via SGLang server.

## Context
You are working in directory `/opt/vastai`. The user wants to deploy the larger 27B parameter model (Qwen3.5-27B) instead of the previously tested 7B model. Previous attempts with the 27B model encountered GPU out-of-memory (OOM) errors on 24GB VRAM cards.

## Prerequisites
1. **API Key**: Available in `.env` file as `VASTAI_API_KEY=your_vastai_api_key_here`
2. **SSH Key**: Already added to Vast.ai account (user confirmed)
3. **Vast.ai CLI**: Should be installed (`pip install --upgrade vastai`)

## Requirements
- Use a GPU with sufficient VRAM for Qwen3.5-27B (requires ~54GB VRAM for FP16 or quantized version for 24GB cards)
- Deploy using SGLang server image: `lmsysorg/sglang:latest`
- Server should be accessible via OpenAI-compatible API at `http://localhost:8000/v1`
- Include SSH tunnel setup for local testing
- Document the deployed instance details

## Detailed Instructions

### 1. Set up API Key
```bash
vastai set api-key "your_vastai_api_key_here"
```

### 2. Search for GPU Offers
Search for appropriate GPU instances:
- For FP16 version (54GB+ VRAM): Look for A100/H100 or multi-GPU setups
- For quantized version (24GB VRAM): Search for RTX 4090/3090 with 24GB VRAM

Example search commands:
```bash
# For 54GB+ VRAM (FP16 model)
vastai search offers "gpu_ram>=54 num_gpus=1 direct_port_count>=1 rentable=true disk_space>=200 cuda_vers>=12.2" -o dph

# For 24GB VRAM (quantized model)
vastai search offers "gpu_ram>=24 num_gpus=1 direct_port_count>=1 rentable=true disk_space>=200 cuda_vers>=12.2 dph<=2" -o dph
```

### 3. Deploy Instance
Choose the appropriate model path:
- **FP16 version**: `Qwen/Qwen3.5-27B` (requires ~54GB VRAM)
- **Quantized version**: Look for models like `Qwen/Qwen3.5-27B-A3B` (3-bit) or similar if available

Deployment command:
```bash
vastai create instance <OFFER_ID> \
  --image lmsysorg/sglang:latest \
  --disk 200 \
  --label "qwen-27b" \
  --onstart-cmd 'python3 -m sglang.launch_server --model-path Qwen/Qwen3.5-27B --host 0.0.0.0 --port 8000 --tp-size 1 --context-length 32768 --reasoning-parser qwen3 --mem-fraction-static 0.85'
```

**Important**: The correct model identifier is `Qwen/Qwen3.5-27B` (no "-Instruct" suffix needed, as this is already instruction-tuned).

### 4. Monitor Deployment
- Use `vastai show instance <INSTANCE_ID> --raw | jq -r '.actual_status'` to check status
- Instance will go through "loading" → "running" states
- Model download may take 10-30 minutes

### 5. SSH Access and Manual Setup
If onstart command fails or model needs manual intervention:
```bash
# Get SSH details
vastai ssh-url <INSTANCE_ID>

# SSH into instance (using instance API key as password)
sshpass -p "<INSTANCE_API_KEY>" ssh -o StrictHostKeyChecking=no root@<ssh_host> -p <ssh_port>

# Inside instance, start server manually if needed
cd / && python3 -m sglang.launch_server \
  --model-path Qwen/Qwen3.5-27B \
  --host 0.0.0.0 \
  --port 8000 \
  --tp-size 1 \
  --context-length 32768 \
  --reasoning-parser qwen3 \
  --mem-fraction-static 0.85 > /tmp/sglang.log 2>&1 &
```

### 6. Test API
Use the parameterized test scripts:
```bash
# Set environment variables for convenience
# Note: These values are for a destroyed instance; replace with new instance details
export VASTAI_INSTANCE_ID="your_instance_id_here"
export VASTAI_SSH_HOST="sshX.vast.ai"
export VASTAI_SSH_PORT=XXXXX
export VASTAI_INSTANCE_API_KEY="your_instance_api_key_here"
export VASTAI_CONTAINER_PORT=8000
export VASTAI_LOCAL_PORT=18000
export VASTAI_MODEL_NAME="Qwen3.5-27B"

# Test API with SSH tunnel
python3 test_api.py

# Or with explicit arguments
python3 test_api.py --instance-id <INSTANCE_ID> --ssh-host <SSH_HOST> --ssh-port <SSH_PORT> --instance-api-key <INSTANCE_API_KEY>
```

### 7. Script Usage (Parameterized)
All scripts now accept command-line arguments or environment variables:

- **monitor.sh**: Monitor instance status
  ```bash
  ./monitor.sh [INSTANCE_ID]
  # or: export VASTAI_INSTANCE_ID=<INSTANCE_ID>
  # then: ./monitor.sh
  ```

- **poll_status.sh**: Poll until instance is running
  ```bash
  ./poll_status.sh [INSTANCE_ID]
  ```

- **poller.py**: Python-based polling with detailed output
  ```bash
  python3 poller.py --instance-id <INSTANCE_ID>
  ```

- **test_ready.py**: Check if server is ready via SSH
  ```bash
  python3 test_ready.py --ssh-host <SSH_HOST> --ssh-port <SSH_PORT>
  ```

- **test_api.py**: Full API test with SSH tunnel
  ```bash
  python3 test_api.py --instance-api-key <KEY> --ssh-host <HOST> --ssh-port <PORT>
  ```

## Previous Deployment (Destroyed)
- **Instance ID**: your_instance_id_here
- **GPU**: A100 SXM4 (80GB VRAM)
- **SSH**: `sshX.vast.ai:XXXXX`
- **Instance API Key**: `your_instance_api_key_here`
- **Model**: `Qwen/Qwen3.5-27B`
- **Cost**: $1.134/hour (~$27.22/day, $816.60/month)
- **Status**: Destroyed (as of 2026-03-22)
- **Note**: Instance destroyed, SSH and API key no longer valid

## Expected Challenges
1. **GPU Memory**: Qwen3.5-27B in FP16 requires ~54GB VRAM. Most consumer GPUs have 24GB max.
2. **Quantized Models**: May need to find and use quantized versions (3-bit, 4-bit) that fit in 24GB VRAM.
3. **Model Availability**: Ensure the model path exists on Hugging Face.
4. **Download Time**: Large model (27B parameters) will take significant time to download.

## Success Criteria
- Instance deployed and running ✓
- SGLang server accessible via SSH tunnel ✓
- API responds to test queries ✓
- Documentation updated with deployment details ✓
- Scripts parameterized for reuse ✓

## Reference
See `/opt/vastai/howtolaunch.md` for comprehensive deployment guide, troubleshooting, and cost estimates.