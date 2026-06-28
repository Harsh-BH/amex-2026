"""Build the Unstop submission .xlsx from scores_v1.csv + the framework writeup.

Fills the OFFICIAL template (docs/...submission_template.xlsx) in place into a new file:
  - `Predictions`            : ID + Prediction for all 500K (joined by ID, never reordered)
  - `Profitability Framework`: Section + Response, parsed from .claude/templates/framework-doc.md

Every hard constraint in checklists/before-submission.md is asserted here; the file is written
ONLY if all guards pass (a bad file wastes 1 of 10 submissions).

Run:  .venv/bin/python src/build_submission.py
"""
from __future__ import annotations
import csv
import re
from pathlib import Path
import openpyxl
from openpyxl.styles import Alignment, Font

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = next((ROOT / "docs").glob("*submission*template*.xlsx"))
SCORES = ROOT / "data" / "scores_v1.csv"
WRITEUP = ROOT / ".claude" / "templates" / "framework-doc.md"
OUT = ROOT / "submissions" / "submission_v1_baseline.xlsx"
N_ROWS = 500_000


def parse_writeup(md: str) -> dict[str, str]:
    """Split the writeup markdown into {section heading -> body text}. Strips HTML comments and
    the leading '## '. Bodies are returned verbatim (already plain-text-friendly for Excel cells)."""
    md = re.sub(r"<!--.*?-->", "", md, flags=re.DOTALL)
    out: dict[str, str] = {}
    heading, buf = None, []
    for line in md.splitlines():
        if line.startswith("## "):
            if heading is not None:
                out[heading] = "\n".join(buf).strip()
            heading, buf = line[3:].strip(), []
        elif heading is not None:
            buf.append(line)
    if heading is not None:
        out[heading] = "\n".join(buf).strip()
    return out


def load_scores() -> dict[int, float]:
    with SCORES.open() as f:
        r = csv.reader(f)
        header = next(r)
        assert header == ["id", "score"], f"unexpected scores header: {header}"
        return {int(i): float(s) for i, s in r}


def build():
    sections = parse_writeup(WRITEUP.read_text())
    scores = load_scores()
    assert len(scores) == N_ROWS, f"scores has {len(scores):,} rows, expected {N_ROWS:,}"
    assert set(scores) == set(range(N_ROWS)), "scores ids are not exactly 0..499,999"
    assert all(v is not None for v in scores.values()), "null score present"

    wb = openpyxl.load_workbook(TEMPLATE)

    # --- Predictions: fill by matching the template's own ID cells (never assume row order) ---
    pred = wb["Predictions"]
    assert [pred.cell(1, c).value for c in (1, 2)] == ["ID", "Prediction"], "Predictions header drift"
    seen = set()
    for row in range(2, N_ROWS + 2):
        rid = pred.cell(row, 1).value
        rid = int(rid)
        assert rid in scores, f"template id {rid} missing from scores"
        assert rid not in seen, f"duplicate id {rid} in template"
        seen.add(rid)
        pred.cell(row, 2).value = scores[rid]
    assert len(seen) == N_ROWS, f"filled {len(seen):,} ids, expected {N_ROWS:,}"
    assert pred.max_row == N_ROWS + 1, f"Predictions has {pred.max_row} rows (added/removed rows?)"

    # --- Profitability Framework: fill Response keyed by the template's exact Section text ---
    fw = wb["Profitability Framework"]
    assert [fw.cell(1, c).value for c in (1, 2)] == ["Section", "Response"], "Framework header drift"
    missing = []
    for row in range(2, fw.max_row + 1):
        sec = fw.cell(row, 1).value
        if sec is None:
            continue
        if sec not in sections:
            missing.append(sec)
            continue
        cell = fw.cell(row, 2)
        cell.value = sections[sec]
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    assert not missing, f"writeup is missing template sections: {missing}"
    fw.column_dimensions["A"].width = 28
    fw.column_dimensions["B"].width = 110
    for row in range(2, fw.max_row + 1):
        fw.cell(row, 1).font = Font(bold=True)

    OUT.parent.mkdir(exist_ok=True)
    wb.save(OUT)
    vals = list(scores.values())
    print(f"OK wrote {OUT.relative_to(ROOT)}")
    print(f"  Predictions: {len(seen):,} ids (0..{N_ROWS-1}), no nulls/dupes")
    print(f"  Framework:   {sum(1 for r in range(2, fw.max_row+1) if fw.cell(r,1).value)} sections filled")
    print(f"  score range: [{min(vals):.4f}, {max(vals):.4f}]  distinct={len(set(vals)):,} (degenerate check)")


def _self_check():
    p = parse_writeup("# T\n<!-- x -->\n## A\nbody a\nline2\n## B\nbody b\n")
    assert p == {"A": "body a\nline2", "B": "body b"}, p
    print("OK build_submission.py self-checks pass")


if __name__ == "__main__":
    _self_check()
    build()
