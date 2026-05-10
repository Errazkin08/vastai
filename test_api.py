#!/usr/bin/env python3
import time
import subprocess
import sys
import os
import argparse
import requests
import json
from openai import OpenAI

def parse_args():
    parser = argparse.ArgumentParser(description="Test Qwen API on Vast.ai instance")
    parser.add_argument(
        "--instance-id",
        type=str,
        default=os.environ.get("VASTAI_INSTANCE_ID"),
        help="Vast.ai instance ID (default: from VASTAI_INSTANCE_ID env var)"
    )
    parser.add_argument(
        "--ssh-host",
        type=str,
        default=os.environ.get("VASTAI_SSH_HOST", "sshX.vast.ai"),
        help="SSH host (default: from VASTAI_SSH_HOST env var or sshX.vast.ai)"
    )
    parser.add_argument(
        "--ssh-port",
        type=int,
        default=int(os.environ.get("VASTAI_SSH_PORT", 13792)),
        help="SSH port (default: from VASTAI_SSH_PORT env var or 13792)"
    )
    parser.add_argument(
        "--instance-api-key",
        type=str,
        default=os.environ.get("VASTAI_INSTANCE_API_KEY"),
        help="Instance API key (default: from VASTAI_INSTANCE_API_KEY env var)"
    )
    parser.add_argument(
        "--container-port",
        type=int,
        default=int(os.environ.get("VASTAI_CONTAINER_PORT", 8000)),
        help="Container port where SGLang server runs (default: 8000)"
    )
    parser.add_argument(
        "--local-port",
        type=int,
        default=int(os.environ.get("VASTAI_LOCAL_PORT", 18000)),
        help="Local port for SSH forwarding (default: 18000)"
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default=os.environ.get("VASTAI_MODEL_NAME", "Qwen3.5-27B"),
        help="Model name for API calls (default: Qwen3.5-27B)"
    )
    return parser.parse_args()

def start_ssh_tunnel(ssh_host, ssh_port, instance_api_key, container_port, local_port):
    """Start SSH tunnel in background, return subprocess.Popen"""
    cmd = [
        "sshpass", "-p", instance_api_key,
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-L", f"{local_port}:localhost:{container_port}",
        "-p", str(ssh_port),
        f"root@{ssh_host}",
        "-N"  # no remote command, just forward ports
    ]
    print(f"Starting SSH tunnel: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)  # give it time to establish
    if proc.poll() is not None:
        # process terminated
        stdout, stderr = proc.communicate()
        print(f"SSH tunnel failed: {stderr.decode()}")
        return None
    return proc

def test_connection(local_port):
    """Test if the server is reachable via local tunnel"""
    try:
        response = requests.get(f"http://localhost:{local_port}/health", timeout=5)
        if response.status_code == 200:
            return True
    except Exception as e:
        print(f"Connection test failed: {e}")
    return False

def test_openai(local_port, model_name):
    """Test using OpenAI client"""
    client = OpenAI(
        base_url=f"http://localhost:{local_port}/v1",
        api_key="EMPTY"
    )
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Say 'hello'"}],
            max_tokens=10
        )
        print(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"OpenAI client error: {e}")
        return False

def main():
    args = parse_args()

    # Validate required arguments
    if not args.instance_api_key:
        print("Error: Instance API key is required")
        print("Provide via --instance-api-key or VASTAI_INSTANCE_API_KEY env var")
        sys.exit(1)

    print(f"Testing Qwen API on Vast.ai instance {args.instance_id or '(unknown ID)'}")
    print(f"SSH: {args.ssh_host}:{args.ssh_port}")
    print(f"Local port forward: {args.local_port} -> localhost:{args.container_port}")
    print(f"Model: {args.model_name}")

    # Start SSH tunnel
    tunnel = start_ssh_tunnel(
        args.ssh_host, args.ssh_port, args.instance_api_key,
        args.container_port, args.local_port
    )
    if tunnel is None:
        print("Failed to start SSH tunnel. Exiting.")
        sys.exit(1)

    try:
        # Wait for server to be ready
        max_attempts = 30
        for i in range(max_attempts):
            print(f"Attempt {i+1}/{max_attempts}: Checking server health...")
            if test_connection(args.local_port):
                print("Server is reachable!")
                break
            time.sleep(10)
        else:
            print("Server not ready after multiple attempts.")
            sys.exit(1)

        # Test OpenAI client
        print("Testing OpenAI client...")
        if test_openai(args.local_port, args.model_name):
            print("Success! API is working.")
        else:
            print("OpenAI client test failed.")
    finally:
        if tunnel.poll() is None:
            tunnel.terminate()
            tunnel.wait()
            print("SSH tunnel terminated.")

if __name__ == "__main__":
    main()