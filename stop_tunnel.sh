#!/bin/bash
# Stop the SSH tunnel for Qwen Vast.ai instance

PID_FILE="/opt/vastai/tunnel.pid"
LOG_FILE="/opt/vastai/tunnel.log"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill $PID 2>/dev/null; then
        echo "Stopped tunnel process $PID"
        rm -f "$PID_FILE"
    else
        echo "Tunnel process $PID not running or already stopped"
        rm -f "$PID_FILE"
    fi
else
    echo "No tunnel PID file found at $PID_FILE"
    echo "Looking for processes on port 18000..."
    PIDS=$(lsof -ti:18000 2>/dev/null)
    if [ -n "$PIDS" ]; then
        echo "Found processes on port 18000: $PIDS"
        echo "Killing them..."
        kill -9 $PIDS 2>/dev/null
        echo "Killed processes: $PIDS"
    else
        echo "No tunnel processes found on port 18000"
    fi
fi

# Also check for sshpass processes
echo "Checking for sshpass processes..."
SSHPASS_PIDS=$(pgrep -f "sshpass.*vast.ai" 2>/dev/null)
if [ -n "$SSHPASS_PIDS" ]; then
    echo "Killing sshpass processes: $SSHPASS_PIDS"
    kill -9 $SSHPASS_PIDS 2>/dev/null
fi

echo "Tunnel stopped."