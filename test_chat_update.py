#!/usr/bin/env python3
import subprocess
import time
import sys

def test_default():
    """Test with default (show reasoning)"""
    print("=== Testing with default (reasoning shown) ===")
    proc = subprocess.Popen(
        [sys.executable, "/opt/vastai/chat_qwen.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Send a simple query and quit
    query = "What is 2+2?\n/quit\n"
    try:
        stdout, stderr = proc.communicate(input=query, timeout=30)
        print("Output captured:")
        print(stdout[:2000])  # Limit output
        if stderr:
            print("Stderr:", stderr)
    except subprocess.TimeoutExpired:
        proc.kill()
        print("Timeout!")

def test_hide_reasoning():
    """Test with --hide-reasoning"""
    print("\n=== Testing with --hide-reasoning ===")
    proc = subprocess.Popen(
        [sys.executable, "/opt/vastai/chat_qwen.py", "--hide-reasoning"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    query = "What is 2+2?\n/quit\n"
    try:
        stdout, stderr = proc.communicate(input=query, timeout=30)
        print("Output captured:")
        print(stdout[:1000])
        if stderr:
            print("Stderr:", stderr)
    except subprocess.TimeoutExpired:
        proc.kill()
        print("Timeout!")

if __name__ == "__main__":
    test_default()
    test_hide_reasoning()