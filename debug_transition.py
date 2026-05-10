#!/usr/bin/env python3
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:18000/v1",
    api_key="EMPTY"
)

print("Testing transition from reasoning to content...")
response = client.chat.completions.create(
    model="Qwen3.5-27B",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    max_tokens=500,
    temperature=0.1,
    stream=True
)

last_type = None
reasoning_buf = []
content_buf = []

for i, chunk in enumerate(response):
    if not chunk.choices or not chunk.choices[0].delta:
        continue

    delta = chunk.choices[0].delta
    current_type = None
    val = None

    if delta.reasoning_content is not None:
        current_type = "reasoning"
        val = delta.reasoning_content
        reasoning_buf.append(val)
    elif delta.content is not None:
        current_type = "content"
        val = delta.content
        content_buf.append(val)
    else:
        current_type = "other"
        val = None

    if current_type != last_type:
        if last_type is not None:
            print(f"\n--- Transition: {last_type} -> {current_type} ---")
        last_type = current_type

    if val is not None:
        print(val, end="", flush=True)

    # Stop if we have both reasoning and content and content is substantial
    if content_buf and len(''.join(content_buf)) > 10:
        print(f"\n\nStopping early after getting content...")
        break

print(f"\n\nFinal:")
print(f"Reasoning length: {len(''.join(reasoning_buf))}")
print(f"Content length: {len(''.join(content_buf))}")
print(f"Content: {''.join(content_buf)}")