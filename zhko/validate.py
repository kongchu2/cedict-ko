"""Validate built dictionaries against Yomitan's JSON schemas, plus a few lookup smoke checks."""
import json
import re
import sys
import zipfile

from jsonschema.validators import validator_for

from .paths import DIST, SCHEMAS

BANK_SCHEMAS = {
    "term_bank": "dictionary-term-bank-v3-schema.json",
    "tag_bank": "dictionary-tag-bank-v3-schema.json",
    "kanji_bank": "dictionary-kanji-bank-v3-schema.json",
}
# Both scripts must be searchable, with tone-marked pinyin readings.
SMOKE_READINGS = {"学习": "xué xí", "學習": "xué xí", "中国": "Zhōng guó"}


def _validator(name):
    schema = json.loads((SCHEMAS / name).read_text())
    return validator_for(schema)(schema)


def validate_zip(path):
    errors = 0
    with zipfile.ZipFile(path) as z:
        for name in sorted(z.namelist()):
            if name == "index.json":
                v = _validator("dictionary-index-schema.json")
            else:
                m = re.match(r"(\w+_bank)_\d+\.json$", name)
                if not m:
                    continue
                v = _validator(BANK_SCHEMAS[m.group(1)])
            for err in v.iter_errors(json.loads(z.read(name))):
                errors += 1
                if errors <= 20:
                    print(f"  {name}: {'/'.join(map(str, err.absolute_path))}: {err.message[:200]}")
        rows = [r for n in z.namelist() if n.startswith("term_bank_") for r in json.loads(z.read(n))]
    if rows:
        readings = {}
        for r in rows:
            readings.setdefault(r[0], set()).add(r[1])
        for term, reading in SMOKE_READINGS.items():
            if term in readings and reading not in readings[term]:
                errors += 1
                print(f"  smoke: {term} has readings {sorted(readings[term])}, expected {reading}")
    print(f"{path.name}: {'OK' if not errors else f'{errors} errors'}")
    return errors


def main(args):
    zips = sorted(DIST.glob("*.zip"))
    if not zips:
        sys.exit("nothing in dist/ — run `python -m zhko build` first")
    if sum(validate_zip(z) for z in zips):
        sys.exit(1)
