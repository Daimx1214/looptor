#!/usr/bin/env python3
"""Score eval outputs: loop rate, non-termination, tokens, accuracy.

Usage: python3 score_loops.py results/base [--save results/score_base.json]
Accuracy: for checkable items, gold must appear in the final-answer content
(word-boundary match for numbers, substring for names/days).
Bootstrap 95% CI on loop rate (1,000 resamples, seed fixed).
"""
import argparse, json, os, re, sys
import random as pyrandom
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "loopbench"))
from loop_detect import detect


def gold_hit(gold, content):
    if gold is None:
        return None
    text = content.lower()
    if re.fullmatch(r"\d+", gold):
        return bool(re.search(rf"(?<![\d,]){int(gold):,}(?!\d)|(?<!\d){gold}(?!\d)", text))
    return gold.lower() in text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("indir")
    ap.add_argument("--save", default="")
    args = ap.parse_args()

    summary = {}
    for fn in sorted(os.listdir(args.indir)):
        if not fn.endswith(".jsonl"):
            continue
        rows = [json.loads(l) for l in open(os.path.join(args.indir, fn))]
        if not rows:
            continue
        loops, nonterms, toks, hits, checked = 0, 0, [], 0, 0
        per_cat = {}
        for r in rows:
            hit_cap = r.get("done_reason") == "length"
            has_final = bool(r.get("content", "").strip())
            d = detect(r.get("full_text", ""), hit_token_cap=hit_cap, has_final_answer=has_final)
            loops += d["loop"]; nonterms += d["non_termination"]
            toks.append(r.get("tokens", 0))
            h = gold_hit(r.get("gold"), r.get("content", ""))
            if h is not None:
                checked += 1; hits += h
            c = per_cat.setdefault(r.get("category", "?"), [0, 0])
            c[0] += d["loop"]; c[1] += 1
        n = len(rows)
        toks_sorted = sorted(toks)
        rng = pyrandom.Random(42)
        flags = []
        for r in rows:
            d = detect(r.get("full_text", ""), hit_token_cap=r.get("done_reason") == "length",
                       has_final_answer=bool(r.get("content", "").strip()))
            flags.append(1 if d["loop"] else 0)
        boots = []
        for _ in range(1000):
            sample = [flags[rng.randrange(n)] for _ in range(n)]
            boots.append(sum(sample) / n)
        boots.sort()
        summary[fn[:-6]] = {
            "n": n,
            "loop_rate": round(loops / n, 4),
            "loop_ci95": [round(boots[25], 4), round(boots[975], 4)],
            "nonterm_rate": round(nonterms / n, 4),
            "median_tokens": toks_sorted[n // 2],
            "mean_tokens": round(sum(toks) / n, 1),
            "accuracy": (round(hits / checked, 4) if checked else None),
            "accuracy_n": checked,
            "loop_by_category": {k: f"{a}/{b}" for k, (a, b) in sorted(per_cat.items())},
        }
    print(json.dumps(summary, indent=2))
    if args.save:
        with open(args.save, "w") as f:
            json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
