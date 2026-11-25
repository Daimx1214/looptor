#!/usr/bin/env python3
"""LoopTor side-by-side web demo (Guide Ch. 14 + Ch. 22 Qwen violet theme).
Local only: http://127.0.0.1:8770 — one prompt, two panels (base vs tuned),
each with tokens, time and the loop detector's verdict.
"""
import json, os, sys, time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "loopbench"))
from loop_detect import detect

API = "http://127.0.0.1:11434/api/chat"

PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>LoopTor — Think. Don't loop.</title>
<style>
 body{background:#1E1B4B;color:#EEF0FF;font-family:system-ui,sans-serif;margin:0;padding:24px}
 h1{color:#fff} h1 span{color:#8f8bf5} .tag{color:#b9b7f9;margin-top:-10px}
 textarea{width:100%;height:90px;border-radius:10px;border:2px solid #615CED;padding:10px;font-size:15px}
 button{background:#615CED;color:#fff;border:0;padding:12px 28px;border-radius:10px;font-size:16px;cursor:pointer;margin:12px 0}
 .row{display:flex;gap:16px;flex-wrap:wrap}
 .panel{flex:1;min-width:320px;background:#EEF0FF;color:#1E1B4B;border-radius:12px;padding:16px}
 .panel h2{margin:0 0 6px} .badge{float:right;padding:4px 10px;border-radius:20px;color:#fff;font-size:13px}
 .ok{background:#0E9F8E} .bad{background:#DC2626} .warn{background:#D97706}
 pre{white-space:pre-wrap;font-size:13px;max-height:420px;overflow:auto;background:#fff;border-radius:8px;padding:10px}
 .meta{font-size:13px;color:#4338CA;font-weight:600}
</style></head><body>
<h1>LoopTor <span>· Socho, phanso mat.</span></h1>
<p class="tag">Qwen3-1.7B, fine-tuned to think — without looping. 100% local (Ollama).</p>
<textarea id="p">Count from 1 to 60, writing each number and next to it whether it is odd or even. Then verify the whole list a second time from the start before giving the total count of even numbers.</textarea>
<button onclick="run()">Run both models</button>
<div class="row">
 <div class="panel"><h2>Base — Qwen3-1.7B <span id="bb" class="badge warn">waiting</span></h2>
 <div class="meta" id="bm"></div><pre id="bt">—</pre></div>
 <div class="panel"><h2>LoopTor — fine-tuned <span id="tb" class="badge warn">waiting</span></h2>
 <div class="meta" id="tm"></div><pre id="tt">—</pre></div>
</div>
<script>
async function run(){
  for (const p of ['b','t']){ document.getElementById(p+'b').textContent='running…';
    document.getElementById(p+'b').className='badge warn'; document.getElementById(p+'t').textContent='—'; }
  const r = await fetch('/run', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({prompt: document.getElementById('p').value})});
  const d = await r.json();
  for (const [p, res] of [['b', d.base], ['t', d.tuned]]){
    const b = document.getElementById(p+'b');
    if (!res){ b.textContent='model not available'; continue; }
    b.textContent = res.loop ? 'LOOP DETECTED' : 'loop-free';
    b.className = 'badge ' + (res.loop ? 'bad' : 'ok');
    document.getElementById(p+'m').textContent = res.tokens + ' tokens · ' + res.secs + 's';
    document.getElementById(p+'t').textContent = res.text;
  }
}
</script></body></html>"""


def run_model(model, prompt, max_tokens=2048):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "stream": False, "think": True,
            "options": {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "num_predict": max_tokens}}
    req = urllib.request.Request(API, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=3600) as r:
        resp = json.loads(r.read())
    msg = resp.get("message", {})
    full = ((msg.get("thinking", "") or "") + "\n" + (msg.get("content", "") or "")).strip()
    d = detect(full, hit_token_cap=resp.get("done_reason") == "length",
               has_final_answer=bool((msg.get("content") or "").strip()))
    return {"text": full, "tokens": resp.get("eval_count", 0),
            "secs": round(time.time() - t0, 1), "loop": d["loop"]}


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(PAGE.encode())

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        prompt = json.loads(self.rfile.read(n))["prompt"]
        out = {}
        for key, model in (("base", "qwen3-base"), ("tuned", "looptor")):
            try:
                out[key] = run_model(model, prompt)
            except Exception:
                out[key] = None
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(out).encode())

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("LoopTor demo at http://127.0.0.1:8770")
    HTTPServer(("127.0.0.1", 8770), H).serve_forever()
