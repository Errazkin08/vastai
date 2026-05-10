#!/usr/bin/env python3
import json
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:18000/v1",
    api_key="EMPTY"
)

print("Testing streaming chunk structure...")
response = client.chat.completions.create(
    model="Qwen3.5-27B",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    max_tokens=500,
    temperature=0.1,
    stream=True
)

print("Streaming chunks:")
for i, chunk in enumerate(response):
    print(f"\n--- Chunk {i} ---")
    print(f"Chunk object: {chunk}")
    print(f"Chunk type: {type(chunk)}")
    print(f"Chunk dir: {[a for a in dir(chunk) if not a.startswith('_')]}")

    if hasattr(chunk, 'choices') and chunk.choices:
        choice = chunk.choices[0]
        print(f"Choice: {choice}")
        print(f"Choice dir: {[a for a in dir(choice) if not a.startswith('_')]}")

        if hasattr(choice, 'delta'):
            delta = choice.delta
            print(f"Delta: {delta}")
            print(f"Delta dir: {[a for a in dir(delta) if not a.startswith('_')]}")

            # Check all attributes
            for attr in ['content', 'reasoning_content', 'role', 'tool_calls', 'function_call']:
                if hasattr(delta, attr):
                    val = getattr(delta, attr)
                    if val is not None:
                        print(f"  delta.{attr}: {repr(val)}")

    # Stop after a few chunks
    if i >= 5:
        print("\n... (showing first 5 chunks)")
        break

print("\n\nTesting non-streaming for comparison...")
non_stream = client.chat.completions.create(
    model="Qwen3.5-27B",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    max_tokens=500,
    temperature=0.1,
    stream=False
)
print(f"Non-stream response type: {type(non_stream)}")
print(f"Has reasoning_content: {hasattr(non_stream.choices[0].message, 'reasoning_content')}")
if hasattr(non_stream.choices[0].message, 'reasoning_content'):
    reasoning = non_stream.choices[0].message.reasoning_content
    print(f"Reasoning length: {len(reasoning)} chars")
    print(f"Reasoning preview: {reasoning[:200]}...")
print(f"Content: {non_stream.choices[0].message.content}")