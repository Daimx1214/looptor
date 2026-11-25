#!/usr/bin/env python3
"""Build the LoopTor training dataset — 4 parts (Guide Ch. 10).

Part 1 (~1,800): Best-of-N selection from data/bestofn_raw.jsonl —
  shortest loop-free, gold-correct sample per train prompt.
Part 2 (~700): programmatic concise traces (plan -> steps -> final).
Part 3 (~300): loop-recovery traces (one repeat, then notice-and-exit).
Part 4 (~200): direct-answer examples (tiny think + immediate answer).

Output: data/train.jsonl in {"messages":[...]} format with <think> blocks
inside the assistant content (Unsloth Qwen3 SFT recipe), data/stats.json.
Leakage: any generated prompt colliding with test/stress is dropped.
"""
import json, math, os, random, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "loopbench"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loop_detect import detect
from score_loops import gold_hit

rng = random.Random(777)
NAMES = ["Ahmed", "Fatima", "Bilal", "Ayesha", "Usman", "Zainab", "Hassan", "Maryam"]


def msg(user, think, answer):
    content = f"<think>\n{think}\n</think>\n\n{answer}" if think else answer
    return {"messages": [{"role": "user", "content": user},
                         {"role": "assistant", "content": content}]}


# ---------------- Part 1: Best-of-N selection ----------------
def part1():
    path = os.path.join(ROOT, "data", "bestofn_raw.jsonl")
    if not os.path.exists(path):
        print("part1: no bestofn_raw.jsonl yet, skipping")
        return []
    by_id = {}
    for l in open(path):
        r = json.loads(l)
        by_id.setdefault(r["id"], []).append(r)
    out = []
    for pid, samples in by_id.items():
        good = []
        for s in samples:
            full = (s["thinking"] + "\n" + s["content"]).strip()
            d = detect(full, hit_token_cap=s["done_reason"] == "length",
                       has_final_answer=bool(s["content"].strip()))
            if d["loop"] or not s["content"].strip():
                continue
            if s.get("check"):
                if not gold_hit(s.get("gold"), s["content"]):
                    continue
            good.append(s)
        if not good:
            continue
        best = min(good, key=lambda s: s["tokens"])
        think = best["thinking"].strip()
        out.append(msg(best["prompt"], think, best["content"].strip()))
    print(f"part1: {len(out)} selected from {len(by_id)} prompts")
    return out


