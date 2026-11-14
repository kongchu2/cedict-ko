"""Download the Yomitan schemas; with flags, refresh the pinned CC-CEDICT snapshot and the hanzi list."""
import gzip
import json
import re
import urllib.request
import zipfile

from .paths import CEDICT, HANZI, RAW, SCHEMAS, UNIHAN

CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
UNIHAN_URL = "https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip"
SCHEMA_BASE = "https://raw.githubusercontent.com/yomidevs/yomitan/master/ext/data/schemas"
SCHEMA_FILES = [
    "dictionary-index-schema.json",
    "dictionary-term-bank-v3-schema.json",
    "dictionary-tag-bank-v3-schema.json",
    "dictionary-kanji-bank-v3-schema.json",
]
UNIHAN_FIELDS = {
    "kTGH", "kHangul", "kMandarin", "kDefinition", "kTraditionalVariant", "kSimplifiedVariant", "kTotalStrokes",
}


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "cedict-ko-builder"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def fetch_schemas():
    SCHEMAS.mkdir(parents=True, exist_ok=True)
    for name in SCHEMA_FILES:
        (SCHEMAS / name).write_bytes(_get(f"{SCHEMA_BASE}/{name}"))


def fetch_cedict():
    body = gzip.decompress(_get(CEDICT_URL))
    CEDICT.parent.mkdir(parents=True, exist_ok=True)
    CEDICT.write_bytes(body)
    date = re.search(rb"^#! date=(\S+)", body, re.M)
    print(f"CC-CEDICT {date.group(1).decode() if date else '?'} → {CEDICT}")


def _codepoints(value):
    return [chr(int(m, 16)) for m in re.findall(r"U\+([0-9A-F]+)", value)]


def unihan():
    """{char: {field: value}} for the fields we use."""
    out = {}
    with zipfile.ZipFile(UNIHAN) as z:
        for name in z.namelist():
            for line in z.read(name).decode("utf-8").splitlines():
                if not line.startswith("U+"):
                    continue
                cp, field, value = line.split("\t", 2)
                if field in UNIHAN_FIELDS:
                    out.setdefault(chr(int(cp[2:], 16)), {})[field] = value
    return out


def select_hanzi(data):
    """The 通用规范汉字表 (8,105 characters) and their traditional forms, most frequent first."""
    from wordfreq import get_frequency_dict

    freq = get_frequency_dict("zh", "large")
    wanted = {c for c, d in data.items() if "kTGH" in d}
    simp_of = {}
    for c in sorted(wanted):
        for t in _codepoints(data[c].get("kTraditionalVariant", "")):
            if t != c:
                simp_of.setdefault(t, c)
    chars = wanted | set(simp_of)
    rows = []
    for c in chars:
        d = data.get(c, {})
        trad = [t for t in _codepoints(d.get("kTraditionalVariant", "")) if t != c]
        simp = [s for s in _codepoints(d.get("kSimplifiedVariant", "")) if s != c]
        row = {
            "c": c,
            "py": d.get("kMandarin", "").split(),
            "ko": [h.split(":")[0] for h in d.get("kHangul", "").split()],
            "en": d.get("kDefinition", ""),
            "strokes": int(d.get("kTotalStrokes", "0").split()[0] or 0),
        }
        if trad:
            row["trad"] = trad
        if simp:
            row["simp"] = simp
        if "kTGH" in d:
            row["tgh"] = int(d["kTGH"].split()[0].split(":")[1])
        row["_f"] = freq.get(c, 0.0) or freq.get(simp_of.get(c, ""), 0.0) * 0.5
        rows.append(row)
    rows.sort(key=lambda r: (-r["_f"], r.get("tgh", 99999), r["c"]))
    with open(HANZI, "w", encoding="utf-8") as f:
        for r in rows:
            r.pop("_f")
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(rows)} hanzi ({len(wanted)} in 通用规范汉字表) → {HANZI}")


def fetch_unihan():
    RAW.mkdir(parents=True, exist_ok=True)
    UNIHAN.write_bytes(_get(UNIHAN_URL))
    select_hanzi(unihan())


def main(args):
    fetch_schemas()
    if args.cedict:
        fetch_cedict()
    if args.unihan:
        fetch_unihan()
