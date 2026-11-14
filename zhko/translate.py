"""Translate CC-CEDICT senses and hanzi 훈음 into Korean with an LLM."""
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import cedict
from .llm import ClaudeCLI, RateLimited
from .paths import HANZI, HANZI_STORE, TERMS_STORE
from .store import Store

CJK_SCRIPT = re.compile("[\u3040-\u30ff\u3100-\u312f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0003ffff]")  # kana, bopomofo, hanzi
ENGLISH_WORD = re.compile(r"[a-z]{4,}")  # leaves room for DNA, km, pH, mRNA
PINYIN_LETTER = re.compile("[\u00c0-\u024f]")  # tone-marked or accented Latin letters
HUNUM = re.compile(r"^[가-힣](?:[가-힣 ,·()]*[가-힣)])? [가-힣]$")  # "배울 학", "나라 국"

TERMS_SYSTEM = """You are a professional Chinese–Korean lexicographer writing the Korean side of a Chinese→Korean learner's dictionary (중한사전) built on CC-CEDICT.

Each entry has a number (#n), the simplified headword (and the traditional form after " / " when it differs), its pinyin in brackets, and numbered senses. Capitalized pinyin marks a proper noun. The senses are CC-CEDICT's English glosses. Tags in square brackets ([literary], [coll.], [Tw], [bound form], [idiom], [math.] …) are shown separately by the dictionary. References such as 學習|学习[xue2 xi2] point to other words.

For every sense, write the Korean equivalents a Korean speaker would expect in a 중한사전.

Rules:
1. Translate the meaning of the Chinese word in that sense. The English gloss only tells you which sense is meant: do not translate the English mechanically, and do not translate an explanatory gloss word for word when Korean has a real equivalent.
2. Return exactly as many senses as given, in the same order. Never merge, split, skip or reorder senses, even when two senses end up with the same Korean.
3. Give 1–4 short glosses per sense, most natural first. Prefer real equivalent words. Use a short explanatory phrase only when Korean has no equivalent.
4. Sino-Korean words: use the Korean word with the same hanja only when Korean really uses it in this meaning (经济 → 경제, 学习 → 배우다, 공부하다, 학습하다). Watch for false friends: 爱人 → 배우자, 남편, 아내 (not 애인); 新闻 → 뉴스 (not 신문); 汽车 → 자동차 (not 기차); 走 → 걷다, 가다 (not 달리다); 东西 dōngxi → 물건; 工作 → 일, 일하다 (not 공작); 馒头 → 찐빵 (not 만두); 告诉 → 알리다 (not 고소); 便宜 piányi → 싸다. Never invent a Sino-Korean reading that is not a real Korean word.
5. Match the part of speech of the gloss. "to …" → a verb in dictionary form ending in -다 (吃 → 먹다). Adjectives and stative verbs → predicate form (漂亮 → 예쁘다, 高 → 높다, 키가 크다). Nouns as nouns, adverbs as adverbs. Measure words ("classifier for …") → the Korean counter with ~ (本 classifier for books → ~권) or a short description of what it counts. Particles and grammatical words: the Korean pattern with ~ when there is one (的 possessive → ~의), otherwise a short description of the function in parentheses ((completed action marker) → (동작의 완료를 나타냄)). Never prefix glosses with grammar labels such as (명사), (동사), (조사).
6. Do not repeat the tags. Keep register: slang, vulgar, coll. → equally informal Korean; literary → written Korean. Idioms (成语): the Korean 사자성어 only when Korea really uses the same one (一石二鸟 → 일석이조), otherwise the meaning as a short Korean phrase.
7. Proper nouns, following 외래어 표기법: Chinese people and places of modern times by Mandarin pronunciation (北京 → 베이징, 四川 → 쓰촨, 习近平 → 시진핑); those of before 1911 by the Korean hanja reading (孔子 → 공자, 长安 → 장안, 诸葛亮 → 제갈량). Korean and Japanese names as Koreans write them (首尔 → 서울, 东京 → 도쿄). Other foreign names: the standard Korean name (华盛顿 → 워싱턴). Surnames: "surname Wang" → 왕 (성씨). For lesser-known names add what it is in parentheses (宜宾 → 이빈 (쓰촨성의 도시)).
8. Loanwords: when Korean normally uses the loanword, standard 외래어 표기법 spelling (沙发 → 소파, 咖啡 → 커피).
9. Technical and other domain terms: the established Korean term (勾股定理 → 피타고라스 정리, 合弓纲 → 단궁강). Never coin a term by reading the characters in Korean: if you do not know the established term, describe it in plain Korean and set conf to low. Species: the Korean common name if one exists; otherwise a descriptive name (… 의 일종).
10. Write only Korean (Hangul, with punctuation and ~ allowed): no Chinese characters, no pinyin, no English. Latin letters only where Korean itself writes them (DNA, CD, km).
11. conf: "low" only when you are unsure of the core meaning of some sense (obscure, rare or ambiguous word). Many senses, nuance or register differences alone are not reasons for "low"; otherwise "high".
12. freq: how common the word is in modern Mandarin with this pronunciation and these senses, 1–5: 5 everyday, 4 common, 3 occasional, 2 rare, 1 very rare, archaic or obscure. The same characters with another pronunciation are a different entry and are rated on their own (东西 dōngxi "thing" → 5, 东西 dōngxī "east and west" → 3)."""

