#!/usr/bin/env python3
"""LoopTor loop detector — spec frozen 25 Nov 2026 (Master Guide Appendix A).

An output is a LOOP if any of:
  (a) some 8-gram (8 consecutive words) occurs 3+ times, or
  (b) some sentence of 10+ words occurs 3+ times, or
  (c) non-termination: generation hit the token cap with no EOS / final answer
      (reported separately AND counted in loop rate).

Code blocks are masked before detection so legitimate code repetition
(e.g. loop bodies) does not trigger a false loop.
"""
import re
from collections import Counter

WORD_RE = re.compile(r"[a-z0-9']+")
CODE_RE = re.compile(r"```.*?```", re.S)
SENT_SPLIT_RE = re.compile(r"[.?!]\s+|\n+")


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def mask_code(text: str) -> str:
    return CODE_RE.sub(" CODEBLOCK ", text)


def words_of(text: str) -> list:
    return WORD_RE.findall(normalize(mask_code(text)))


def ngram_repeats(words: list, n: int = 8, min_count: int = 3) -> Counter:
    grams = Counter(tuple(words[i:i + n]) for i in range(len(words) - n + 1))
    return Counter({g: c for g, c in grams.items() if c >= min_count})


def sentence_repeats(text: str, min_words: int = 10, min_count: int = 3) -> Counter:
    body = mask_code(normalize(text))
    sents = [s.strip() for s in SENT_SPLIT_RE.split(body) if s.strip()]
    long_sents = [s for s in sents if len(WORD_RE.findall(s)) >= min_words]
    counts = Counter(long_sents)
    return Counter({s: c for s, c in counts.items() if c >= min_count})


def detect(text: str, hit_token_cap: bool = False, has_final_answer: bool = True) -> dict:
    """Return loop verdict + evidence for one model output."""
    words = words_of(text)
    ng = ngram_repeats(words)
    sr = sentence_repeats(text)
    nonterm = bool(hit_token_cap and not has_final_answer)
    is_loop = bool(ng) or bool(sr) or nonterm
    return {
        "loop": is_loop,
        "non_termination": nonterm,
        "ngram_hits": {(" ".join(g)): c for g, c in list(ng.items())[:5]},
        "sentence_hits": {s[:80]: c for s, c in list(sr.items())[:5]},
        "n_words": len(words),
    }


if __name__ == "__main__":
    import sys, json
    hit_cap = "--hit-cap" in sys.argv
    text = sys.stdin.read()
    print(json.dumps(detect(text, hit_token_cap=hit_cap), indent=2, ensure_ascii=False))
