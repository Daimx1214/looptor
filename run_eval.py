#!/usr/bin/env python3
"""Run a model over LoopBench sets via the local Ollama API.

Usage: python3 run_eval.py --model qwen3:1.7b --sets stress --limit 10 \
           --out results/base --temp 0.6 --max-tokens 1536
Writes <out>/<set>.jsonl with the full generated text (thinking + answer),
token count and done_reason for every prompt. Resumable: ids already in the
output file are skipped.
"""
import argparse, json, os, sys, time
import urllib.request

API = "http://127.0.0.1:11434/api/chat"


def generate(model, prompt, temp, top_p, max_tokens):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": True,
        "options": {"temperature": temp, "top_p": top_p, "num_predict": max_tokens},
    }
    req = urllib.request.Request(API, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3600) as r:
        resp = json.loads(r.read())
    msg = resp.get("message", {})
    thinking = msg.get("thinking", "") or ""
    content = msg.get("content", "") or ""
    return {
        "thinking": thinking,
        "content": content,
        "full_text": (thinking + "\n" + content).strip(),
        "tokens": resp.get("eval_count", 0),
        "done_reason": resp.get("done_reason", ""),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--sets", default="test,stress")
    ap.add_argument("--limit", type=int, default=0, help="per set, 0 = all")
    ap.add_argument("--out", required=True)
    ap.add_argument("--temp", type=float, default=0.6)
    ap.add_argument("--top-p", type=float, default=0.95)
    ap.add_argument("--max-tokens", type=int, default=2048)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    bench = os.path.join(os.path.dirname(os.path.abspath(__file__)), "loopbench")
    for s in args.sets.split(","):
        items = [json.loads(l) for l in open(os.path.join(bench, f"{s}.jsonl"))]
        if args.limit:
            items = items[:args.limit]
        path = os.path.join(args.out, f"{s}.jsonl")
        done = set()
        if os.path.exists(path):
            done = {json.loads(l)["id"] for l in open(path)}
        with open(path, "a") as f:
            for it in items:
                if it["id"] in done:
                    continue
                t0 = time.time()
                try:
                    gen = generate(args.model, it["prompt"], args.temp, args.top_p, args.max_tokens)
                except Exception as e:
                    print(f"{it['id']}: ERROR {e}", flush=True)
                    continue
                rec = {**it, **gen, "model": args.model, "temp": args.temp,
                       "max_tokens": args.max_tokens, "secs": round(time.time() - t0, 1)}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                print(f"{it['id']}: {gen['tokens']} tok, {rec['secs']}s, done={gen['done_reason']}", flush=True)


if __name__ == "__main__":
    main()
