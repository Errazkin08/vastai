#!/bin/bash

# Usage: ./monitor.sh [INSTANCE_ID]
#   INSTANCE_ID: Vast.ai instance ID (default: from VASTAI_INSTANCE_ID env var)

set -e

INSTANCE_ID="${1:-${VASTAI_INSTANCE_ID}}"

if [[ -z "$INSTANCE_ID" ]]; then
    echo "Error: No instance ID provided"
    echo "Usage: $0 [INSTANCE_ID]"
    echo "   or: export VASTAI_INSTANCE_ID=12345"
    exit 1
fi

echo "Monitoring instance $INSTANCE_ID..."

while true; do
    status=$(vastai show instance "$INSTANCE_ID" --raw 2>&1 | jq -r '.actual_status')
    echo "$(date): $status"
    if [[ "$status" != "loading" ]]; then
        echo "Status changed to $status at $(date)"
        break
    fi
    sleep 60
done