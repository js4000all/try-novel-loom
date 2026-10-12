#!/usr/bin/env python

import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=2024,
    thinking={"type": "disabled"},
    system=(
        "あなたは日本語小説の執筆アシスタントです。"
        "設定に基づき、指定されたシーンを執筆してください。"
    ),
    messages=[
        {
            "role": "user",
            "content": (
                "富士登頂に臨む二人の前夜祭（夕食）の様子。"
                "高尾山から始まり、これまでに重ねたステップを振り返る。"
            ),
        }
    ],
)

print("stop_reason:", response.stop_reason)
print("content types:", [b.type for b in response.content])
print("usage:", response.usage)
print(" --")
print(response.content[0].text)
