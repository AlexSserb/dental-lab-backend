import re

MAX_CHUNK_CHARS = 800
_HEADING_RE = re.compile(r"^## +(.+)$", re.MULTILINE)


class ChunkingService:
    @staticmethod
    def parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
        """Split a markdown file into (`key: value` frontmatter, body). Without frontmatter -> ({}, raw)."""
        raw = raw.lstrip("﻿")
        if not raw.startswith("---"):
            return {}, raw
        parts = raw.split("---", 2)
        if len(parts) < 3:
            return {}, raw

        meta: dict[str, str] = {}
        for line in parts[1].strip().splitlines():
            key, sep, value = line.partition(":")
            if sep:
                meta[key.strip()] = value.strip()
        return meta, parts[2].strip()

    @staticmethod
    def chunk_markdown(title: str, body: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
        """One chunk per `##` section. Every chunk starts with "<title> / <heading>" so it makes sense on its own.
        Sections longer than `max_chars` are packed line by line into several chunks."""
        matches = list(_HEADING_RE.finditer(body))
        sections: list[tuple[str, str]] = []

        preamble = body[:matches[0].start()] if matches else body
        preamble = re.sub(r"^# .*$", "", preamble, flags=re.MULTILINE).strip()  # drop the H1: it duplicates the title
        if preamble:
            sections.append((title, preamble))

        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            content = body[match.end():end].strip()
            if content:
                sections.append((f"{title} / {match.group(1).strip()}", content))

        chunks: list[str] = []
        for prefix, content in sections:
            for piece in ChunkingService._pack_lines(content, max_chars - len(prefix) - 1):
                chunks.append(f"{prefix}\n{piece}")
        return chunks

    @staticmethod
    def _pack_lines(content: str, limit: int) -> list[str]:
        pieces: list[str] = []
        current = ""
        for line in (line.strip() for line in content.splitlines()):
            if not line:
                continue
            if current and len(current) + len(line) + 1 > limit:
                pieces.append(current)
                current = ""
            current = f"{current}\n{line}" if current else line
        if current:
            pieces.append(current)
        return pieces
