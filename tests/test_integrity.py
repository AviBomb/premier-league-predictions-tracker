"""Self-check for src/integrity.py. Run: python tests/test_integrity.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.integrity import detect_integrity_flags  # noqa: E402

PICKS = {f"m{i}": {"pred": f"{i % 3}-1"} for i in range(8)}


def rec(author, cid, fixtures=None, text="", status="Valid"):
    return {"author": author, "comment_id": cid, "fixtures": fixtures or {}, "raw_text": text, "status": status}


def kinds(flags):
    return sorted(f["type"] for f in flags)


# Three accounts, same 8 scorelines -> one identical_picks flag; two accounts is not enough.
flags = detect_integrity_flags([rec("@a", "1", PICKS), rec("@b", "2", PICKS), rec("@c", "3", PICKS)])
assert kinds(flags) == ["identical_picks"], flags
assert flags[0]["authors"] == ["@a", "@b", "@c"]
assert detect_integrity_flags([rec("@a", "1", PICKS), rec("@b", "2", PICKS)]) == []

# Fewer than 6 scored matches never counts as an identical set.
few = {k: v for k, v in list(PICKS.items())[:5]}
assert detect_integrity_flags([rec(a, a, few) for a in ("@a", "@b", "@c")]) == []

# Copied text across accounts (whitespace/case-insensitive); short text ignored.
long_text = "Arsenal 2-1 Chelsea, Liverpool 3-0 Everton, Spurs 1-1 Villa and the rest"
flags = detect_integrity_flags([rec("@a", "1", text=long_text), rec("@b", "2", text=long_text.upper().replace(" ", "  "))])
assert kinds(flags) == ["copied_text"], flags
assert detect_integrity_flags([rec("@a", "1", text="2-1"), rec("@b", "2", text="2-1")]) == []

# Same account posting two prediction comments -> repeat_submissions; admin entries are ignored.
other = {k: {"pred": "0-0"} for k in PICKS}
flags = detect_integrity_flags([rec("@a", "1", PICKS), rec("@a", "2", other)])
assert kinds(flags) == ["repeat_submissions"], flags
assert detect_integrity_flags([rec("@a", "1", PICKS), rec("@a", "2", other, status="Valid (Admin entry)")]) == []

print("integrity checks passed")