# ---------------- Part 2: concise traces ----------------
def gen_problem():
    """Return (prompt, think, answer) with a fully worked concise trace."""
    kind = rng.randrange(9)
    if kind == 0:
        d1, t1 = rng.randrange(40, 400, 20), rng.randrange(1, 6)
        d2, t2 = rng.randrange(40, 300, 20), rng.randrange(1, 5)
        if (d1 + d2) % (t1 + t2): return None
        v = (d1 + d2) // (t1 + t2)
        return (f"A train travels {d1} km in {t1} hours, then {d2} km in {t2} hours. "
                f"What is its average speed for the whole journey in km/h?",
                f"Plan: total distance / total time.\nDistance = {d1} + {d2} = {d1+d2} km. "
                f"Time = {t1} + {t2} = {t1+t2} h.\nAverage speed = {d1+d2} / {t1+t2} = {v} km/h.",
                f"Average speed = {v} km/h.")
    if kind == 1:
        x = rng.randrange(2, 40); a = rng.randrange(2, 9); c = rng.randrange(1, 25)
        b = a * x + c
        return (f"Solve for x: {a}x + {c} = {b}.",
                f"Plan: isolate x.\n{a}x = {b} - {c} = {b-c}.\nx = {b-c} / {a} = {x}.",
                f"x = {x}.")
    if kind == 2:
        price = rng.randrange(400, 6000, 100); pct = rng.choice([10, 20, 25, 30, 40, 50])
        v = price * (100 - pct) // 100
        return (f"A shirt costs Rs {price} and is sold at a discount of {pct}%. What is the final price?",
                f"Plan: subtract the discount from the price.\nDiscount = {pct}% of {price} = Rs {price*pct//100}.\n"
                f"Final price = {price} - {price*pct//100} = Rs {v}.",
                f"Final price = Rs {v}.")
    if kind == 3:
        a, b = rng.randrange(4, 30), rng.randrange(4, 30)
        v = a * b // math.gcd(a, b)
        return (f"Two bells toll every {a} minutes and every {b} minutes. They toll together now. "
                f"After how many minutes will they toll together again?",
                f"Plan: find the LCM of {a} and {b}.\nLCM({a}, {b}) = {v}.",
                f"They will toll together again after {v} minutes.")
    if kind == 4:
        a = rng.choice([4, 5, 6, 8, 10, 12]); b = rng.choice([3, 4, 6, 8, 12])
        if (a * b) % (a + b): return None
        v = (a * b) // (a + b)
        return (f"{rng.choice(NAMES)} can finish a job in {a} days and {rng.choice(NAMES)} in {b} days. "
                f"Working together, how many days do they need?",
                f"Plan: add the daily rates.\nRate together = 1/{a} + 1/{b} = {(a+b)}/{a*b} per day.\n"
                f"Days = {a*b} / {a+b} = {v}.",
                f"Together they need {v} days.")
    if kind == 5:
        marks = [rng.randrange(35, 100) for _ in range(4)]
        if sum(marks) % 4: return None
        v = sum(marks) // 4
        return (f"A student scored {marks[0]}, {marks[1]}, {marks[2]} and {marks[3]} in four tests. "
                f"What is the average score?",
                f"Plan: sum, then divide by 4.\nSum = {marks[0]} + {marks[1]} + {marks[2]} + {marks[3]} = {sum(marks)}.\n"
                f"Average = {sum(marks)} / 4 = {v}.",
                f"Average score = {v}.")
    if kind == 6:
        cost = rng.randrange(200, 3000, 50); pct = rng.choice([10, 15, 20, 25, 30])
        v = cost * pct // 100
        return (f"A trader buys goods for Rs {cost} and sells them at a profit of {pct}%. "
                f"How much profit does he make in rupees?",
                f"Plan: profit is {pct}% of the cost.\nProfit = {pct}% of {cost} = Rs {v}.",
                f"Profit = Rs {v}.")
    if kind == 7:
        a = rng.randrange(5, 50); b = a + rng.randrange(10, 40)
        v = (a + b) * (b - a + 1) // 2
        return (f"What is the sum of all integers from {a} to {b}?",
                f"Plan: use the pairing formula.\nCount = {b-a+1}. Sum = ({a} + {b}) x {b-a+1} / 2 = {v}.",
                f"Sum = {v}.")
    k = rng.randrange(3, 12); upto = k * rng.randrange(8, 16)
    v = upto // k
    return (f"How many multiples of {k} are there between 1 and {upto}?",
            f"Plan: divide the range by {k}.\nCount = {upto} / {k} = {v}.",
            f"There are {v} multiples of {k}.")


def part2(n=700):
    out, seen = [], set()
    while len(out) < n:
        g = gen_problem()
        if not g or g[0] in seen: continue
        seen.add(g[0])
        out.append(msg(g[0], g[1], g[2]))
    print(f"part2: {len(out)}")
    return out


# ---------------- Part 3: loop-recovery traces ----------------
RECOVERY = [
    "I have already established this above, so I will not repeat it. Moving on.",
    "This is the same result I just derived. No need to check it again; continuing.",
    "I notice I am repeating the previous step. It is already proven, so I will conclude.",
    "That check gives the same value as before, as expected. Proceeding to the answer.",
    "Repeating this will not change anything; the step is settled. Final step now.",
    "I already verified this earlier in this solution. Wrapping up.",
    "Same value again, which confirms it once and is enough. Moving to the conclusion.",
    "I was about to re-derive the same line. It is already done above, so I will finish.",
]


