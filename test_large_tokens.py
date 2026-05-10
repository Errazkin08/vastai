#!/usr/bin/env python3
import subprocess
import time
import requests
import json

def start_tunnel():
    cmd = [
        "sshpass", "-p", "your_instance_api_key_here",
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-L", "18000:localhost:8000",
        "-p", "XXXXX",
        "root@sshX.vast.ai",
        "-N"
    ]
    print(f"Starting tunnel")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5)
    return proc

def test_with_tokens(max_tokens=1000):
    url = "http://localhost:18000/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    # Test with system message asking for direct answer
    data = {
        "model": "Qwen3.5-27B",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Provide direct answers without showing your thinking process."},
            {"role": "user", "content": "Say hello in a friendly way."}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.1
    }

    print(f"\n=== Testing with max_tokens={max_tokens} ===")
    response = requests.post(url, headers=headers, json=data, timeout=30)
    result = response.json()

    print(f"Status: {response.status_code}")
    print(f"Finish reason: {result['choices'][0]['finish_reason']}")
    print(f"Content: {result['choices'][0]['message']['content']}")
    print(f"Has reasoning_content: {'reasoning_content' in result['choices'][0]['message']}")
    if 'reasoning_content' in result['choices'][0]['message']:
        reasoning = result['choices'][0]['message']['reasoning_content']
        print(f"Reasoning length: {len(reasoning)} chars")
        print(f"Reasoning preview: {reasoning[:200]}...")

    # Count tokens
    usage = result.get('usage', {})
    print(f"Prompt tokens: {usage.get('prompt_tokens')}")
    print(f"Completion tokens: {usage.get('completion_tokens')}")
    print(f"Total tokens: {usage.get('total_tokens')}")

    return result

def main():
    tunnel = start_tunnel()
    try:
        # Wait for tunnel
        time.sleep(5)

        # Test health
        health = requests.get("http://localhost:18000/health", timeout=5)
        print(f"Health: {health.status_code}")

        # Test with increasing token limits
        for tokens in [200, 500, 1000, 1500]:
            try:
                result = test_with_tokens(tokens)
                content = result['choices'][0]['message']['content']
                if content is not None and content.strip():
                    print(f"Success! Got content with {tokens} tokens: {content[:100]}...")
                    break
            except Exception as e:
                print(f"Error with {tokens} tokens: {e}")
                continue

    finally:
        if tunnel.poll() is None:
            tunnel.terminate()
            tunnel.wait()
            print("Tunnel terminated")

if __name__ == "__main__":
    main()