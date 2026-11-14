"""Dump a sample of translations (optionally side by side with another store) for manual review."""
import random
from pathlib import Path

from . import cedict
from .paths import REVIEW, TERMS_STORE
from .store import Store
from .translate import translatable


def main(args):
    entries = translatable(cedict.load())
    if args.top:
        entries = entries[: args.top]
    store = Store(Path(args.store) if args.store else TERMS_STORE)
    other = Store(Path(args.against)) if args.against else None
    pool = [e for e in entries if store.get(e["id"]) and (store.get(e["id"])["c"] == "low" or not args.low)]
    if other:
        pool = [e for e in pool if other.get(e["id"])]
    random.Random(args.seed).shuffle(pool)
    out = []
    for e in pool[: args.n]:
        r = store.get(e["id"])
        out.append(f"### {cedict.headline(e)} conf={r['c']} freq={r.get('f')}")
        for n, s in enumerate(cedict.senses(e)):
            tags = "".join(f"[{t}] " for t in s["t"])
            line = f"{n + 1}. {tags}{s['g']}\n   → {'; '.join(r['s'][n])}"
            if other:
                o = other.get(e["id"])
                line += f"\n   ⇢ {'; '.join(o['s'][n])}  ({o['m']}, conf={o['c']}, freq={o.get('f')})"
            out.append(line)
        out.append("")
    REVIEW.mkdir(exist_ok=True)
    path = REVIEW / ("low.md" if args.low else "sample.md")
    path.write_text("\n".join(out))
    print(f"{min(len(pool), args.n)} entries → {path}")
