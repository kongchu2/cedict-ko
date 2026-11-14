"""CC-CEDICT helpers: parsing, pinyin, cross-references, labels, ranking, prompt text.

An entry is one line `Traditional Simplified [pin1 yin1] /gloss/gloss/`. Its slash-separated
glosses become items of four kinds:
- "sense": translated by the LLM (with leading labels such as "(literary)" split off as tags),
- "ref":   a pure cross-reference ("variant of X", "see X", "used in X"), rendered without the LLM,
- "pron":  "Taiwan pr. [x]" / "also pr. [x]",
- "cl":    measure words ("CL:個|个[ge4]").
"""
import hashlib
import json
import re
import unicodedata

from .paths import CEDICT, TAGS_FILE

LINE = re.compile(r"^(\S+) (\S+) \[([^\]]*)\] /(.*)/\s*$")

_CJK = "〇㐀-鿿豈-﫿\U00020000-\U0003ffff"
_WORD = rf"[0-9A-Za-z·]*[{_CJK}][{_CJK}0-9A-Za-z·]*"
_REF = rf"{_WORD}(?:\|{_WORD})?(?:\[[^\]]+\])?"
REF_RE = re.compile(rf"({_WORD})(?:\|({_WORD}))?(?:\[([^\]]+)\])?")

# How a pure cross-reference reads in Korean; {} is the referenced word(s).
REF_KINDS = {
    "variant of": "{}의 이체자",
    "old variant of": "{}의 옛 이체자",
    "archaic variant of": "{}의 옛 이체자",
    "unofficial variant of": "{}의 비공식 이체자",
    "erhua variant of": "{}의 얼화형",
    "Japanese variant of": "{}의 일본식 자형",
    "see": "{} 참조",
    "see also": "{}도 참조",
    "used in": "{}에 쓰임",
    "also written": "다른 표기: {}",
    "abbr. for": "{}의 약칭",
}
_KIND_ALT = "|".join(re.escape(k) for k in sorted(REF_KINDS, key=len, reverse=True))
PURE_REF = re.compile(rf"^({_KIND_ALT}) ((?:{_REF})(?:(?:, | or | and |, or |, and |/)(?:{_REF}))*)\s*$")
PRON = re.compile(r"^(Taiwan pr\.|also pr\.) \[([^\]]+)\]$")
PRON_KO = {"Taiwan pr.": "대만 발음", "also pr.": "다른 발음"}
LABEL = re.compile(r"^\(([^()]*)\)\s*")

TONE_MARKS = {"1": "̄", "2": "́", "3": "̌", "4": "̀"}
SYLLABLE = re.compile(r"^([A-Za-z:]+)([1-5])$")


def load():
    """All entries in file order."""
    out = []
    with open(CEDICT, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            m = LINE.match(line)
            if not m:
                continue
            t, s, p, g = m.groups()
            out.append({"id": f"{t} {s} [{p}]", "t": t, "s": s, "p": p, "g": [x for x in g.split("/") if x.strip()]})
    return out


def version():
    with open(CEDICT, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#! date="):
                return line.split("=", 1)[1].strip()[:10]
            if not line.startswith("#"):
                break
    return "unknown"


def tone_syllable(syl):
    m = SYLLABLE.match(syl)
    if not m:
        return syl
    base, tone = m.group(1).replace("u:", "ü").replace("U:", "Ü"), m.group(2)
    if tone not in TONE_MARKS:
        return base
    low = base.lower()
    if "a" in low:
        i = low.index("a")
    elif "e" in low:
        i = low.index("e")
    elif "ou" in low:
        i = low.index("o")
    else:
        vowels = [k for k, c in enumerate(low) if c in "iouü"]
        nasals = [k for k, c in enumerate(low) if c in "mn"]
        if vowels:
            i = vowels[-1]
        elif nasals:
            i = nasals[0]  # m2, ng2, hm, hng
        else:
            return base
    return unicodedata.normalize("NFC", base[: i + 1] + TONE_MARKS[tone] + base[i + 1 :])


def pinyin(p):
    """'xue2 xi2' -> 'xué xí'; non-syllable tokens (digits, letters, ·) are kept."""
    return " ".join(tone_syllable(t) for t in p.split())


def refs_in(text):
    """[(traditional, simplified, pinyin or None)] for every CEDICT-style reference in the text."""
    return [(m.group(1), m.group(2) or m.group(1), m.group(3)) for m in REF_RE.finditer(text)]


def _tags():
    return json.loads(TAGS_FILE.read_text()) if TAGS_FILE.exists() else {}


_TAG_CACHE = {}


def known_labels():
    if "tags" not in _TAG_CACHE:
        _TAG_CACHE["tags"] = _tags()
    return _TAG_CACHE["tags"]


def items(entry):
    """Classify the glosses of an entry (see module docstring), in their original order."""
    labels = known_labels()
    out = []
    for g in entry["g"]:
        g = g.strip()
        if g.startswith("CL:"):
            out.append({"k": "cl", "refs": refs_in(g[3:])})
            continue
        m = PRON.match(g)
        if m:
            out.append({"k": "pron", "kind": m.group(1), "p": m.group(2)})
            continue
        m = PURE_REF.match(g)
        if m:
            out.append({"k": "ref", "kind": m.group(1), "refs": refs_in(m.group(2)), "en": g})
            continue
        tags, text = [], g
        while True:
            lm = LABEL.match(text)
            if not lm or lm.group(1) not in labels or not text[lm.end():].strip():
                break
            tags.append(lm.group(1))
            text = text[lm.end():]
        out.append({"k": "sense", "t": tags, "g": text, "en": g})
    return out


def senses(entry):
    return [it for it in items(entry) if it["k"] == "sense"]


def source_hash(entry):
    """Fingerprint of everything the translation depends on; a change means re-translate."""
    payload = [entry["t"], entry["s"], entry["p"], [[s["t"], s["g"]] for s in senses(entry)]]
    return hashlib.sha1(json.dumps(payload, ensure_ascii=False).encode()).hexdigest()[:12]


def is_proper(entry):
    return entry["p"][:1].isupper()


def rank(entries):
    """Translation order: corpus frequency of the simplified form (wordfreq), common nouns before names."""
    from wordfreq import get_frequency_dict

    freq = get_frequency_dict("zh", "large")
    order = {e["id"]: i for i, e in enumerate(entries)}
    return sorted(entries, key=lambda e: (-freq.get(e["s"], 0.0), is_proper(e), len(e["s"]), order[e["id"]]))


def headline(entry):
    head = entry["s"] if entry["t"] == entry["s"] else f"{entry['s']} / {entry['t']}"
    return f"{head} [{pinyin(entry['p'])}]"


def entry_prompt(entry, n):
    lines = [f"#{n} {headline(entry)}"]
    for k, s in enumerate(senses(entry), 1):
        tags = "".join(f"[{t}] " for t in s["t"])
        lines.append(f"{k}. {tags}{s['g']}")
    return "\n".join(lines)
