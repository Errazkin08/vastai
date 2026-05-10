#!/usr/bin/env python3
"""
Chat with Qwen3.5-27B on Vast.ai via local SSH tunnel.

Before running:
1. Make sure SSH tunnel is running (port 18000 forwarded to instance)
2. Install required packages: pip install openai

Usage:
  python3 chat_qwen.py
  python3 chat_qwen.py --hide-reasoning
"""

import argparse
import os
import sys
from openai import OpenAI

def parse_args():
    parser = argparse.ArgumentParser(description="Chat with Qwen3.5-27B on Vast.ai")
    parser.add_argument(
        "--hide-reasoning",
        action="store_true",
        help="Hide model's reasoning content (shows only final answer)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=2000,
        help="Maximum tokens in response (default: 2000, needed for reasoning + answer)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Temperature for sampling (default: 0.7)"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=os.environ.get("VASTAI_BASE_URL"),
        help="OpenAI-compatible base URL (default: VASTAI_BASE_URL env var)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("VASTAI_MODEL_NAME", "Qwen2.5-7B-Instruct"),
        help="Model name (default: VASTAI_MODEL_NAME or Qwen2.5-7B-Instruct)"
    )
    return parser.parse_args()

def main():
    args = parse_args()

    base_url = args.base_url or f"http://localhost:{os.environ.get('VASTAI_LOCAL_PORT', '8080')}/v1"

    # Initialize OpenAI client
    client = OpenAI(
        base_url=base_url,
        api_key="EMPTY"  # SGLang server doesn't require API key
    )

    print("=" * 60)
    print("Qwen Chat (Vast.ai Instance)")
    print("=" * 60)
    print(f"Endpoint: {base_url}")
    print(f"Model: {args.model}")
    print(f"Max tokens per response: {args.max_tokens}")
    if not args.hide_reasoning:
        print("Showing reasoning content")
    else:
        print("Hiding reasoning (showing only final answer)")
    print("\nType your messages. Type '/quit' to exit, '/clear' to clear context.")
    print("=" * 60)

    messages = []
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == '/quit':
            print("Goodbye!")
            break
        elif user_input.lower() == '/clear':
            messages = []
            print("Context cleared.")
            continue
        elif user_input.lower() == '/help':
            print("Commands:")
            print("  /quit     - Exit chat")
            print("  /clear    - Clear conversation history")
            print("  /help     - Show this help")
            print("  /models   - List available models")
            continue
        elif user_input.lower() == '/models':
            try:
                models = client.models.list()
                print(f"Available models: {[m.id for m in models.data]}")
            except Exception as e:
                print(f"Error listing models: {e}")
            continue

        # Add user message to history
        messages.append({"role": "user", "content": user_input})

        print("\nQwen: ", end="", flush=True)

        try:
            # Call the API
            response = client.chat.completions.create(
                model=args.model,
                messages=messages,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                stream=True
            )

            # Stream the response
            full_response = ""
            full_reasoning = ""
            in_reasoning = False
            in_content = False
            last_chunk_type = None

            for chunk in response:
                if not chunk.choices or not chunk.choices[0].delta:
                    continue

                delta = chunk.choices[0].delta

                # Check for reasoning content (non-empty)
                if delta.reasoning_content is not None and delta.reasoning_content != '':
                    reasoning_chunk = delta.reasoning_content
                    full_reasoning += reasoning_chunk

                    if not in_reasoning and not args.hide_reasoning:
                        # First reasoning chunk
                        print("\n[Reasoning]: ", end="", flush=True)
                        in_reasoning = True
                        in_content = False

                    if not args.hide_reasoning:
                        print(reasoning_chunk, end="", flush=True)

                # Check for answer content (non-empty)
                elif delta.content is not None and delta.content != '':
                    content_chunk = delta.content
                    full_response += content_chunk

                    if not in_content:
                        # First content chunk after reasoning
                        if in_reasoning and not args.hide_reasoning:
                            print()  # New line after reasoning
                        print("\n[Answer]: ", end="", flush=True)
                        in_content = True
                        in_reasoning = False

                    print(content_chunk, end="", flush=True)

                # Handle other chunks (role, finish_reason, etc.)
                else:
                    # Check for finish reason
                    if chunk.choices[0].finish_reason:
                        pass  # Could log finish reason if needed

            print()  # Final new line

            # Add assistant response to history (content only, not reasoning)
            if full_response:
                messages.append({"role": "assistant", "content": full_response})
            elif full_reasoning and not full_response:
                # Edge case: only reasoning generated (hit token limit during reasoning)
                # Still add something to history
                messages.append({"role": "assistant", "content": "(Reasoning only, no answer generated)"})

            # If show_reasoning is False but we still want to capture reasoning for token counting?
            # Not needed for now.

        except Exception as e:
            print(f"\nError: {e}")
            print("Check if SSH tunnel is running: ssh -L 18000:localhost:8000 -p XXXXX root@sshX.vast.ai -N")
            # Remove the last user message since we couldn't get a response
            if messages and messages[-1]["role"] == "user":
                messages.pop()

if __name__ == "__main__":
    main()