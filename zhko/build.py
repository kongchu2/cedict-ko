"""Build the Yomitan dictionaries: CC-CEDICT-ko (terms) and Hanzi-ko (훈음 of characters)."""
import hashlib
import json
import zipfile
from datetime import datetime, timezone

from . import cedict
from .paths import DIST, HANZI, HANZI_NAME, HANZI_STORE, NAME, RELEASE_URL, REPO, TERMS_STORE
from .store import Store

BANK_SIZE = 10000
AUTHOR = "kongchu2"
REPO_URL = f"https://github.com/{REPO}"
TITLE = "CC-CEDICT-ko"
HANZI_TITLE = "Hanzi-ko"

STYLES = """\
[data-sc-zhko="tag"] {
  font-size: 0.75em; font-weight: bold; padding: 0.1em 0.35em; margin-right: 0.3em;
  border-radius: 0.3em; background-color: #8a5a00; color: #fff; vertical-align: text-bottom;
}
[data-sc-zhko="form"], [data-sc-zhko="cl"], [data-sc-zhko="note"] { font-size: 0.85em; opacity: 0.8; }
[data-sc-zhko="ref"] { opacity: 0.9; }
[data-sc-zhko="en"] { font-size: 0.85em; opacity: 0.75; margin-top: 0.3em; }
[data-sc-zhko="en"] ol { margin: 0; }
"""


def _revision():
    return datetime.now(timezone.utc).strftime("%Y.%m.%d.%H%M")


def _index(title, name, description, attribution, sequenced):
    return {
        "title": title,
        "revision": _revision(),
        "format": 3,
        "sequenced": sequenced,
        "author": AUTHOR,
        "url": REPO_URL,
        "description": description,
        "attribution": attribution,
        "sourceLanguage": "zh",
        "targetLanguage": "ko",
        "isUpdatable": True,
        "indexUrl": f"{RELEASE_URL}/{name}-index.json",
        "downloadUrl": f"{RELEASE_URL}/{name}.zip",
    }