TERMS_SCHEMA = {
    "type": "object",
    "properties": {
        "entries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "n": {"type": "integer"},
                    "senses": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
                    "conf": {"type": "string", "enum": ["high", "low"]},
                    "freq": {"type": "integer", "minimum": 1, "maximum": 5},
                },
                "required": ["n", "senses", "conf", "freq"],
            },
        }
    },
    "required": ["entries"],
}

HANZI_SYSTEM = """You write the Korean 훈음 (meaning + Sino-Korean reading) of Chinese characters, exactly as Korean hanja dictionaries (옥편) do.
Each input line gives a character, its traditional form(s) if it is a simplified character, its Korean reading(s) from Unihan if known, its Mandarin reading(s) and English meanings.
Rules:
- Use the traditional 훈음 of the character, written as "훈 음" (學 → 배울 학, 國 → 나라 국, 東 → 동녘 동).
- A simplified character takes the 훈음 of its traditional form (学 → 배울 학, 们 → 들 문). When one simplified character stands for several traditional ones, give the 훈음 of each, most common first (发 → "필 발" for 發, "터럭 발" for 髮).
- A character with several readings gets one item per reading, most common first (樂 → "즐길 락", "노래 악", "좋아할 요").
- Write the reading in its dictionary form, not the initial-sound-rule form: 즐길 락, not 즐길 낙.
- Most characters have a 훈음 in Korean 옥편 even when no Korean reading is given here (你 → 너 니, 嗎 and 吗 → 꾸짖을 마, 跑 → 달릴 포, 躺 → 누울 당). Give it whenever you know it.
- Return an empty list only for characters that Korean 옥편 do not list and for which you know no Korean reading (many modern dialect or onomatopoeic characters).
- Output Hangul only."""

HANZI_SCHEMA = {
    "type": "object",
    "properties": {
        "hanzi": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"c": {"type": "string"}, "hunum": {"type": "array", "items": {"type": "string"}}},
                "required": ["c", "hunum"],
            },
        }
    },
    "required": ["hanzi"],
}


def _chunk(items, max_items, weight=lambda x: 1, max_weight=None):
    batch, w = [], 0
    for it in items:
        iw = weight(it)
        if batch and (len(batch) >= max_items or (max_weight and w + iw > max_weight)):
            yield batch
            batch, w = [], 0
        batch.append(it)
        w += iw
    if batch:
        yield batch


def _run(batches, worker, workers):
    """Run worker(batch) -> (ok_count, failed_items) in parallel; stop cleanly on rate limits."""
    stop = threading.Event()
    failed, done, total, t0 = [], 0, len(batches), time.time()

    def guarded(b):
        if stop.is_set():
            return 0, []
        try:
            return worker(b)
        except RateLimited as e:
            stop.set()
            print(f"\n!! rate/usage limit reached, stopping: {e}", file=sys.stderr)
            return 0, []
        except Exception as e:  # keep going; the batch stays untranslated and is retried next run
            print(f"\n!! batch failed: {e}", file=sys.stderr)
            return 0, []

    ok = 0
    with ThreadPoolExecutor(workers) as pool:
        for fut in as_completed([pool.submit(guarded, b) for b in batches]):
            n, f = fut.result()
            ok += n
            failed += f
            done += 1
            print(f"[{done}/{total}] ok={ok} failed={len(failed)} {time.time() - t0:.0f}s", flush=True)
    return ok, failed, stop.is_set()


