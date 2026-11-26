# LoopTor — Think. Don't Loop.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Base model](https://img.shields.io/badge/Base-Qwen3--1.7B-blue.svg)](https://huggingface.co/Qwen/Qwen3-1.7B)
[![Format](https://img.shields.io/badge/Format-GGUF%20Q4__K__M-orange.svg)](https://huggingface.co/Daimx1214/looptor-1.7b)
[![Runs locally](https://img.shields.io/badge/Runs%20locally-Ollama-purple.svg)](https://ollama.com)

**LoopTor** is a LoRA fine-tune of **Qwen3-1.7B** that measurably reduces
*thought loops* — the failure mode where a small reasoning model repeats
itself in its thinking, re-verifies steps it already settled, and sometimes
hits the token limit without ever producing a final answer.

Built by team **NoobDevelopers** for the **Qwen Local Hackathon 2026**
(Qwen Pakistan).

| | |
|---|---|
| 🤗 **Model (GGUF)** | [huggingface.co/Daimx1214/looptor-1.7b](https://huggingface.co/Daimx1214/looptor-1.7b) |
| 🎥 **Demo video** | [youtube.com/watch?v=PR28WXYgqDA](https://www.youtube.com/watch?v=PR28WXYgqDA) |
| 📥 **Run it** | `ollama run hf.co/Daimx1214/looptor-1.7b` |

---

## Results

Both models were evaluated on the **same unseen prompts**, with the **same
decoding settings** and a loop detector whose thresholds were **frozen before
any results were seen**. Full machine-readable scores:
[`results/score_base.json`](results/score_base.json) ·
[`results/score_tuned.json`](results/score_tuned.json)

### Test set — 200 unseen prompts

| Metric | Qwen3-1.7B (base) | LoopTor | Change |
|---|---:|---:|---:|
| Loop rate | 56.0% (95% CI 49.5–63.0) | **41.5%** (CI 35.0–48.5) | **−14.5 pts** |
| Accuracy | 90.3% | **93.6%** | +3.3 pts |
| Non-termination rate | 10.0% | **4.5%** | −5.5 pts |
| Median output tokens | 1,295 | **1,170** | −125 |

### Stress set — 100 adversarial loop-trap prompts

| Metric | Qwen3-1.7B (base) | LoopTor | Change |
|---|---:|---:|---:|
| Loop rate | 85.0% (CI 78.0–91.0) | **77.0%** (CI 69.0–85.0) | **−8.0 pts** |
| Accuracy | 28.3% | **33.3%** | +5.0 pts |
| Non-termination rate | 52.0% | **39.0%** | −13.0 pts |

### Loops by category (test set)

| Category | Base | LoopTor |
|---|---:|---:|
| Logic | 29/45 | **14/45** |
| Counting | 47/48 | **36/48** |
| Math | 26/93 | 24/93 |
| Coding | 6/6 | 6/6 |
| Planning | 3/4 | 3/4 |
| Explain | 1/4 | **0/4** |

### A real before/after pair

Prompt `test-017`: *"Ahmed is taller than Omar. Omar is taller than Fatima.
Who is the shortest of the three?"* (gold answer: Fatima)

- **Base:** 665 tokens — thinking circles back on the same comparisons —
  detector verdict **LOOP**.
- **LoopTor:** 583 tokens — one clean chain of comparisons, correct final
  answer — verdict **CLEAN**.

Raw outputs: [`results/pair-test-017/`](results/pair-test-017/)

---

## The problem

Small reasoning models are usually evaluated on whether the final answer is
right. In everyday local use, a different failure dominates: the model
*thinks in circles*. It restates the same step, re-checks a result it already
verified, and keeps going until the token budget runs out — slowly, and
sometimes without answering at all. On our base-model measurement this was
not rare: **56% of ordinary reasoning prompts looped, and 52% of stress
prompts never terminated.**

## How LoopTor was built

### 1. LoopBench — a frozen benchmark

900 prompts in three disjoint sets (zero overlap, verified programmatically):

- **Train pool** — 600 prompts the data generation could draw from
- **Test** — 200 unseen prompts (logic, math, counting, coding, planning, explain)
- **Stress** — 100 unseen adversarial prompts designed to trap models into
  repetition and endless verification

The **loop detector** ([`loopbench/loop_detect.py`](loopbench/loop_detect.py))
flags a response as a LOOP when any of these fire (code blocks are masked):

- an 8-gram repeats 3+ times, **or**
- a sentence of 10+ words repeats 3+ times, **or**
- the response never terminates with a final answer.

The detector was validated on 20 hand-written cases (20/20) and its
thresholds were frozen before evaluation.

### 2. Training data — 1,263 self-built examples

| Part | Rows | What it teaches |
|---|---:|---|
| Best-of-N traces | 215 | Sample the base model N times per prompt; keep only the *shortest correct, loop-free* reasoning traces |
| Concise traces | 700 | Programmatically generated short, complete reasoning |
| Loop-recovery | 240 | Recognize a repeated pattern mid-thinking and break out toward the answer |
| Direct answers | 108 | Trivial questions get short answers, not essays |

No external datasets; everything is self-generated or programmatic, so the
data is fully licensed for this use. The committed
[`data/train.jsonl`](data/train.jsonl) holds the 1,048 programmatic rows;
the Best-of-N rows are reproducible with
[`scripts/gen_bestofn.py`](scripts/gen_bestofn.py) and were merged for the
final training run.

### 3. Fine-tuning

- **Method:** LoRA (rank 16, alpha 32, all linear layers), loss on responses only
- **Framework:** Unsloth · **Epochs:** 3 · **LR:** 2e-4 · **Max length:** 1,024
- **Hardware:** free Kaggle notebook, 2× NVIDIA T4 (417 steps)
- **Export:** GGUF **Q4_K_M** (1.1 GB) + LoRA adapter, published on Hugging Face
- **Accuracy guard:** a checkpoint that traded away accuracy for fewer loops
  would have been rejected — LoopTor instead improved both.

### 4. Evaluation discipline

Same prompts, same decoding, same detector for base and tuned. Headline
claims rest only on the full 200/100-prompt runs — single generations vary,
and we do not cherry-pick them.

---

## Quickstart

### Run the model (Ollama)

```bash
ollama run hf.co/Daimx1214/looptor-1.7b
```

That is the whole setup: a 1.1 GB download, then it runs fully locally and
offline on a normal laptop CPU.

### Try the demos in this repo

```bash
# CLI: base vs LoopTor side by side on LoopBench prompts
python demo/looptor_demo.py

# Web UI: side-by-side comparison in the browser
python demo/looptor_web.py
```

(Both expect the `qwen3-base` and `looptor-tuned` models in your local
Ollama; see the Modelfile in the Hugging Face repo.)

### Reproduce the benchmark

```bash
python scripts/loopbench_gen.py     # regenerate LoopBench (600/200/100)
python scripts/test_detector.py     # detector unit cases — must pass 20/20
python scripts/run_eval.py          # run a model over the test/stress sets
python scripts/score_loops.py       # loop rate, accuracy, tokens, 95% CI
```

---

## Repository structure

```
looptor/
├── README.md                  # this file
├── LICENSE                    # MIT
├── loopbench/                 # the frozen benchmark
│   ├── loop_detect.py         #   the loop detector (frozen thresholds)
│   ├── train_pool.jsonl       #   600 prompts
│   ├── test.jsonl             #   200 unseen prompts
│   └── stress.jsonl           #   100 adversarial prompts
├── data/
│   ├── train.jsonl            # 1,048 programmatic training rows
│   └── stats.json             # dataset composition (final run: 1,263 rows)
├── scripts/
│   ├── loopbench_gen.py       # benchmark generator (zero set overlap)
│   ├── gen_bestofn.py         # Best-of-N shortest-correct trace sampler
│   ├── build_dataset.py       # assembles the 4-part training set
│   ├── run_eval.py            # resumable evaluation runner (Ollama API)
│   ├── score_loops.py         # scoring: loops, accuracy, tokens, CI
│   └── test_detector.py       # 20 hand-written detector cases
├── demo/
│   ├── looptor_demo.py        # CLI side-by-side demo
│   └── looptor_web.py         # web side-by-side demo
├── results/
│   ├── score_base.json        # full base-model scores
│   ├── score_tuned.json       # full LoopTor scores
│   └── pair-test-017/         # raw before/after outputs for one prompt
└── looptor_colab.ipynb        # early training notebook (final run: Kaggle)
```

## Limitations — stated honestly

- **Loops are reduced, not eliminated.** 77% of the hardest stress traps
  still loop. Those prompts are engineered to trap small models, and a 1.7B
  model has real limits; the measured improvement, not a cure, is the claim.
- **Single-run variance is real.** Any one generation can differ from the
  rates above; that is why the headline numbers come from 300 prompts, not
  anecdotes.
- **Scope:** English reasoning prompts of the kinds in LoopBench. Behaviour
  on other languages, long-form writing, or tool use was not measured.

## Team

**NoobDevelopers**

- **Daim Ali** (Lead) — [@Daimx1214](https://github.com/Daimx1214)
- **Hassan Raza** — [@hassanra12144](https://github.com/hassanra12144)

## License

MIT — see [LICENSE](LICENSE). The base model, Qwen3-1.7B, is by the Qwen
team (Alibaba Cloud) under its own license; LoopTor's adapter and GGUF
quantization are derived from it for this hackathon project.

## Acknowledgments

Thanks to **Junaid Shaukat** and **Qwen Pakistan** for organizing the Qwen
Local Hackathon 2026, and to the Qwen team for releasing strong small open
models that make fully local AI practical.
