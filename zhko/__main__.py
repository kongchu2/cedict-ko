import argparse

from . import build, fetch, review, status, translate, validate


def main():
    p = argparse.ArgumentParser(prog="python -m zhko", description="CC-CEDICT → Korean Yomitan dictionary builder")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="download Yomitan schemas (and optionally refresh sources)")
    f.add_argument("--cedict", action="store_true", help="replace source/cedict_ts.u8 with the latest CC-CEDICT")
    f.add_argument("--unihan", action="store_true", help="download Unihan and rewrite source/hanzi.jsonl")
    f.set_defaults(run=fetch.main)

    t = sub.add_parser("translate", help="translate with the claude CLI (resumable)")
    t.add_argument("what", choices=["terms", "hanzi"])
    t.add_argument("--model", default="haiku")
    t.add_argument("--limit", type=int, default=0, help="max items this run (0 = all)")
    t.add_argument("--top", type=int, default=0, help="only the first N entries in rank order (0 = all)")
    t.add_argument("--batch", type=int, default=25, help="entries per LLM call")
    t.add_argument("--workers", type=int, default=4)
    t.add_argument("--ids", help="file with one entry id per line: translate only these")
    t.add_argument("--store", help="alternative store file (e.g. to compare models)")
    t.add_argument("--redo-empty", action="store_true", help="hanzi: retry characters stored with no 훈음")
    t.set_defaults(run=translate.main)

    b = sub.add_parser("build", help="build dist/*.zip")
    b.add_argument("--include-untranslated", action="store_true", help="include entries with English glosses only")
    b.set_defaults(run=build.main)

    sub.add_parser("validate", help="validate dist/*.zip against Yomitan schemas").set_defaults(run=validate.main)

    sub.add_parser("status", help="translation progress").set_defaults(run=status.main)

    r = sub.add_parser("review", help="write a translation sample for manual review")
    r.add_argument("-n", type=int, default=200)
    r.add_argument("--low", action="store_true", help="only low-confidence entries")
    r.add_argument("--seed", type=int, default=0)
    r.add_argument("--top", type=int, default=0, help="sample only from the first N entries in rank order")
    r.add_argument("--store", help="store to review instead of translations/terms.jsonl")
    r.add_argument("--against", help="second store to show side by side")
    r.set_defaults(run=review.main)

    args = p.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
