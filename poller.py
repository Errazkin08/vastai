#!/usr/bin/env python3
import subprocess
import json
import time
import sys
import os
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Poll Vast.ai instance status")
    parser.add_argument(
        "--instance-id",
        type=str,
        default=os.environ.get("VASTAI_INSTANCE_ID"),
        help="Vast.ai instance ID (default: from VASTAI_INSTANCE_ID env var)"
    )
    return parser.parse_args()

def get_status(instance_id):
    cmd = ["vastai", "show", "instance", str(instance_id), "--raw"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"Error running vastai: {result.stderr}")
            return None
        data = json.loads(result.stdout)
        return data.get("actual_status"), data.get("status_msg")
    except Exception as e:
        print(f"Exception: {e}")
        return None, None

def main():
    args = parse_args()
    if not args.instance_id:
        print("Error: No instance ID provided")
        print("Usage: python3 poller.py --instance-id INSTANCE_ID")
        print("   or: export VASTAI_INSTANCE_ID=12345")
        sys.exit(1)

    print(f"Polling instance {args.instance_id}...")
    last_msg = ""
    while True:
        status, msg = get_status(args.instance_id)
        if status is None:
            time.sleep(30)
            continue
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        if msg != last_msg:
            print(f"{timestamp} Status: {status}, Message: {msg}")
            last_msg = msg
        else:
            print(f"{timestamp} Status: {status}")
        if status == "running":
            print("Instance is now running!")
            sys.exit(0)
        time.sleep(60)

if __name__ == "__main__":
    main()