"""Print translation progress (in rank order) and hanzi coverage."""
from . import cedict
from .paths import HANZI, HANZI_STORE, TERMS_STORE
from .store import Store
from .translate import load_hanzi, translatable


def _pct(n, d):
    return f"{n:,} / {d:,} ({n / d:.1%})" if d else "0 / 0"


def main(args):
    entries = translatable(cedict.load())
    store = Store(TERMS_STORE)
    fresh = [e["id"] for e in entries if (store.get(e["id"]) or {}).get("h") == cedict.source_hash(e)]
    done = set(fresh)
    for n in (10000, 30000, 50000, 80000):
        print(f"top {n:,}: {_pct(sum(e['id'] in done for e in entries[:n]), min(n, len(entries)))}")
    print(f"all (entries with senses): {_pct(len(done), len(entries))}")
    print(f"stale (CC-CEDICT changed, will re-translate): {len(store.records) - len(done):,}")
    print(f"low confidence: {sum(1 for i in fresh if store.get(i)['c'] == 'low'):,}")
    if HANZI.exists():
        chars = load_hanzi()
        hs = Store(HANZI_STORE, key="c")
        print(f"hanzi 훈음: {_pct(sum(1 for c in chars if hs.get(c['c'])), len(chars))}")
