#!/usr/bin/env python3
"""Build request.md for a novel-writing Claude API workflow.

Run from anywhere: python scripts/build_request.py
The project root is the parent directory of scripts/.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_required(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"必要なファイルがありません: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"ファイルが空です: {path.relative_to(ROOT)}")
    return text


def read_optional(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip() or None


def parse_instruction(text: str) -> tuple[int, list[str], str]:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    if not match:
        raise ValueError("instruction.md の冒頭に --- で囲ったメタデータを指定してください")
    metadata, body = match.groups()
    chapter = None
    characters: list[str] = []
    in_characters = False
    for line in metadata.splitlines():
        if m := re.fullmatch(r"chapter:\s*(\d+)\s*", line):
            chapter = int(m.group(1))
            in_characters = False
        elif re.fullmatch(r"characters:\s*", line):
            in_characters = True
        elif in_characters and (m := re.fullmatch(r"\s+-\s+([a-zA-Z0-9_-]+)\s*", line)):
            characters.append(m.group(1))
        elif line.strip() and not line.lstrip().startswith("#"):
            raise ValueError(f"未対応のメタデータ: {line!r}")
    if chapter is None or chapter < 1:
        raise ValueError("chapter は1以上の整数で指定してください")
    if not body.strip():
        raise ValueError("執筆指示の本文が空です")
    if len(set(characters)) != len(characters):
        raise ValueError("characters に重複があります")
    return chapter, characters, body.strip()


def section(title: str, source: Path, text: str) -> str:
    return f"## {title}\n\n参照: `{source.relative_to(ROOT).as_posix()}`\n\n{text}"


def build() -> Path:
    chapter, characters, instruction = parse_instruction(read_required(ROOT / "instruction.md"))
    parts = ["# 小説執筆リクエスト", "以下の設定と既存本文を踏まえ、最後の執筆指示に従って本文の続きを執筆してください。既存本文を繰り返さず、生成した本文のみを出力してください。"]

    for title, filename in [("文体・執筆ルール", "style.md"), ("世界設定", "world.md")]:
        path = ROOT / filename
        parts.append(section(title, path, read_required(path)))

    for i in range(1, chapter):
        path = ROOT / "outlines" / f"chapter_{i:02d}.md"
        parts.append(section(f"第{i}章のアウトライン", path, read_required(path)))
        summary = ROOT / "summaries" / f"chapter_{i:02d}.md"
        if text := read_optional(summary):
            parts.append(section(f"第{i}章の確定要約", summary, text))

    outline = ROOT / "outlines" / f"chapter_{chapter:02d}.md"
    parts.append(section(f"第{chapter}章のアウトライン", outline, read_required(outline)))

    for name in characters:
        path = ROOT / "characters" / f"{name}.md"
        parts.append(section(f"登場人物: {name}", path, read_required(path)))

    current = ROOT / "chapters" / f"chapter_{chapter:02d}.md"
    current_text = read_optional(current)
    if current_text:
        parts.append(section(f"第{chapter}章の既存本文（続きの起点）", current, current_text))
    else:
        parts.append(f"## 第{chapter}章の既存本文（続きの起点）\n\n（本文なし。章の冒頭から執筆してください）")

    parts.append(f"## 今回の執筆指示\n\n{instruction}")
    output = ROOT / "request.md"
    output.write_text("\n\n---\n\n".join(parts).rstrip() + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    try:
        output = build()
    except (OSError, ValueError) as exc:
        raise SystemExit(f"エラー: {exc}")
    print(f"生成しました: {output} ({output.stat().st_size:,} bytes)")
