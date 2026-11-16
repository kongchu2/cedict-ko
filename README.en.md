# CC-CEDICT-ko: a Chinese→Korean dictionary for Yomitan

> Sister dictionaries: [Japanese → Korean (JMdict-ko)](https://github.com/kongchu2/jmdict-ko) · [English → Korean (Wiktionary-en-ko)](https://github.com/kongchu2/wiktionary-en-ko). Korean install guide: https://kongchu2.github.io/yomitan-ko/
> Found a wrong gloss? [Report a mistranslation](../../issues/new?template=mistranslation.yml).

[한국어](README.md) · English

A **Chinese→Korean** dictionary for [Yomitan](https://github.com/yomidevs/yomitan).
It keeps the headwords (simplified and traditional), pinyin and sense divisions of [CC-CEDICT](https://cc-cedict.org/) and translates each sense into Korean with an LLM.
A character dictionary with Korean 훈음 (Hanzi-ko) is released alongside it.

> Translated by Claude Haiku. It has 83,719 of the 83,729 entries that occur in the [wordfreq](https://github.com/rspeer/wordfreq) corpus (71% of CC-CEDICT). The other 34,000 or so entries, which do not occur in the corpus (rare proper nouns, species names and the like), are not translated yet. The 훈음 of 10,353 characters were written by Claude Sonnet.

## Why

The only public Chinese→Korean dictionary for Yomitan was `wty-zh-ko`, extracted from the Korean Wiktionary. With 16,307 headwords it has 92% of the 1,000 most frequent words, 59% of the top 10,000 and 20% of the top 50,000 (no 学习, 东西, 我们 or 电脑). Commercial Chinese→Korean dictionaries cannot be redistributed, so this project translates the English glosses of CC-CEDICT, which is freely licensed (CC BY-SA 4.0), into Korean.

## What is in it

- **Headwords**: the translated entries out of CC-CEDICT's 125,413. Translation went in [wordfreq](https://github.com/rspeer/wordfreq) Chinese frequency order.
- **Simplified and traditional**: both are searchable (`学习`, `學習`). A simplified lookup also shows the traditional form, and the other way round.
- **Pinyin**: shown with tone marks (`xué xí`). A capital initial marks a proper noun (`Běi jīng`).
- **Several readings of one form**: while translating, the model also rates how common each reading is in modern Chinese (1 to 5), and entries are shown in that order (`东西` dōngxi "thing" before dōngxī "east and west", `行` xíng before háng). Proper nouns and reference-only entries come last.
- **Usage labels**: CEDICT's `(literary)`, `(coll.)`, `(Tw)`, `(bound form)`, `(idiom)` and similar labels become Korean tags (`translations/tags.json`, editable by hand).
- **Reference entries**: the 7,944 entries that only say "variant of", "see", "used in" or "abbr. for" are not translated. They link to the target word, as in `罗锅(곱사등이)의 얼화형` (erhua form of 罗锅 "hunchback").
- **Classifiers and Taiwan pronunciation**: `양사: 篇 piān, 份 fèn`, `대만 발음: zhú`.
- **Repeated glosses**: CC-CEDICT lists near-synonyms as separate glosses (`luxurious/sumptuous/lavish`), so the Korean translations overlap. Each Korean gloss is shown once.
- **Sense order**: it follows CC-CEDICT, so for some words a common sense comes after a rarer one (`让` shows "to yield" before "to let, to make").
- **English original**: every entry keeps the CC-CEDICT text in a collapsed section.

### Character dictionary (Hanzi-ko)

The 8,105 characters of the [Table of General Standard Chinese Characters](https://en.wikipedia.org/wiki/Table_of_General_Standard_Chinese_Characters) (2013) and their traditional forms, 10,894 in all. It shows the Korean 훈음 (`學` 배울 학, `们` 들 문; a simplified character gets the 훈음 of its traditional form), the Sino-Korean reading and pinyin (from [Unihan](https://www.unicode.org/charts/unihan.html)), the stroke count and the simplified/traditional counterpart. It opens when you click a character of a headword in the term dictionary.

## Install

1. Download `cedict-ko.zip` and `hanzi-ko.zip` from [Releases](../../releases/latest).
2. In Yomitan, go to Settings → General and set Language to Chinese. To use it next to Japanese, make a separate profile for Chinese.
3. Go to Settings → Dictionaries → Import and choose the two zips.

## Translation quality

- The Korean glosses are machine-translated with an LLM (Claude Haiku) and some are wrong. Use the English original to check.
- To choose the model, 155 entries were translated by both Haiku and Sonnet and graded by Claude without knowing which was which. Of 372 senses, it flagged 8 from Haiku (2.2%, 1 wrong) and 19 from Sonnet (5.1%, 3 wrong). Both models handled false friends between Chinese and Sino-Korean words correctly: 爱人 (spouse), 新闻 (news), 工作 (work), 馒头 (steamed bun). Most errors were Sino-Korean words that do not exist (合弓纲 → 합궁강; the real term is 단궁강). A model graded a model here, so the true error rate may be higher.
- Entries the model was unsure about carry the note `※ 자동 번역 신뢰도 낮음` (low-confidence machine translation).
- To fix a gloss, edit `s` (the list of Korean glosses per sense) on that entry's line in `translations/terms.jsonl`. 훈음 are in `hunum` in `translations/hanzi.jsonl`.

## Building it yourself

You need Python 3.9 or later, and the [Claude Code](https://claude.com/claude-code) CLI (`claude`) to translate.

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

.venv/bin/python -m zhko fetch                          # download the Yomitan schemas
.venv/bin/python -m zhko translate terms --top 50000    # translate what is untranslated in the top 50,000 (re-run to continue)
.venv/bin/python -m zhko translate hanzi --model sonnet # 훈음 of the characters
.venv/bin/python -m zhko build                          # dist/cedict-ko.zip, dist/hanzi-ko.zip
.venv/bin/python -m zhko validate                       # check against the Yomitan schemas
.venv/bin/python -m zhko review -n 200                  # write a review sample to review/sample.md
.venv/bin/python -m zhko status                         # progress
node tools/lookup.mjs 学习 "了解情况"                     # look words up in the zip with Yomitan's own lookup code
node tools/lookup.mjs --text article.txt                # read a text from the start and collect characters that are not found
```

- `tools/lookup.mjs` needs the [Yomitan](https://github.com/yomidevs/yomitan) source in `data/yomitan` (`git clone --depth 1`; no npm install needed).
- The source is pinned in `source/cedict_ts.u8`. CC-CEDICT changes daily, so building from the latest file every time would drop each corrected entry until it is translated again. To move to the latest file, run `fetch --cedict` (the changed lines show up in git diff) and then `translate terms`. Only entries whose senses changed are translated again.
- `build --include-untranslated` also includes untranslated entries, with their English glosses.
- GitHub Actions (`.github/workflows/release.yml`) rebuilds when `translations/`, `source/` or `zhko/` change and makes a release only when the content changed. Translation runs locally: commit `translations/` afterwards.

## License

- Code (`zhko/`, `tools/`, `.github/`): [MIT](LICENSE).
- Dictionary data (`source/cedict_ts.u8`, `translations/`, the built zips): [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). It is derived from CC-CEDICT (MDBG and contributors).
- `source/hanzi.jsonl` and the readings, stroke counts and character forms in the character dictionary: [Unihan](https://www.unicode.org/charts/unihan.html), [Unicode License V3](LICENSE).
- Frequency data used to order the translation work: [wordfreq](https://github.com/rspeer/wordfreq) (CC BY-SA 4.0). It is not included in the built dictionaries.
