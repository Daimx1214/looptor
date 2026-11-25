# LoopTor — "Socho, phanso mat." (Think. Don't loop.)

A LoRA fine-tune of **Qwen3-1.7B** that fixes Qwen's #1 user complaint:
**thought loops** — the model repeating itself in its thinking, re-verifying
settled steps, and often hitting the token limit without ever answering.

Built for the **Qwen Local Hackathon 2026** by Daim Ali (solo).

## Approach (SEER-style, self-generated data)

1. **LoopBench** — a frozen benchmark (train pool 600 / unseen test 200 /
   stress 100) plus a programmatic loop detector (repeated 8-grams /
   repeated sentences / non-termination). Detector thresholds were fixed
   before any results were seen.
2. **Measure the base model first** — loop rate, non-termination rate,
   output tokens, task accuracy.
3. **Best-of-N data** — sample the base model N=6 times per training prompt;
   keep only the *shortest correct, loop-free* traces, plus programmatic
   concise traces, loop-recovery examples, and direct-answer examples.
4. **LoRA fine-tune** on those traces, then re-measure on the *same* unseen
   sets with the *same* decoding. Accuracy guard: a run that trades away
   more than 5 accuracy points is rejected.

## Files

- `loopbench_gen.py` — generates LoopBench (zero train/test prompt overlap)
- `loop_detect.py` — the loop detector (spec: Master Guide Appendix A)
- `test_detector.py` — 20 hand-written cases, must pass 20/20
- `run_eval.py` — runs a model over LoopBench via the Ollama API (resumable)
- `score_loops.py` — loop rate, non-termination, tokens, accuracy, 95% CI
- `loopbench/` — the benchmark itself (prompts + gold answers)

## Status

- [x] LoopBench generated (600/200/100), zero cross-set overlap
- [x] Detector verified 20/20 on hand cases
- [ ] Base-model before-numbers (local subset running; full on Colab)
- [x] Dataset builder ready (1,048 rows pre-BoN; ~3,000 after Best-of-N)
- [ ] Training (Colab notebook ready: looptor_colab.ipynb)
- [ ] GGUF + local Ollama verification
