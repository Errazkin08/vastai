#!/bin/bash
# Start SSH tunnel for Qwen Vast.ai instance

# Stop any existing tunnel first
/opt/vastai/stop_tunnel.sh > /dev/null 2>&1

# Configuration (update these if needed)
SSH_HOST="sshX.vast.ai"
SSH_PORT="XXXXX"
INSTANCE_API_KEY="your_instance_api_key_here"
CONTAINER_PORT="8000"
LOCAL_PORT="18000"

echo "Starting SSH tunnel to Vast.ai instance..."
echo "SSH: $SSH_HOST:$SSH_PORT"
echo "Forwarding: localhost:$LOCAL_PORT -> localhost:$CONTAINER_PORT"

# Start tunnel in background
sshpass -p "$INSTANCE_API_KEY" ssh \
  -o StrictHostKeyChecking=no \
  -L ${LOCAL_PORT}:localhost:${CONTAINER_PORT} \
  -p $SSH_PORT \
  root@$SSH_HOST \
  -N > /opt/vastai/tunnel.log 2>&1 &

TUNNEL_PID=$!
echo $TUNNEL_PID > /opt/vastai/tunnel.pid

echo "Tunnel started with PID: $TUNNEL_PID"
echo "Logs: /opt/vastai/tunnel.log"
echo "PID: /opt/vastai/tunnel.pid"

# Wait a bit and check if it's working
sleep 5
echo "Checking tunnel health..."
if curl -s http://localhost:$LOCAL_PORT/health > /dev/null 2>&1; then
    echo "✓ Tunnel is working! Health check passed."
    echo ""
    echo "Now you can run:"
    echo "  python3 /opt/vastai/chat_qwen.py"
    echo ""
    echo "Or test with:"
    echo "  curl http://localhost:$LOCAL_PORT/health"
    echo "  python3 -c \"from openai import OpenAI; client = OpenAI(base_url='http://localhost:$LOCAL_PORT/v1', api_key='EMPTY'); print(client.chat.completions.create(model='Qwen3.5-27B', messages=[{'role':'user','content':'Hello'}], max_tokens=1000).choices[0].message.content)\""
else
    echo "✗ Tunnel may not be working. Check logs: /opt/vastai/tunnel.log"
    echo "  Instance may be stopped or SSH connection failed."
    echo "  Check instance status with: vastai show instance ${VASTAI_INSTANCE_ID:-your_instance_id_here} --raw | jq -r '.actual_status'"
fi