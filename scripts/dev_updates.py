#!/usr/bin/env python3
# note this is AI slop - generated, unreviewed.

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
SEPARATOR_CELL_RE = re.compile(r"^\s*:?-{1,}:?\s*$")


def split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def is_separator_row(line: str) -> bool:
    cells = split_row(line)
    return len(cells) > 0 and all(SEPARATOR_CELL_RE.match(c) for c in cells)


@dataclass
class Table:
    header: list[str]
    aligns: list[str]
    rows: list[list[str]]

    def key_of(self, row: list[str]) -> str:
        return normalize_cell(row[0]) if row else ""


@dataclass
class TextBlock:
    lines: list[str] = field(default_factory=list)


def normalize_cell(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def sort_key(name_cell: str):
    # Sort by the display name inside the first [...] link, case-insensitively,
    # so ordering matches how the table is read alphabetically. Falls back to
    # the raw cell when there is no link.
    m = re.search(r"\[([^\]]*)\]", name_cell)
    label = m.group(1) if m else name_cell
    return (label.strip().lower(), name_cell.lower())


def parse_alignment(sep_cell: str) -> str:
    c = sep_cell.strip()
    left = c.startswith(":")
    right = c.endswith(":")
    if left and right:
        return "center"
    if right:
        return "right"
    if left:
        return "left"
    return ""


def parse_blocks(text: str) -> list[object]:
    lines = text.split("\n")
    blocks: list[object] = []
    i = 0
    n = len(lines)
    while i < n:
        if (
            TABLE_ROW_RE.match(lines[i])
            and i + 1 < n
            and TABLE_ROW_RE.match(lines[i + 1])
            and is_separator_row(lines[i + 1])
        ):
            header = split_row(lines[i])
            aligns = [parse_alignment(c) for c in split_row(lines[i + 1])]
            if len(aligns) < len(header):
                aligns += [""] * (len(header) - len(aligns))
            else:
                aligns = aligns[: len(header)]
            j = i + 2
            rows: list[list[str]] = []
            while j < n and TABLE_ROW_RE.match(lines[j]) and not is_separator_row(lines[j]):
                cells = split_row(lines[j])
                if len(cells) < len(header):
                    cells += [""] * (len(header) - len(cells))
                else:
                    cells = cells[: len(header)]
                rows.append(cells)
                j += 1
            blocks.append(Table(header=header, aligns=aligns, rows=rows))
            i = j
        else:
            if blocks and isinstance(blocks[-1], TextBlock):
                blocks[-1].lines.append(lines[i])
            else:
                blocks.append(TextBlock([lines[i]]))
            i += 1
    return blocks


def visual_len(s: str) -> int:
    return len(s)


def render_table(t: Table) -> str:
    ncol = len(t.header)
    widths = [visual_len(t.header[c]) for c in range(ncol)]
    for row in t.rows:
        for c in range(ncol):
            widths[c] = max(widths[c], visual_len(row[c]))
    for c in range(ncol):
        widths[c] = max(widths[c], 3)

    def fmt_cell(text: str, c: int) -> str:
        pad = widths[c] - visual_len(text)
        align = t.aligns[c]
        if align == "right":
            return " " * pad + text
        if align == "center":
            left = pad // 2
            return " " * left + text + " " * (pad - left)
        return text + " " * pad

    def fmt_sep(c: int) -> str:
        w = widths[c]
        align = t.aligns[c]
        if align == "center":
            return ":" + "-" * (w - 2) + ":"
        if align == "right":
            return "-" * (w - 1) + ":"
        if align == "left":
            return ":" + "-" * (w - 1)
        return "-" * w

    out = []
    out.append("| " + " | ".join(fmt_cell(t.header[c], c) for c in range(ncol)) + " |")
    out.append("| " + " | ".join(fmt_sep(c) for c in range(ncol)) + " |")
    for row in t.rows:
        out.append("| " + " | ".join(fmt_cell(row[c], c) for c in range(ncol)) + " |")
    return "\n".join(out)


def render_blocks(blocks: list[object]) -> str:
    parts = []
    for b in blocks:
        if isinstance(b, Table):
            parts.append(render_table(b))
        else:
            parts.append("\n".join(b.lines))
    return "\n".join(parts)


def sort_table_rows(t: Table) -> Table:
    # Sort rows alphabetically by name, but only for tables that actually have
    # named rows. Placeholder tables (empty Phase 2/3) are left untouched so we
    # don't disturb their blank rows.
    if not any(t.key_of(r) for r in t.rows):
        return t
    rows = sorted(t.rows, key=lambda r: sort_key(r[0]) if r else ("", ""))
    return Table(t.header, t.aligns, rows)


def do_format(text: str) -> str:
    blocks = parse_blocks(text)
    blocks = [sort_table_rows(b) if isinstance(b, Table) else b for b in blocks]
    result = render_blocks(blocks)
    if text.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result


def merge_cell(base: str, ours: str, theirs: str) -> tuple[str, bool]:
    nb, no, nt = normalize_cell(base), normalize_cell(ours), normalize_cell(theirs)
    if no == nt:
        return ours, False
    if no == nb:
        return theirs, False
    if nt == nb:
        return ours, False
    if nb == "":
        if no and nt:
            return f"{ours} <!-- CONFLICT: {theirs} -->", True
        return (ours or theirs), False
    return f"{ours} <!-- CONFLICT: {theirs} -->", True


def merge_tables(base: Table, ours: Table, theirs: Table) -> tuple[Table, bool]:
    header = ours.header if ours.header != base.header else theirs.header
    aligns = ours.aligns if ours.aligns != base.aligns else theirs.aligns
    ncol = len(header)

    def reshape(row: list[str]) -> list[str]:
        r = list(row)
        if len(r) < ncol:
            r += [""] * (ncol - len(r))
        return r[:ncol]

    conflict = False

    def keyed(t: Table) -> bool:
        return any(t.key_of(r) for r in t.rows)

    use_keys = keyed(base) or keyed(ours) or keyed(theirs)

    if not use_keys:
        maxlen = max(len(base.rows), len(ours.rows), len(theirs.rows))
        merged_rows = []
        for idx in range(maxlen):
            b = reshape(base.rows[idx]) if idx < len(base.rows) else [""] * ncol
            o = reshape(ours.rows[idx]) if idx < len(ours.rows) else [""] * ncol
            th = reshape(theirs.rows[idx]) if idx < len(theirs.rows) else [""] * ncol
            mrow = []
            for c in range(ncol):
                v, cf = merge_cell(b[c], o[c], th[c])
                conflict = conflict or cf
                mrow.append(v)
            merged_rows.append(mrow)
        return Table(header, aligns, merged_rows), conflict

    base_map = {base.key_of(r): reshape(r) for r in base.rows if base.key_of(r)}
    ours_map = {ours.key_of(r): reshape(r) for r in ours.rows if ours.key_of(r)}
    theirs_map = {theirs.key_of(r): reshape(r) for r in theirs.rows if theirs.key_of(r)}

    # Canonical row order is alphabetical by display name. The table is meant to
    # be alphabetical, and forcing a deterministic order means every branch and
    # main converge to the SAME ordering -- so the only real diff is cell content
    # and git can merge without conflicts regardless of when a branch forked.
    order = sorted(
        set(base_map) | set(ours_map) | set(theirs_map),
        key=sort_key,
    )

    merged_rows = []
    for k in order:
        b = base_map.get(k, [""] * ncol)
        o = ours_map.get(k, b)
        th = theirs_map.get(k, b)
        b = reshape(b); o = reshape(o); th = reshape(th)
        mrow = []
        for c in range(ncol):
            v, cf = merge_cell(b[c], o[c], th[c])
            conflict = conflict or cf
            mrow.append(v)
        merged_rows.append(mrow)

    return Table(header, aligns, merged_rows), conflict


def merge_text_blocks(base: TextBlock, ours: TextBlock, theirs: TextBlock) -> tuple[TextBlock, bool]:
    if ours.lines == theirs.lines:
        return ours, False
    if ours.lines == base.lines:
        return theirs, False
    if theirs.lines == base.lines:
        return ours, False
    return ours, True


def merge_documents(base_text: str, ours_text: str, theirs_text: str) -> tuple[str, bool]:
    b_blocks = parse_blocks(base_text)
    o_blocks = parse_blocks(ours_text)
    t_blocks = parse_blocks(theirs_text)

    conflict = False
    n = max(len(b_blocks), len(o_blocks), len(t_blocks))
    merged: list[object] = []

    def get(blocks, idx):
        return blocks[idx] if idx < len(blocks) else None

    for i in range(n):
        b, o, th = get(b_blocks, i), get(o_blocks, i), get(t_blocks, i)
        present = [x for x in (b, o, th) if x is not None]
        types = {type(x) for x in present}
        if len(types) != 1:
            chosen = o if o is not None else (th if th is not None else b)
            if chosen is not None:
                merged.append(chosen)
            conflict = True
            continue
        if isinstance(present[0], Table):
            bb = b or Table(o.header if o else th.header, o.aligns if o else th.aligns, [])
            oo = o or bb
            tt = th or bb
            mt, cf = merge_tables(bb, oo, tt)
            conflict = conflict or cf
            merged.append(mt)
        else:
            bb = b or TextBlock([])
            oo = o or bb
            tt = th or bb
            mtb, cf = merge_text_blocks(bb, oo, tt)
            conflict = conflict or cf
            merged.append(mtb)

    result = render_blocks(merged)
    if (ours_text.endswith("\n") or theirs_text.endswith("\n")) and not result.endswith("\n"):
        result += "\n"
    return result, conflict


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="format/merge dev-updates.md tables")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pf = sub.add_parser("format")
    pf.add_argument("file")
    pf.add_argument("--check", action="store_true")

    pm = sub.add_parser("merge")
    pm.add_argument("base")
    pm.add_argument("ours")
    pm.add_argument("theirs")
    pm.add_argument("--output")

    args = ap.parse_args(argv)

    if args.cmd == "format":
        original = read(args.file)
        formatted = do_format(original)
        if args.check:
            if original != formatted:
                sys.stderr.write(f"{args.file} not formatted\n")
                return 1
            return 0
        if original != formatted:
            write(args.file, formatted)
        return 0

    if args.cmd == "merge":
        raw_ours = read(args.ours)
        raw_theirs = read(args.theirs)
        for label, txt in (("ours", raw_ours), ("theirs", raw_theirs)):
            if re.search(r"^(<{7}|={7}|>{7})", txt, re.MULTILINE):
                sys.stderr.write(f"merge: {label} already contains git conflict markers\n")
                return 1
        base = do_format(read(args.base))
        ours = do_format(raw_ours)
        theirs = do_format(raw_theirs)
        merged, conflict = merge_documents(base, ours, theirs)
        out = args.output or args.ours
        write(out, merged)
        if conflict:
            sys.stderr.write("merge: unresolved conflict (see <!-- CONFLICT markers)\n")
            return 1
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