def _write_zip(name, index, banks, extra=None):
    """banks: {"term_bank": rows, ...}; returns sha256 of the content (index excluded)."""
    DIST.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with zipfile.ZipFile(DIST / f"{name}.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("index.json", json.dumps(index, ensure_ascii=False, indent=1))
        for bank, rows in banks.items():
            for n in range(0, max(len(rows), 1), BANK_SIZE):
                body = json.dumps(rows[n : n + BANK_SIZE], ensure_ascii=False, separators=(",", ":"))
                z.writestr(f"{bank}_{n // BANK_SIZE + 1}.json", body)
                digest.update(body.encode())
        for fname, body in (extra or {}).items():
            z.writestr(fname, body)
            digest.update(body.encode())
    (DIST / f"{name}-index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1))
    return digest.hexdigest()


class Resolver:
    """Find the entry a CEDICT reference (traditional, simplified, pinyin) points to."""

    def __init__(self, entries):
        self.by_form = {}
        for e in entries:
            self.by_form.setdefault((e["t"], e["s"]), []).append(e)
            if e["t"] != e["s"]:
                self.by_form.setdefault((e["s"], e["s"]), []).append(e)

    def find(self, ref, ok):
        t, s, p = ref
        cands = [e for e in self.by_form.get((t, s), []) if ok(e)]
        if p:
            same = [e for e in cands if e["p"].lower() == p.lower()]
            cands = same or cands
        return cands[0] if cands else None


class Builder:
    def __init__(self, entries, store, include_untranslated=False):
        self.store = store
        self.tags = cedict.known_labels()
        self.include_untranslated = include_untranslated
        self.tr = {}
        for e in entries:
            rec = store.get(e["id"])
            if rec and rec["h"] == cedict.source_hash(e):
                self.tr[e["id"]] = rec
        self.resolver = Resolver(entries)

    def translated(self, e):
        return e["id"] in self.tr

    def first_gloss(self, e):
        rec = self.tr.get(e["id"])
        return rec["s"][0][0] if rec and rec["s"] and rec["s"][0] else None

    def _link(self, ref):
        t, s, p = ref
        target = self.resolver.find(ref, self.translated)
        out = [{"tag": "a", "href": f"?query={s}&wildcards=off", "content": s}]
        gloss = self.first_gloss(target) if target else None
        if gloss:
            out.append(f"({gloss})")
        return out

    def _links(self, refs):
        out = []
        for ref in refs:
            if out:
                out.append(", ")
            out += self._link(ref)
        return out

    def _tag(self, code):
        t = self.tags.get(code, {})
        return {"tag": "span", "data": {"zhko": "tag"}, "title": t.get("long", code), "content": t.get("short", code)}

    def _item(self, it, ko):
        if it["k"] == "sense":
            parts = [self._tag(t) for t in it["t"]]
            if ko is not None:
                parts.append({"tag": "span", "lang": "ko", "content": "; ".join(ko)})
            else:
                parts.append({"tag": "span", "lang": "en", "content": it["g"]})
            refs = cedict.refs_in(it["g"])
            if refs:
                parts.append({"tag": "span", "data": {"zhko": "ref"}, "content": [" → "] + self._links(refs)})
            return parts
        if it["k"] == "ref":
            before, _, after = cedict.REF_KINDS[it["kind"]].partition("{}")
            return [{"tag": "span", "data": {"zhko": "ref"}, "content": [before] + self._links(it["refs"]) + [after]}]
        if it["k"] == "pron":
            return [{"tag": "span", "data": {"zhko": "note"}, "content": f"{cedict.PRON_KO[it['kind']]}: {cedict.pinyin(it['p'])}"}]
        raise ValueError(it["k"])

    def render(self, e, other_form=None, other_label=""):
        rec = self.tr.get(e["id"])
        its = cedict.items(e)
        ko = iter(rec["s"]) if rec else None
        rows = []
        for it in its:
            if it["k"] == "cl":
                continue
            rows.append(self._item(it, next(ko) if ko is not None and it["k"] == "sense" else None))
        content = []
        if other_form:
            content.append({"tag": "div", "data": {"zhko": "form"}, "content": f"{other_label} {other_form}"})
        if len(rows) == 1:
            content.append({"tag": "div", "content": rows[0]})
        else:
            content.append({"tag": "ol", "content": [{"tag": "li", "content": r} for r in rows]})
        cls = [r for it in its if it["k"] == "cl" for r in it["refs"]]
        if cls:
            content.append({"tag": "div", "data": {"zhko": "cl"}, "content": ["양사: "] + self._cl_links(cls)})
        has_senses = any(it["k"] == "sense" for it in its)
        if has_senses and rec is None:
            content.append({"tag": "div", "data": {"zhko": "note"}, "content": "※ 아직 번역되지 않은 항목 (영어 원문)"})
        elif rec and rec["c"] == "low":
            content.append({"tag": "div", "data": {"zhko": "note"}, "content": "※ 자동 번역 신뢰도 낮음 — 영어 원문을 확인하세요"})
        if rec:
            en = [{"tag": "li", "content": g} for g in e["g"]]
            content.append({
                "tag": "details",
                "data": {"zhko": "en"},
                "content": [{"tag": "summary", "content": "영어 원문 (CC-CEDICT)"}, {"tag": "ol", "lang": "en", "content": en}],
            })
        return {"type": "structured-content", "content": content}

    def _cl_links(self, refs):
        out = []
        for t, s, p in refs:
            if out:
                out.append(", ")
            out.append({"tag": "a", "href": f"?query={s}&wildcards=off", "content": s})
            if p:
                out.append(f" {cedict.pinyin(p)}")
        return out

    def wanted(self, e):
        """Translated entries; reference-only entries whose target is in the dictionary."""
        if self.translated(e):
            return True
        its = cedict.items(e)
        if any(it["k"] == "sense" for it in its):
            return self.include_untranslated
        refs = [r for it in its if it["k"] == "ref" for r in it["refs"]]
        return any(self.resolver.find(r, self.translated) for r in refs)

    def order_key(self, e):
        rec = self.tr.get(e["id"])
        ref_only = not any(it["k"] == "sense" for it in cedict.items(e))
        return (ref_only, cedict.is_proper(e), -(rec or {}).get("f", 3))


def build_terms(include_untranslated=False):
    entries = cedict.load()
    store = Store(TERMS_STORE)
    b = Builder(entries, store, include_untranslated)
    chosen = [(i, e) for i, e in enumerate(entries) if b.wanted(e)]

    # Score orders the entries that share a written form (行 xíng before háng, 东西 dōngxi before dōngxī).
    by_form = {}
    for i, e in chosen:
        for form in {e["s"], e["t"]}:
            by_form.setdefault(form, []).append((b.order_key(e), i))
    score = {}
    for form, lst in by_form.items():
        for pos, (_, i) in enumerate(sorted(lst)):
            score[(form, i)] = -pos

    rows = []
    for i, e in chosen:
        reading = cedict.pinyin(e["p"])
        if e["s"] == e["t"]:
            rows.append([e["s"], reading, "", "", score[(e["s"], i)], [b.render(e)], i + 1, ""])
            continue
        rows.append([e["s"], reading, "", "", score[(e["s"], i)], [b.render(e, e["t"], "번체")], i + 1, ""])
        rows.append([e["t"], reading, "", "", score[(e["t"], i)], [b.render(e, e["s"], "간체")], i + 1, ""])
    # Yomitan merges rows whose readings differ only in case (能 néng / Néng) and shows the reading of the row
    # it meets first, so the best-scored row of each form goes first in the bank.
    rows.sort(key=lambda r: -r[4])
    index = _index(
        TITLE,
        NAME,
        f"CC-CEDICT 기반 중한사전. 한국어 뜻은 LLM 번역 (CC-CEDICT {cedict.version()}).",
        "CC-CEDICT © MDBG and contributors, CC BY-SA 4.0 (https://cc-cedict.org/). "
        "Korean translations derived from CC-CEDICT, CC BY-SA 4.0.",
        sequenced=True,
    )
    tag_rows = []
    digest = _write_zip(NAME, index, {"term_bank": rows, "tag_bank": tag_rows}, {"styles.css": STYLES})
    print(f"{NAME}: {len(chosen)} entries ({len(b.tr)} translated), {len(rows)} rows")
    return digest


def build_hanzi():
    if not HANZI.exists():
        print(f"{HANZI_NAME}: skipped (no {HANZI.name}; run `fetch --unihan`)")
        return None
    with open(HANZI, encoding="utf-8") as f:
        chars = [json.loads(line) for line in f if line.strip()]
    store = Store(HANZI_STORE, key="c")
    rows = []
    for c in chars:
        rec = store.get(c["c"])
        hunum = rec["hunum"] if rec else []
        if not (hunum or c.get("ko")):
            continue
        stats = {"ko": ", ".join(c.get("ko", [])) or "-", "strokes": str(c["strokes"])}
        if c.get("trad"):
            stats["trad"] = "".join(c["trad"])
        if c.get("simp"):
            stats["simp"] = "".join(c["simp"])
        if c.get("tgh"):
            stats["tgh"] = str(c["tgh"])
        tag = "통용" if c.get("tgh") else ""
        rows.append([c["c"], " ".join(c.get("py", [])), " ".join(c.get("ko", [])), tag, hunum or c["ko"], stats])
    tag_rows = [
        ["통용", "frequent", 0, "통용규범한자표(通用规范汉字表, 2013) 수록자", 0],
        ["ko", "misc", 0, "한국 한자음", 0],
        ["strokes", "misc", 1, "획수", 0],
        ["trad", "misc", 2, "번체자", 0],
        ["simp", "misc", 3, "간체자", 0],
        ["tgh", "misc", 4, "통용규범한자표 번호 (1–3500 1급, 3501–6500 2급, 6501– 3급)", 0],
    ]
    index = _index(
        HANZI_TITLE,
        HANZI_NAME,
        "Unihan 기반 한자 사전. 통용규범한자표와 그 번체자의 한국 한자 훈음 수록.",
        "Unicode Han Database (Unihan) © Unicode, Inc., Unicode License v3. "
        "Korean 훈음 by LLM, CC BY-SA 4.0.",
        sequenced=False,
    )
    digest = _write_zip(HANZI_NAME, index, {"kanji_bank": rows, "tag_bank": tag_rows})
    print(f"{HANZI_NAME}: {len(rows)} hanzi, {sum(1 for r in rows if store.get(r[0]))} with 훈음")
    return digest


def main(args):
    digests = {NAME: build_terms(args.include_untranslated), HANZI_NAME: build_hanzi()}
    (DIST / "content.sha256").write_text("".join(f"{v}  {k}\n" for k, v in digests.items() if v))
