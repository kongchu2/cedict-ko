from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
SCHEMAS = ROOT / "data" / "schemas"
SOURCE = ROOT / "source"
TRANSLATIONS = ROOT / "translations"
DIST = ROOT / "dist"
REVIEW = ROOT / "review"

# Pinned snapshot of CC-CEDICT, refreshed only by `fetch --cedict` (a visible git diff).
CEDICT = SOURCE / "cedict_ts.u8"
# Selected hanzi with their Unihan fields, written by `fetch --unihan`.
HANZI = SOURCE / "hanzi.jsonl"
UNIHAN = RAW / "Unihan.zip"

TERMS_STORE = TRANSLATIONS / "terms.jsonl"
HANZI_STORE = TRANSLATIONS / "hanzi.jsonl"
TAGS_FILE = TRANSLATIONS / "tags.json"

NAME = "cedict-ko"
HANZI_NAME = "hanzi-ko"
REPO = "kongchu2/" + NAME
RELEASE_URL = f"https://github.com/{REPO}/releases/latest/download"
