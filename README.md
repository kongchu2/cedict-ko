# CC-CEDICT-ko — Yomitan용 중한사전

> Yomitan이 처음이라면 [설치 안내](https://kongchu2.github.io/yomitan-ko/)부터 보세요.
> 자매 사전: [일본어 → 한국어 (JMdict-ko)](https://github.com/kongchu2/jmdict-ko) · [영어 → 한국어 (Wiktionary-en-ko)](https://github.com/kongchu2/wiktionary-en-ko)
> 틀린 뜻을 발견하면 [오역 제보](../../issues/new?template=mistranslation.yml)로 알려 주세요.

[Yomitan](https://github.com/yomidevs/yomitan)에서 쓰는 **중국어→한국어** 사전입니다.
[CC-CEDICT](https://cc-cedict.org/)의 표제어(간체·번체), 병음, 뜻 구분을 그대로 쓰고, 각 뜻을 LLM으로 한국어로 번역합니다.
한자의 훈음을 보여 주는 한자 사전(Hanzi-ko)도 함께 배포합니다.

> Claude Haiku가 번역했습니다. 말뭉치([wordfreq](https://github.com/rspeer/wordfreq))에 나오는 83,729개 항목 가운데 83,719개가 들어 있습니다(CC-CEDICT 전체의 71%). 말뭉치에 나오지 않는 나머지 약 3만 4천 항목(드문 고유명사, 생물 종 이름 등)은 아직 번역하지 않았습니다. 한자 훈음 10,353자는 Claude Sonnet이 붙였습니다.

## 왜 만들었나

공개된 중한 Yomitan 사전은 한국어 위키낱말사전에서 뽑은 `wty-zh-ko`뿐인데, 표제어가 16,307개라 빈도 상위 1,000단어의 92%, 10,000단어의 59%, 50,000단어의 20%만 들어 있습니다(学习, 东西, 我们, 电脑 없음). 상용 중한사전은 재배포할 수 없으므로, 자유 라이선스(CC BY-SA 4.0)인 CC-CEDICT의 영어 뜻을 한국어로 옮겼습니다.

## 수록 내용

- **표제어**: CC-CEDICT 전체 125,413개 항목 중 번역된 항목. 번역은 [wordfreq](https://github.com/rspeer/wordfreq) 중국어 빈도순으로 진행합니다.
- **간체·번체**: 둘 다 검색됩니다(`学习`, `學習`). 간체로 찾으면 번체를, 번체로 찾으면 간체를 함께 보여 줍니다.
- **병음**: 성조 부호로 표시합니다(`xué xí`). 대문자로 시작하면 고유명사입니다(`Běi jīng`).
- **같은 글자의 여러 독음**: 번역할 때 모델이 독음별로 현대 중국어에서 얼마나 흔한지(1~5)를 함께 매기고, 그 순서로 보여 줍니다(`东西` dōngxi "물건"이 dōngxī "동서"보다 먼저, `行` xíng이 háng보다 먼저). 고유명사와 참조만 있는 항목은 뒤로 갑니다.
- **용법 표시**: CEDICT의 `(literary)`, `(coll.)`, `(Tw)`, `(bound form)`, `(idiom)` 같은 표시는 문어·구어·대만·결합형·성어 태그로 바꿨습니다(`translations/tags.json`, 손으로 고칠 수 있음).
- **참조 항목**: "variant of", "see", "used in", "abbr. for"만 있는 항목(7,944개)은 번역하지 않고 `罗锅(곱사등이)의 얼화형`처럼 대상 단어로 연결합니다.
- **양사·대만 발음**: `양사: 篇 piān, 份 fèn`, `대만 발음: zhú`.
- **영어 원문**: 항목마다 CC-CEDICT 원문을 접어 두었습니다.

### 한자 사전 (Hanzi-ko)

[통용규범한자표](https://zh.wikipedia.org/wiki/通用规范汉字表)(2013)의 8,105자와 그 번체자, 모두 10,894자입니다. 한국 한자 훈음(`學` 배울 학, `们` 들 문. 간체자는 번체자의 훈음), 한국 한자음과 병음([Unihan](https://www.unicode.org/charts/unihan.html)), 획수, 간체·번체 대응을 보여 줍니다. 단어 사전에서 표제어의 글자를 누르면 나옵니다.

## 설치

1. [Releases](../../releases/latest)에서 `cedict-ko.zip`과 `hanzi-ko.zip`을 받습니다.
2. Yomitan → 설정 → 일반(General)에서 언어(Language)를 Chinese로 바꿉니다. 일본어와 함께 쓰려면 중국어용 프로필을 따로 만드세요.
3. Yomitan → 설정 → 사전(Dictionaries) → 가져오기(Import)에서 두 zip을 불러옵니다.

## 번역 품질

- 한국어 뜻은 LLM(Claude Haiku) 자동 번역이라 오역이 있습니다. 영어 원문을 확인용으로 쓰세요.
- 모델을 고르려고 155개 항목을 Haiku와 Sonnet으로 각각 번역해, 어느 쪽인지 가린 채 Claude가 채점했습니다. 뜻 372개 중 문제가 있다고 본 것은 Haiku 8개(2.2%, 오역 1), Sonnet 19개(5.1%, 오역 3)였습니다. 두 모델 모두 爱人(배우자), 新闻(뉴스), 工作(일), 馒头(찐빵) 같은 한자어 거짓 짝은 맞게 옮겼고, 틀린 것은 대개 없는 한자어를 지어낸 경우였습니다(合弓纲 → 합궁강, 맞는 말은 단궁강). 모델이 모델을 채점했으므로 실제 오류율은 더 높을 수 있습니다.
- 모델이 확신하지 못한 항목에는 `※ 자동 번역 신뢰도 낮음` 표시가 붙습니다.
- 오역 수정은 `translations/terms.jsonl`에서 해당 항목 줄의 `s`(뜻별 한국어 목록)를 고치면 됩니다. 훈음은 `translations/hanzi.jsonl`의 `hunum`입니다.

## 직접 빌드하기

Python 3.9 이상, 그리고 번역할 때는 [Claude Code](https://claude.com/claude-code) CLI(`claude`)가 필요합니다.

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

.venv/bin/python -m zhko fetch                          # Yomitan 스키마 다운로드
.venv/bin/python -m zhko translate terms --top 50000    # 빈도 상위 5만 항목 중 미번역 항목 번역 (재실행하면 이어서)
.venv/bin/python -m zhko translate hanzi --model sonnet # 한자 훈음
.venv/bin/python -m zhko build                          # dist/cedict-ko.zip, dist/hanzi-ko.zip
.venv/bin/python -m zhko validate                       # Yomitan 스키마 검증
.venv/bin/python -m zhko review -n 200                  # review/sample.md 에 검수용 샘플
.venv/bin/python -m zhko status                         # 진행 상황
node tools/lookup.mjs 学习 "了解情况"                     # Yomitan의 조회 코드로 zip을 찾아보기
node tools/lookup.mjs --text article.txt                # 글을 앞에서부터 읽으며 안 나오는 글자 모으기
```

- `tools/lookup.mjs`는 [Yomitan](https://github.com/yomidevs/yomitan) 소스를 `data/yomitan`에 받아 두어야 돌아갑니다(`git clone --depth 1`, npm 설치는 필요 없음).
- 원본은 `source/cedict_ts.u8`에 고정해 두었습니다. CC-CEDICT는 매일 바뀌므로, 빌드할 때마다 최신판을 받으면 고쳐진 항목이 번역 전까지 빠집니다. 최신판으로 바꾸려면 `fetch --cedict`(git diff로 바뀐 줄이 보임) 후 `translate terms`를 다시 돌립니다. 뜻이 바뀐 항목만 다시 번역됩니다.
- `build --include-untranslated`를 붙이면 미번역 항목도 영어 뜻으로 포함합니다.
- GitHub Actions(`.github/workflows/release.yml`)가 `translations/`, `source/`, `zhko/`가 바뀔 때 다시 빌드하고, 내용이 바뀐 경우에만 릴리스를 만듭니다. 번역은 로컬에서 돌리고 `translations/`를 커밋하세요.

## 라이선스

- 코드(`zhko/`, `tools/`, `.github/`): [MIT](LICENSE).
- 사전 데이터(`source/cedict_ts.u8`, `translations/`, 빌드된 zip): [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). CC-CEDICT(MDBG 및 기여자)의 파생물입니다.
- `source/hanzi.jsonl`과 한자 사전의 독음·획수·자형 정보: [Unihan](https://www.unicode.org/charts/unihan.html), [Unicode License V3](LICENSE).
- 번역 순서를 정할 때 쓰는 빈도 데이터: [wordfreq](https://github.com/rspeer/wordfreq) (CC BY-SA 4.0). 빌드 결과물에는 포함되지 않습니다.

## English

CC-CEDICT-ko is a Chinese→Korean dictionary for [Yomitan](https://github.com/yomidevs/yomitan). It keeps the headwords (simplified and traditional), pinyin and sense divisions of [CC-CEDICT](https://cc-cedict.org/) and gives each sense in Korean. The Korean glosses are machine-translated with an LLM (Claude): the original English is kept in a collapsed section of every entry, and entries the model was unsure about are marked. It covers the 83,719 entries that occur in the wordfreq corpus (71% of CC-CEDICT). `hanzi-ko.zip` is a character dictionary with Korean 훈음 (meaning and Sino-Korean reading). Download both from [Releases](../../releases/latest), set Yomitan's language to Chinese and import them in Settings → Dictionaries. Data: CC BY-SA 4.0 (Unihan fields: Unicode License V3); code: MIT.
