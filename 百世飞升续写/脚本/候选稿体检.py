# -*- coding: utf-8 -*-
"""检查候选正文的去空白字数、场景长度、必留/禁用字面项和元叙述。

示例：
    python 脚本/候选稿体检.py 重写压缩/正文/新49_五成.md --min-chars 2800 --max-chars 3300 --scene-count-min 3 --scene-count-max 5 --scene-min 450 --require 五成 --forbid 大潮

本脚本检查结构与字面约束；文风仍交给 文风体检.py，事实连续性仍需人工验收。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SCENE_SEPARATOR = re.compile(r"^[ \t]*——[ \t]*$", re.MULTILINE)
TITLE_LINE = re.compile(r"^\s*#\s*第\s*\d+\s*章")
COMMENT_LINE = re.compile(r"^\s*<!--.*-->\s*$")
META_PATTERN = re.compile(r"本章|上一章|下一章|第\s*\d+\s*章|新\s*\d{1,3}(?=\D|$)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="体检《百世飞升》候选正文")
    parser.add_argument("path", type=Path)
    parser.add_argument("--min-chars", type=int)
    parser.add_argument("--max-chars", type=int)
    parser.add_argument("--scene-min", type=int)
    parser.add_argument("--scene-count-min", type=int)
    parser.add_argument("--scene-count-max", type=int)
    parser.add_argument("--require", action="append", default=[], help="必须出现的字面文本，可重复")
    parser.add_argument("--forbid", action="append", default=[], help="禁止出现的字面文本，可重复")
    parser.add_argument("--allow-meta", action="store_true", help="允许正文出现章号等元叙述")
    return parser.parse_args()


def body_without_metadata(text: str) -> str:
    kept = []
    for line in text.splitlines():
        if TITLE_LINE.match(line) or COMMENT_LINE.match(line):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def compact_length(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def line_hits(text: str, needle: str) -> list[int]:
    return [number for number, line in enumerate(text.splitlines(), 1) if needle in line]


def main() -> int:
    args = parse_args()
    try:
        text = args.path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"[ERROR] 无法读取 {args.path}: {exc}")
        return 2

    body = body_without_metadata(text)
    scenes = [part.strip() for part in SCENE_SEPARATOR.split(body)]
    scene_lengths = [compact_length(part) for part in scenes]
    total = compact_length(body)
    failures: list[str] = []

    if args.min_chars is not None and total < args.min_chars:
        failures.append(f"去空白字数 {total} < {args.min_chars}")
    if args.max_chars is not None and total > args.max_chars:
        failures.append(f"去空白字数 {total} > {args.max_chars}")
    if args.scene_count_min is not None and len(scenes) < args.scene_count_min:
        failures.append(f"场景数 {len(scenes)} < {args.scene_count_min}")
    if args.scene_count_max is not None and len(scenes) > args.scene_count_max:
        failures.append(f"场景数 {len(scenes)} > {args.scene_count_max}")
    if args.scene_min is not None:
        short = [(index + 1, size) for index, size in enumerate(scene_lengths) if size < args.scene_min]
        if short:
            failures.append("短场景 " + ", ".join(f"{index}:{size}" for index, size in short))

    missing = [needle for needle in args.require if needle not in body]
    if missing:
        failures.append("缺少必留：" + "；".join(missing))

    forbidden = [(needle, line_hits(body, needle)) for needle in args.forbid if needle in body]
    if forbidden:
        failures.append(
            "命中禁用：" + "；".join(f"{needle}@{','.join(map(str, lines))}" for needle, lines in forbidden)
        )

    meta_hits = [] if args.allow_meta else [
        (number, match.group(0))
        for number, line in enumerate(body.splitlines(), 1)
        for match in META_PATTERN.finditer(line)
    ]
    if meta_hits:
        failures.append("元叙述：" + "；".join(f"{value}@{line}" for line, value in meta_hits))

    status = "FAIL" if failures else "OK"
    print(f"[{status}] {args.path}")
    print(f"去空白字数：{total}")
    print(f"场景：{len(scenes)}，长度：{' / '.join(map(str, scene_lengths))}")
    if args.require:
        print(f"必留：{len(args.require) - len(missing)}/{len(args.require)}")
    if args.forbid:
        print(f"禁用命中：{len(forbidden)}")
    for failure in failures:
        print(f"- {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    raise SystemExit(main())
