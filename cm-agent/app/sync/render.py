# -*- coding: utf-8 -*-
"""Render tresci DB -> bloki Notion. Limity docs-first: rich_text element max 2000 zn.,
100 blokow/call (chunkuje notion_api.append_children)."""


def _rt(text):
    """rich_text array z twardym podzialem po 2000 znakow."""
    text = text or ""
    return [{"type": "text", "text": {"content": text[i:i + 2000]}}
            for i in range(0, max(len(text), 1), 2000)]


def _para(line):
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": _rt(line)}}


def md_to_blocks(text, max_blocks=280):
    """Markdown-ish -> bloki (naglowki/#, listy/-, akapity). Twardy sufit blokow -
    ogon trafia do jednego akapitu z adnotacja (strona mirrora ma odbijac stan, nie byc 1:1 PDF)."""
    blocks = []
    for raw in (text or "").split("\n"):
        line = raw.rstrip()
        if not line.strip():
            continue
        if len(blocks) >= max_blocks:
            blocks.append(_para("[... skrocone przez sync worker - pelna tresc w PostgreSQL]"))
            break
        if line.startswith("### "):
            blocks.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": _rt(line[4:])}})
        elif line.startswith("## "):
            blocks.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": _rt(line[3:])}})
        elif line.startswith("# "):
            blocks.append({"object": "block", "type": "heading_1", "heading_1": {"rich_text": _rt(line[2:])}})
        elif line.lstrip().startswith(("- ", "* ")):
            blocks.append({"object": "block", "type": "bulleted_list_item",
                           "bulleted_list_item": {"rich_text": _rt(line.lstrip()[2:])}})
        else:
            blocks.append(_para(line))
    return blocks or [_para("(pusto)")]


def mirror_text(ts, checksum):
    """Tekst callouta - deterministyczny, md5 tego tekstu = kotwica drift checku (fix po tescie C)."""
    return (f"MIRROR Z POSTGRESQL - sekcja nadpisywana przez sync worker. "
            f"Ostatnia synchronizacja: {ts} UTC, md5 {checksum[:12]}. NIE EDYTOWAC.")


def mirror_callout(ts, checksum):
    return {"object": "block", "type": "callout",
            "callout": {"icon": {"type": "emoji", "emoji": "\U0001F512"},
                        "rich_text": _rt(mirror_text(ts, checksum))}}


def entry_blocks(ts, meta, text):
    """Wpis append-only: naglowek z data + tresc."""
    return ([{"object": "block", "type": "heading_3",
              "heading_3": {"rich_text": _rt(f"[sync {ts} UTC] {meta}")}}]
            + md_to_blocks(text, max_blocks=120))
