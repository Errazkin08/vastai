#!/usr/bin/env python3
import subprocess
import time
import sys
import os
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Check if Qwen API server is ready")
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
    parser.add_argument(
        "--max-wait",
        type=int,
        default=int(os.environ.get("VASTAI_MAX_WAIT", 1200)),
        help="Maximum wait time in seconds (default: 1200, 20 minutes)"
    )
    return parser.parse_args()

def check_health(ssh_host, ssh_port, container_port):
    """Check if server health endpoint responds via SSH"""
    cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no',
        '-p', str(ssh_port),
        f'root@{ssh_host}',
        'curl', '-s', '-o', '/dev/null', '-w', '"%{http_code}"',
        f'http://localhost:{container_port}/health', '2>/dev/null'
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        # Output will have quotes like "200"
        return result.stdout.strip('"').strip() == '200'
    except:
        return False

def main():
    args = parse_args()

    print(f"Waiting for Qwen API server to be ready...")
    print(f"SSH: {args.ssh_host}:{args.ssh_port}")
    print(f"Container port: {args.container_port}")
    print(f"Max wait: {args.max_wait}s")

    start = time.time()

    while time.time() - start < args.max_wait:
        if check_health(args.ssh_host, args.ssh_port, args.container_port):
            print(f"Server is ready! Elapsed: {time.time() - start:.1f}s")
            print("\nSSH tunnel command:")
            print(f"ssh -L {args.local_port}:localhost:{args.container_port} -p {args.ssh_port} root@{args.ssh_host} -N")
            print("\nTest API with:")
            print(f"python3 -c \"from openai import OpenAI; client = OpenAI(base_url='http://localhost:{args.local_port}/v1', api_key='EMPTY'); print(client.chat.completions.create(model='{args.model_name}', messages=[{{'role':'user','content':'Hello'}}], max_tokens=10).choices[0].message.content)\"")
            return
        print(f"Waiting... ({time.time() - start:.0f}s elapsed)")
        time.sleep(30)

    print("Timeout waiting for server")
    sys.exit(1)

if __name__ == "__main__":
    main()