def part3(n=300):
    out, seen = [], set()
    while len(out) < n:
        g = gen_problem()
        if not g or g[0] in seen: continue
        seen.add(g[0])
        prompt, think, answer = g
        lines = think.split("\n")
        if len(lines) < 2: continue
        # repeat the last derivation line once, then recover and conclude
        repeated = lines[-1]
        new_think = "\n".join(lines + [repeated, rng.choice(RECOVERY)])
        out.append(msg(prompt, new_think, answer))
    print(f"part3: {len(out)}")
    return out


# ---------------- Part 4: direct answers ----------------
FACTS = [
    ("What is the capital of France?", "Paris."),
    ("What is the capital of Japan?", "Tokyo."),
    ("What is the capital of Australia?", "Canberra."),
    ("How many days are there in a leap year?", "366 days."),
    ("How many minutes are there in 3 hours?", "180 minutes."),
    ("At what temperature (Celsius) does water boil at sea level?", "100 degrees Celsius."),
    ("What is the chemical symbol for gold?", "Au."),
    ("How many sides does a hexagon have?", "Six sides."),
    ("What is the largest planet in our solar system?", "Jupiter."),
    ("How many continents are there on Earth?", "Seven."),
    ("What is the square root of 144?", "12."),
    ("How many grams are there in 2.5 kilograms?", "2500 grams."),
    ("What is 15% of 200?", "30."),
    ("How many hours are there in 4 days?", "96 hours."),
    ("What is the capital of Canada?", "Ottawa."),
    ("How many letters are there in the English alphabet?", "26."),
    ("What is the freezing point of water in Celsius?", "0 degrees Celsius."),
    ("How many metres are there in 3.5 kilometres?", "3500 metres."),
    ("What is the smallest prime number?", "2."),
    ("How many weeks are there in a year?", "52 weeks."),
]
TINY_THINKS = ["This is a direct fact.", "Straightforward.", "No working needed here.",
               "Simple recall.", "Direct answer."]


def part4(n=200):
    out = []
    facts = FACTS[:]
    while len(out) < n:
        kind = rng.randrange(3)
        if kind == 0 and facts:
            q, a = facts.pop(rng.randrange(len(facts)))
            out.append(msg(q, rng.choice(TINY_THINKS), a))
        elif kind == 1:
            a, b = rng.randrange(3, 99), rng.randrange(3, 99)
            op = rng.choice(["+", "-", "x"])
            v = a + b if op == "+" else (a - b if op == "-" else a * b)
            if v < 0: continue
            out.append(msg(f"What is {a} {op} {b}?", f"Quick calculation: {a} {op} {b} = {v}.", f"{v}."))
        else:
            a = rng.randrange(2, 30)
            out.append(msg(f"What is the square of {a}?", f"Quick calculation: {a} x {a} = {a*a}.", f"{a*a}."))
    print(f"part4: {len(out)}")
    return out


def main():
    parts = {"part1_bestofn": part1(), "part2_concise": part2(),
             "part3_recovery": part3(), "part4_direct": part4()}
    # leakage guard: drop any prompt that appears in test/stress
    banned = set()
    for s in ("test", "stress"):
        for l in open(os.path.join(ROOT, "loopbench", f"{s}.jsonl")):
            banned.add(json.loads(l)["prompt"].strip().lower())
    all_items, stats = [], {}
    seen_prompts = set()
    for name, items in parts.items():
        kept = []
        for it in items:
            p = it["messages"][0]["content"].strip().lower()
            if p in banned or p in seen_prompts:
                continue
            seen_prompts.add(p)
            kept.append(it)
        stats[name] = len(kept)
        all_items += kept
    rng.shuffle(all_items)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "train.jsonl"), "w") as f:
        for it in all_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    stats["total"] = len(all_items)
    with open(os.path.join(ROOT, "data", "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)
    print("stats:", stats)


if __name__ == "__main__":
    main()