def valid_gloss(g):
    return bool(g.strip()) and not CJK_SCRIPT.search(g) and not ENGLISH_WORD.search(g) and not PINYIN_LETTER.search(g)


def _valid_senses(senses, expected):
    return len(senses) == expected and all(s and all(valid_gloss(g) for g in s) for s in senses)


def translatable(entries):
    """Entries with at least one sense to translate, in rank order."""
    return [e for e in cedict.rank(entries) if cedict.senses(e)]


def translate_terms(args):
    store = Store(Path(args.store) if args.store else TERMS_STORE)
    llm = ClaudeCLI(args.model)
    entries = translatable(cedict.load())
    if args.top:
        entries = entries[: args.top]
    if args.ids:
        wanted = set(Path(args.ids).read_text(encoding="utf-8").splitlines())
        entries = [e for e in entries if e["id"] in wanted]
    todo = [e for e in entries if (store.get(e["id"]) or {}).get("h") != cedict.source_hash(e)]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(todo)} entries to translate with {args.model}")

    def worker(batch):
        by_n = dict(enumerate(batch, 1))
        prompt = "\n\n".join(cedict.entry_prompt(e, n) for n, e in by_n.items())
        out = llm.call(TERMS_SYSTEM, prompt, TERMS_SCHEMA)
        recs = []
        for item in out.get("entries", []):
            e = by_n.get(item.get("n"))
            if e is None:
                continue
            senses = [[g.strip() for g in s if g.strip()] for s in item["senses"]]
            if not _valid_senses(senses, len(cedict.senses(e))):
                continue
            del by_n[item["n"]]
            recs.append({
                "id": e["id"], "h": cedict.source_hash(e), "s": senses,
                "c": item["conf"], "f": item["freq"], "m": args.model,
            })
        store.add_many(recs)
        return len(recs), list(by_n.values())

    weight = lambda e: len(cedict.senses(e))  # noqa: E731
    batches = list(_chunk(todo, args.batch, weight=weight, max_weight=args.batch * 3))
    ok, failed, stopped = _run(batches, worker, args.workers)
    if failed and not stopped:
        print(f"retrying {len(failed)} entries in small batches")
        ok2, failed, stopped = _run(list(_chunk(failed, 3)), worker, args.workers)
        ok += ok2
    store.compact()
    print(f"translated {ok}, still failing {len(failed)}: {' / '.join(e['id'] for e in failed[:50])}")
    if stopped:
        sys.exit(75)  # EX_TEMPFAIL: usage limit, run again after it resets


def load_hanzi():
    with open(HANZI, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def translate_hanzi(args):
    chars = load_hanzi()
    store = Store(HANZI_STORE, key="c")
    llm = ClaudeCLI(args.model)
    todo = [c for c in chars if store.get(c["c"]) is None
            or (args.redo_empty and not store.get(c["c"])["hunum"])]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(todo)} hanzi to translate")

    def worker(batch):
        by_c = {c["c"]: c for c in batch}
        prompt = "\n".join(
            f"{c['c']} | traditional: {','.join(c.get('trad', [])) or '-'} | ko: {','.join(c.get('ko', [])) or '-'}"
            f" | mandarin: {','.join(c.get('py', []))} | en: {c.get('en', '')[:120]}"
            for c in batch
        )
        recs = []
        for item in llm.call(HANZI_SYSTEM, prompt, HANZI_SCHEMA)["hanzi"]:
            c = by_c.pop(item["c"], None)
            if c is None:
                continue
            hunum = [h.strip() for h in item["hunum"] if HUNUM.match(h.strip())]
            recs.append({"c": c["c"], "hunum": hunum, "m": args.model})
        store.add_many(recs)
        return len(recs), list(by_c.values())

    ok, failed, stopped = _run(list(_chunk(todo, args.batch)), worker, args.workers)
    store.compact(sort_key=lambda r: r["c"])
    print(f"translated {ok}, failed {len(failed)}")
    if stopped:
        sys.exit(75)


def main(args):
    {"terms": translate_terms, "hanzi": translate_hanzi}[args.what](args)
