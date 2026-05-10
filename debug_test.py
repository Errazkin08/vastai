#!/usr/bin/env python3
import subprocess
import time
import json
from openai import OpenAI

# Start SSH tunnel
def start_tunnel():
    cmd = [
        "sshpass", "-p", "your_instance_api_key_here",
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-L", "18000:localhost:8000",
        "-p", "XXXXX",
        "root@sshX.vast.ai",
        "-N"
    ]
    print(f"Starting tunnel: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3)
    return proc

def test_api():
    client = OpenAI(
        base_url="http://localhost:18000/v1",
        api_key="EMPTY"
    )

    # Test 1: Simple greeting with more tokens
    print("\n=== Test 1: Simple greeting (max_tokens=100) ===")
    try:
        response = client.chat.completions.create(
            model="Qwen3.5-27B",
            messages=[{"role": "user", "content": "Say 'hello' in a friendly way."}],
            max_tokens=100
        )
        print(f"Response object: {response}")
        print(f"Content: {response.choices[0].message.content}")
        print(f"Reasoning content: {response.choices[0].message.reasoning_content if hasattr(response.choices[0].message, 'reasoning_content') else 'No reasoning_content attribute'}")
        print(f"Finish reason: {response.choices[0].finish_reason}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: Without reasoning parser maybe? Try different model name
    print("\n=== Test 2: Different parameters ===")
    try:
        response = client.chat.completions.create(
            model="Qwen3.5-27B",
            messages=[{"role": "user", "content": "What is 2+2?"}],
            max_tokens=50,
            temperature=0.1
        )
        print(f"Content: {response.choices[0].message.content}")
        if hasattr(response.choices[0].message, 'reasoning_content'):
            print(f"Reasoning: {response.choices[0].message.reasoning_content}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 3: Check models endpoint
    print("\n=== Test 3: Check models list ===")
    try:
        models = client.models.list()
        print(f"Available models: {[m.id for m in models.data]}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    tunnel = start_tunnel()
    try:
        # Wait for tunnel to be ready
        time.sleep(5)

        # Test health endpoint
        import requests
        try:
            resp = requests.get("http://localhost:18000/health", timeout=5)
            print(f"Health check: {resp.status_code}")
        except Exception as e:
            print(f"Health check failed: {e}")
            return

        test_api()
    finally:
        if tunnel.poll() is None:
            tunnel.terminate()
            tunnel.wait()
            print("Tunnel terminated")

if __name__ == "__main__":
    main()