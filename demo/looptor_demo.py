#!/usr/bin/env python3
"""LoopTor CLI demo: same prompt, base vs tuned, side by side in the terminal.
Usage: python3 demo/looptor_demo.py "your prompt here"
Models: qwen3-base (original Qwen3-1.7B) and looptor (fine-tuned), via Ollama.
"""
import json, os, sys, time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "loopbench"))
from loop_detect import detect

API = "http://127.0.0.1:11434/api/chat"


def run(model, prompt, max_tokens=2048):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "stream": False, "think": True,
            "options": {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "num_predict": max_tokens}}
    req = urllib.request.Request(API, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=3600) as r:
        resp = json.loads(r.read())
    secs = time.time() - t0
    msg = resp.get("message", {})
    full = ((msg.get("thinking", "") or "") + "\n" + (msg.get("content", "") or "")).strip()
    d = detect(full, hit_token_cap=resp.get("done_reason") == "length",
               has_final_answer=bool((msg.get("content") or "").strip()))
    return full, resp.get("eval_count", 0), secs, d


def show(label, model, prompt):
    print(f"\n{'='*70}\n{label} ({model})\n{'='*70}")
    try:
        full, toks, secs, d = run(model, prompt)
    except Exception as e:
        print(f"[model not available: {e}]")
        return
    print(full[:3000] + ("..." if len(full) > 3000 else ""))
    print(f"\n--- tokens: {toks} | time: {secs:.1f}s | LOOP DETECTED: {'YES' if d['loop'] else 'no'}"
          f" | non-termination: {d['non_termination']}")


if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:]) or (
        "A train travels 240 km in 3 hours, then 180 km in 2 hours. What is its "
        "average speed for the whole journey? Think step by step and verify your answer.")
    show("BASE — Qwen3-1.7B", "qwen3-base", prompt)
    show("LOOPTOR — fine-tuned", "looptor", prompt)
