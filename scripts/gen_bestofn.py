#!/usr/bin/env python3
"""Best-of-N sampling from the base model over the train pool (Guide Ch. 10.1).

For each train prompt: N samples at temp 0.8 via the Ollama API.
Writes ALL samples to data/bestofn_raw.jsonl (resumable by prompt id + sample idx).
Selection (shortest correct loop-free) happens in build_dataset.py.
On Colab the same logic runs on transformers inside the notebook instead.
"""
import argparse, json, os, sys
import urllib.request

API = "http://127.0.0.1:11434/api/chat"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate(model, prompt, temp, max_tokens):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "stream": False, "think": True,
            "options": {"temperature": temp, "top_p": 0.95, "num_predict": max_tokens}}
    req = urllib.request.Request(API, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3600) as r:
        resp = json.loads(r.read())
    msg = resp.get("message", {})
    return {"thinking": msg.get("thinking", "") or "", "content": msg.get("content", "") or "",
            "tokens": resp.get("eval_count", 0), "done_reason": resp.get("done_reason", "")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3-base")
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "bestofn_raw.jsonl"))
    args = ap.parse_args()

    prompts = [json.loads(l) for l in open(os.path.join(ROOT, "loopbench", "train_pool.jsonl"))]
    if args.limit:
        prompts = prompts[:args.limit]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    done = set()
    if os.path.exists(args.out):
        for l in open(args.out):
            r = json.loads(l)
            done.add((r["id"], r["sample"]))
    with open(args.out, "a") as f:
        for it in prompts:
            for s in range(args.n):
                if (it["id"], s) in done:
                    continue
                try:
                    g = generate(args.model, it["prompt"], args.temp, args.max_tokens)
                except Exception as e:
                    print(f"{it['id']}#{s}: ERROR {e}", flush=True)
                    continue
                rec = {"id": it["id"], "sample": s, "category": it["category"],
                       "prompt": it["prompt"], "gold": it["gold"], "check": it["check"], **g}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
            print(f"{it['id']}: done", flush=True)


if __name__ == "__main__":
    main()
