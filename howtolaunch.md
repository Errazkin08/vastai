# Deploying Qwen Models on Vast.ai

## Prerequisites
1. Install Vast.ai CLI: `pip install --upgrade vastai`
2. Set API key: `export VAST_API_KEY="your_api_key"` or `vastai set api-key "your_api_key"`
3. Have SSH key added to Vast.ai account for SSH access

## Scripts Overview
The `/opt/vastai` directory contains parameterized scripts for deployment management:

- **monitor.sh**: Monitor instance status until it exits "loading" state
- **poll_status.sh**: Poll until instance reaches "running" state
- **poller.py**: Python-based polling with detailed status messages
- **test_ready.py**: Check if SGLang server is ready via SSH health check
- **test_api.py**: Full API test with automatic SSH tunnel setup

**Usage**: All scripts accept command-line arguments or environment variables:
```bash
# Set environment variables once
export VASTAI_INSTANCE_ID="your_instance_id_here"
export VASTAI_SSH_HOST="sshX.vast.ai"
export VASTAI_SSH_PORT=XXXXX
export VASTAI_INSTANCE_API_KEY="your_instance_api_key_here"
export VASTAI_CONTAINER_PORT=8000
export VASTAI_LOCAL_PORT=18000
export VASTAI_MODEL_NAME="Qwen3.5-27B"

# Then run scripts without arguments
./monitor.sh
python3 test_api.py
```

## Steps

### 1. Search for GPU Offers
```bash
# For 27B model (24GB+ VRAM)
vastai search offers "gpu_ram>=24 num_gpus=1 direct_port_count>=1 rentable=true disk_space>=200 cuda_vers>=12.2 dph<=2" -o dph

# For larger models (80GB+ VRAM)
vastai search offers "gpu_ram>=80 num_gpus=1 direct_port_count>=1 rentable=true disk_space>=200 cuda_vers>=12.2" -o dph
```

### 2. Deploy Instance
```bash
# For Qwen2.5-7B-Instruct (fits 24GB VRAM)
vastai create instance <OFFER_ID> \
  --image lmsysorg/sglang:latest \
  --disk 200 \
  --label "qwen-7b" \
  --onstart-cmd 'python3 -m sglang.launch_server --model-path Qwen/Qwen2.5-7B-Instruct --host 0.0.0.0 --port 8000 --tp-size 1 --context-length 32768 --reasoning-parser qwen3 --mem-fraction-static 0.85'

# For Qwen3.5-27B (requires ~54GB VRAM for FP16)
vastai create instance <OFFER_ID> \
  --image lmsysorg/sglang:latest \
  --disk 200 \
  --label "qwen-27b" \
  --onstart-cmd 'python3 -m sglang.launch_server --model-path Qwen/Qwen3.5-27B --host 0.0.0.0 --port 8000 --tp-size 1 --context-length 32768 --reasoning-parser qwen3 --mem-fraction-static 0.85'

# For quantized Qwen3.5-27B (fits 24GB VRAM)
# Use quantized models like Qwen/Qwen3.5-27B-A3B (3-bit) if available
```

### 3. Check Instance Status
```bash
# Manual check
vastai show instance <INSTANCE_ID> --raw | jq -r '.actual_status'
vastai show instance <INSTANCE_ID> --raw | jq -r '.ssh_host, .ssh_port'

# Using monitoring scripts (see Scripts Overview section)
./monitor.sh <INSTANCE_ID>
./poll_status.sh <INSTANCE_ID>
python3 poller.py --instance-id <INSTANCE_ID>
```

### 4. SSH Access
```bash
# Get SSH URL and instance API key
vastai ssh-url <INSTANCE_ID>
vastai show instance <INSTANCE_ID> --raw | jq -r '.instance_api_key'

# SSH using SSH key (if added to Vast.ai account)
ssh -o StrictHostKeyChecking=no root@<ssh_host> -p <ssh_port>

# SSH using instance API key as password (requires sshpass)
sshpass -p "<INSTANCE_API_KEY>" ssh -o StrictHostKeyChecking=no root@<ssh_host> -p <ssh_port>
```

