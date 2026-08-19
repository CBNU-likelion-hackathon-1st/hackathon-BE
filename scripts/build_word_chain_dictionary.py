#!/usr/bin/env python3
"""한국어기초사전 전체 JSON에서 끝말잇기용 명사 목록을 생성한다."""

from __future__ import annotations

import argparse
import io
import json
import re
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any, BinaryIO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "app" / "data" / "word_chain_words.json"
LEXICAL_ENTRY_KEY = '"LexicalEntry"'
VALID_WORD = re.compile(r"[가-힣]{2,}").fullmatch


def iter_lexical_entries(stream: BinaryIO) -> Iterator[dict[str, Any]]:
    """큰 JSON 파일을 메모리에 전부 올리지 않고 LexicalEntry를 하나씩 읽는다."""
    reader = io.TextIOWrapper(stream, encoding="utf-8")
    decoder = json.JSONDecoder()
    buffer = ""
    array_started = False
    reached_eof = False
    needs_more_data = True

    while True:
        if not reached_eof and needs_more_data:
            chunk = reader.read(65_536)
            if chunk:
                buffer += chunk
            else:
                reached_eof = True
            needs_more_data = False

        if not array_started:
            key_index = buffer.find(LEXICAL_ENTRY_KEY)
            if key_index < 0:
                if reached_eof:
                    raise ValueError("LexicalEntry 목록을 찾을 수 없습니다.")
                buffer = buffer[-len(LEXICAL_ENTRY_KEY) :]
                needs_more_data = True
                continue

            array_index = buffer.find("[", key_index + len(LEXICAL_ENTRY_KEY))
            if array_index < 0:
                if reached_eof:
                    raise ValueError("LexicalEntry 배열을 찾을 수 없습니다.")
                buffer = buffer[key_index:]
                needs_more_data = True
                continue

            buffer = buffer[array_index + 1 :]
            array_started = True

        buffer = buffer.lstrip(" \t\r\n,")
        if buffer.startswith("]"):
            return

        try:
            entry, end_index = decoder.raw_decode(buffer)
        except json.JSONDecodeError:
            if reached_eof:
                raise ValueError("LexicalEntry JSON이 중간에 끝났습니다.") from None
            needs_more_data = True
            continue

        if isinstance(entry, dict):
            yield entry
        buffer = buffer[end_index:]
        needs_more_data = len(buffer) < 65_536


def feature_value(features: Any, attribute: str) -> str | None:
    """사전의 feat 객체 또는 배열에서 원하는 값을 찾는다."""
    entries = features if isinstance(features, list) else [features]
    return next(
        (
            feature.get("val")
            for feature in entries
            if isinstance(feature, dict) and feature.get("att") == attribute
        ),
        None,
    )


def word_from_entry(entry: dict[str, Any]) -> str | None:
    """끝말잇기에 사용할 수 있는 일반 명사 표제어만 반환한다."""
    if feature_value(entry.get("feat"), "lexicalUnit") != "단어":
        return None
    if feature_value(entry.get("feat"), "partOfSpeech") != "명사":
        return None

    lemma = entry.get("Lemma")
    if not isinstance(lemma, dict):
        return None
    word = feature_value(lemma.get("feat"), "writtenForm")
    if not isinstance(word, str) or VALID_WORD(word) is None:
        return None
    return word


def build_words(archive_path: Path, seed_words: set[str]) -> tuple[set[str], int]:
    """압축 파일의 모든 JSON에서 조건에 맞는 단어를 모은다."""
    words = set(seed_words)
    entry_count = 0

    with zipfile.ZipFile(archive_path) as archive:
        json_members = sorted(
            (name for name in archive.namelist() if name.lower().endswith(".json")),
            key=lambda name: int(name.split("_", 1)[0]),
        )
        if not json_members:
            raise ValueError("압축 파일에 JSON 사전 파일이 없습니다.")

        for member in json_members:
            with archive.open(member) as stream:
                for entry in iter_lexical_entries(stream):
                    entry_count += 1
                    word = word_from_entry(entry)
                    if word is not None:
                        words.add(word)
            print(f"{member}: 누적 표제어 {entry_count:,}건, 단어 {len(words):,}개")

    return words, entry_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="한국어기초사전 전체 JSON ZIP")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    current = json.loads(args.output.read_text(encoding="utf-8"))
    start_words = current["start_words"]
    seed_words = set(current["words"])
    words, entry_count = build_words(args.archive, seed_words)

    payload = {
        "start_words": sorted(start_words),
        "words": sorted(words),
    }
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"사전 표제어 {entry_count:,}건을 검사했습니다.")
    print(f"끝말잇기 단어 {len(words):,}개를 {args.output}에 저장했습니다.")


if __name__ == "__main__":
    main()
