#!/usr/bin/env python3
import time
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:18000/v1",
    api_key="EMPTY"
)

print("Capturing full streaming response...")
response = client.chat.completions.create(
    model="Qwen3.5-27B",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    max_tokens=500,
    temperature=0.1,
    stream=True
)

reasoning_chunks = []
content_chunks = []
other_chunks = []

for i, chunk in enumerate(response):
    if chunk.choices and chunk.choices[0].delta:
        delta = chunk.choices[0].delta

        if delta.reasoning_content is not None:
            reasoning_chunks.append(delta.reasoning_content)
            print(f"Chunk {i}: reasoning_content='{repr(delta.reasoning_content)}'")
        elif delta.content is not None:
            content_chunks.append(delta.content)
            print(f"Chunk {i}: content='{repr(delta.content)}'")
        else:
            other_chunks.append(chunk)
            # Print finish reason if present
            if chunk.choices[0].finish_reason:
                print(f"Chunk {i}: finish_reason={chunk.choices[0].finish_reason}")
            else:
                print(f"Chunk {i}: other (role={delta.role})")

print(f"\nSummary:")
print(f"Total chunks: {i+1}")
print(f"Reasoning chunks: {len(reasoning_chunks)}")
print(f"Content chunks: {len(content_chunks)}")
print(f"Other chunks: {len(other_chunks)}")

if reasoning_chunks:
    full_reasoning = ''.join(reasoning_chunks)
    print(f"\nFull reasoning ({len(full_reasoning)} chars):")
    print(full_reasoning[:500] + ("..." if len(full_reasoning) > 500 else ""))

if content_chunks:
    full_content = ''.join(content_chunks)
    print(f"\nFull content ({len(full_content)} chars):")
    print(full_content)