### 5. Manual Server Start (if onstart fails)
Once logged in via SSH:
```bash
# Start server in background (using instance API key as password)
sshpass -p "<INSTANCE_API_KEY>" ssh -o StrictHostKeyChecking=no root@<ssh_host> -p <ssh_port> 'cd / && python3 -m sglang.launch_server --model-path Qwen/Qwen3.5-27B --host 0.0.0.0 --port 8000 --tp-size 1 --context-length 32768 --reasoning-parser qwen3 --mem-fraction-static 0.85 > /tmp/sglang.log 2>&1 &'

# Or SSH into instance first, then run manually
ssh -o StrictHostKeyChecking=no root@<ssh_host> -p <ssh_port>
# Inside instance:
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

#### Using Parameterized Scripts
All scripts in `/opt/vastai` accept command-line arguments or environment variables:

```bash
# Set environment variables for convenience
export VASTAI_INSTANCE_ID="your_instance_id_here"
export VASTAI_SSH_HOST="sshX.vast.ai"
export VASTAI_SSH_PORT=XXXXX
export VASTAI_INSTANCE_API_KEY="your_instance_api_key_here"
export VASTAI_CONTAINER_PORT=8000
export VASTAI_LOCAL_PORT=18000
export VASTAI_MODEL_NAME="Qwen3.5-27B"

# Test API with SSH tunnel (auto-starts and tears down tunnel)
python3 test_api.py

# Check if server is ready via SSH
python3 test_ready.py

# Monitor instance status
./monitor.sh
./poll_status.sh
python3 poller.py
```

#### Manual SSH Tunnel
```bash
# SSH tunnel (run in background)
ssh -L 18000:localhost:8000 -p <ssh_port> root@<ssh_host> -N &

# Test with Python
python3 -c "
from openai import OpenAI
client = OpenAI(base_url='http://localhost:18000/v1', api_key='EMPTY')
response = client.chat.completions.create(
    model='Qwen3.5-27B',
    messages=[{'role':'user','content':'Hello'}],
    max_tokens=10
)
print(response.choices[0].message.content)
"
```

### 7. Monitor Logs
```bash
# Instance logs
vastai logs <INSTANCE_ID>

# SSH and check server logs
ssh -p <ssh_port> root@<ssh_host> 'tail -f /tmp/sglang.log'
```

### 8. Instance Management
```bash
# Start/stop instance
vastai start instance <INSTANCE_ID>
vastai stop instance <INSTANCE_ID>

# Destroy instance (permanent deletion)
vastai destroy instance <INSTANCE_ID>

# Check instance status
vastai show instance <INSTANCE_ID> --raw | jq -r '.actual_status'

# List all your instances
vastai search instances
```

**Important Notes:**
- **Destroying an instance permanently deletes it and all data on the instance disk**
- Stopping an instance preserves the disk but stops billing for GPU time
- Starting a stopped instance resumes billing
- Instance IDs can be found using `vastai search instances`
- After destruction, the instance ID becomes invalid and cannot be recovered

## Troubleshooting

### GPU Out of Memory
- Use smaller model (7B instead of 27B)
- Use quantized models (look for -A3B, -A10B suffixes)
- Reduce `--mem-fraction-static` (default 0.85)

### Instance Stuck in "loading"
- Check logs: `vastai logs <INSTANCE_ID>`
- Restart: `vastai start instance <INSTANCE_ID>`
- May need to wait for Docker image download (5-30 minutes)

### SSH Connection Issues
- Ensure SSH key is added to Vast.ai account, OR use instance API key as password
- Try after 1-2 minutes if connection refused (instance may still be booting)
- Check instance status is "running"
- Use `sshpass -p "<INSTANCE_API_KEY>" ssh ...` if SSH key authentication fails

## Example Deployment (Current)
- Instance ID: `your_instance_id_here`
- GPU: A100 SXM4 (80GB VRAM)
- SSH: `ssh root@sshX.vast.ai -p XXXXX`
- Instance API Key: `your_instance_api_key_here`
- Model: Qwen/Qwen3.5-27B
- API: `http://localhost:8000/v1` (inside instance)
- Cost: $1.134/hour (~$27.22/day, $816.60/month)
- Status: Destroyed (as of 2026-03-22)
- **Note**: Instance destroyed, SSH and API key no longer valid
## Example Deployment (Previous 7B Model)
- Instance ID: `previous_instance_id_here` (stopped)
- SSH: `ssh root@sshY.vast.ai -p YYYYY`
- Model: Qwen2.5-7B-Instruct
- **Note**: Replace placeholders with actual values from your deployment

## Cost Estimate
- RTX 3090 (24GB): ~$0.12-$0.18/hour
- A100 (80GB): ~$1.10-$1.60/hour (example: $1.134/hour for previous deployment)
- Download time: 10-30 minutes for initial model load
- Storage: 200GB disk included
- **Note**: Costs accrue only while instance is running. Stop instance with `vastai stop instance <ID>` to pause billing.