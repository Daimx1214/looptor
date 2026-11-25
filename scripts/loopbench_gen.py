#!/usr/bin/env python3
"""LoopBench generator — frozen design 25 Nov 2026.

Sets: train_pool (data generation only), test (unseen), stress (loop-tempting).
Open-ended pools are INDEX-PARTITIONED between train and test, so no prompt
text ever appears in both. Math/counting/logic are parameterized (unique).
Each item: {id, set, category, prompt, gold, check}
"""
import json, random, math, os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "loopbench")
NAMES = ["Ahmed", "Fatima", "Bilal", "Ayesha", "Usman", "Zainab", "Hassan", "Maryam",
         "Ali", "Sara", "Omar", "Hira", "Danish", "Noor", "Kamran", "Iqra"]


def math_items(rng, n):
    out = []
    while len(out) < n:
        kind = rng.randrange(7)
        if kind == 0:
            d1, t1 = rng.randrange(60, 400, 20), rng.randrange(1, 6)
            d2, t2 = rng.randrange(40, 300, 20), rng.randrange(1, 5)
            if (d1 + d2) % (t1 + t2): continue
            gold = (d1 + d2) // (t1 + t2)
            p = (f"A bus travels {d1} km in {t1} hours, then {d2} km in {t2} hours. "
                 f"What is its average speed for the whole journey in km/h? "
                 f"Reason step by step and verify your answer before finishing.")
        elif kind == 1:
            x = rng.randrange(2, 30); a = rng.randrange(2, 9); b = a * x + rng.randrange(1, 20)
            gold = x
            p = (f"Solve for x: {a}x + {b - a * x} = {b}. Show each step, then double-check "
                 f"by substituting your answer back into the equation.")
        elif kind == 2:
            price = rng.randrange(500, 5000, 100); pct = rng.choice([10, 20, 25, 30, 40, 50])
            gold = price * (100 - pct) // 100
            p = (f"A jacket costs Rs {price}. It is sold at a discount of {pct}%. "
                 f"What is the final price in rupees? Work it out carefully step by step.")
        elif kind == 3:
            a = rng.choice([4, 5, 6, 8, 10, 12]); b = rng.choice([3, 4, 6, 8, 12])
            days = (a * b) / (a + b)
            if days != int(days): continue
            gold = int(days)
            p = (f"{rng.choice(NAMES)} can paint a house in {a} days and {rng.choice(NAMES)} "
                 f"can paint it in {b} days. Working together, in how many days will they finish? "
                 f"Explain your reasoning fully.")
        elif kind == 4:
            a, b = rng.randrange(4, 25), rng.randrange(4, 25)
            gold = a * b // math.gcd(a, b)
            p = (f"Two buses leave a station together. One returns every {a} minutes and the "
                 f"other every {b} minutes. After how many minutes will they next be at the "
                 f"station together? Show your working.")
        elif kind == 5:
            marks = [rng.randrange(40, 100) for _ in range(4)]
            if sum(marks) % 4: continue
            gold = sum(marks) // 4
            p = (f"A student scored {marks[0]}, {marks[1]}, {marks[2]} and {marks[3]} in four "
                 f"subjects. What is the average score? Compute it step by step and check your sum twice.")
        else:
            cost = rng.randrange(200, 2000, 50); pct = rng.choice([10, 15, 20, 25, 30])
            gold = cost * pct // 100
            p = (f"A shopkeeper buys a phone for Rs {cost} and sells it at a profit of {pct}%. "
                 f"How much profit in rupees does he make? Show the calculation in detail.")
        out.append({"category": "math", "prompt": p, "gold": str(gold), "check": "contains"})
    return out


def counting_items(rng, n):
    out = []
    while len(out) < n:
        kind = rng.randrange(4)
        if kind == 0:
            a, b = rng.randrange(1, 30), rng.randrange(31, 90)
            gold = (b - a + 1)
            p = (f"List every integer from {a} to {b} and then state how many integers there are in total. "
                 f"Be careful not to miss any or repeat any.")
        elif kind == 1:
            word = rng.choice(["banana", "mississippi", "bookkeeper", "committee", "balloon", "success"])
            letter = rng.choice(sorted(set(word)))
            gold = word.count(letter)
            p = (f"How many times does the letter '{letter}' appear in the word '{word}'? "
                 f"Go through the word letter by letter and count carefully, then recount to be sure.")
        elif kind == 2:
            k = rng.randrange(3, 9); upto = k * rng.randrange(8, 15)
            gold = upto // k
            p = (f"How many multiples of {k} are there between 1 and {upto} (including {upto} if it is a "
                 f"multiple)? List them all and give the total count.")
        else:
            a = rng.randrange(5, 40); b = a + rng.randrange(10, 30)
            gold = (a + b) * (b - a + 1) // 2
            p = (f"What is the sum of all integers from {a} to {b}? You may add them in groups, "
                 f"but verify the total by a second method before answering.")
        out.append({"category": "counting", "prompt": p, "gold": str(gold), "check": "contains"})
    return out


def logic_items(rng, n):
    out = []
    while len(out) < n:
        kind = rng.randrange(3)
        if kind == 0:
            now = rng.randrange(8, 20); yrs = rng.randrange(3, 12)
            gold = now + yrs
            p = (f"{rng.choice(NAMES)} is {now} years old. How old will they be in {yrs} years? "
                 f"Also explain how old they were {yrs // 2} years ago, step by step.")
            out.append({"category": "logic", "prompt": p, "gold": str(gold), "check": "contains"})
        elif kind == 1:
            trio = rng.sample(NAMES, 3)
            p = (f"{trio[0]} is taller than {trio[1]}. {trio[1]} is taller than {trio[2]}. "
                 f"Who is the shortest of the three? Explain the chain of comparisons carefully.")
            out.append({"category": "logic", "prompt": p, "gold": trio[2], "check": "contains"})
        else:
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            i = rng.randrange(7); k = rng.randrange(3, 25)
            gold = days[(i + k) % 7]
            p = (f"Today is {days[i]}. What day of the week will it be exactly {k} days from now? "
                 f"Count forward carefully day by day if you need to.")
            out.append({"category": "logic", "prompt": p, "gold": gold, "check": "contains"})
    return out


CODING = [
    "Write a Python function that returns the second largest number in a list. Explain each line of your code in detail after writing it.",
    "Write a JavaScript function that checks whether a string is a palindrome, ignoring spaces and case. Walk through two examples step by step.",
    "Write a Python function to compute the nth Fibonacci number iteratively. Explain why the iterative version is better than recursion here.",
    "Write a C# method that counts the vowels in a given string. Describe how it handles uppercase and lowercase letters.",
    "Write a Python function that merges two sorted lists into one sorted list without using sort(). Explain the two-pointer idea in detail.",
    "Write a Java function that reverses the words in a sentence. Show the output for 'the quick brown fox' and explain each step.",
    "Write a Python function that finds all prime numbers up to n using the sieve of Eratosthenes. Explain the marking process carefully.",
    "Write a JavaScript function that flattens a nested array one level deep. Give two test cases and trace through them.",
    "Write a Python function that validates an email address with a regular expression. Explain each part of the pattern.",
    "Write a C++ function that binary-searches a sorted array and returns the index or -1. Trace it on the array [2, 5, 8, 12, 16, 23] searching for 12.",
    "Write a Python function that counts how many times each word appears in a paragraph. Explain your choice of data structure.",
    "Write a JavaScript function that debounces another function by 300 milliseconds. Explain the role of the timer in detail.",
    "Write a Python function that converts a Roman numeral string to an integer. Trace it on 'MCMXCIV' step by step.",
    "Write a C# method that finds the first non-repeating character in a string, or reports that there is none. Explain the counting approach.",
    "Write a Python function that checks whether two strings are anagrams of each other. Give three test cases and trace one of them.",
    "Write a Java function that computes the greatest common divisor of two numbers using Euclid's algorithm. Trace it for 48 and 36.",
    "Write a Python function that rotates a list to the right by k positions without slicing tricks. Explain the reversal method.",
    "Write a JavaScript function that removes duplicate values from an array while keeping the original order. Explain the data structure you use.",
    "Write a Python function that returns the longest word in a sentence, and the first one if there is a tie. Trace it on an example.",
    "Write a C++ function that checks whether a linked list has a cycle. Explain the fast and slow pointer idea in detail.",
]
EXPLAIN = [
    "Explain how photosynthesis works, in a way a 12-year-old can understand, covering every stage in order.",
    "Explain the difference between TCP and UDP, with examples of where each one is used and why.",
    "Explain why the sky appears blue during the day but orange near sunset. Go through the physics step by step.",
    "Explain how a refrigerator keeps food cold, describing the full cycle of the refrigerant in detail.",
    "Explain the water cycle from evaporation to rainfall, naming every stage and what drives it.",
    "Explain how vaccines train the immune system, step by step, without using technical jargon where possible.",
    "Explain why we see different phases of the Moon during a month, describing the positions involved.",
    "Explain how interest on a savings account is calculated, with a worked example using Rs 10,000 at 8% for 2 years.",
    "Explain the rules of cricket to someone who only knows football, covering batting, bowling and how a team wins.",
    "Explain how GPS knows your location, describing the role of satellites and timing signals in detail.",
    "Explain why aeroplanes stay in the air, covering lift, thrust, drag and weight in balance.",
    "Explain how antibiotics work against bacteria and why they do not work on viruses.",
    "Explain what happens inside a volcano before and during an eruption, stage by stage.",
    "Explain how a rainbow forms after rain, including the role of sunlight and water droplets.",
    "Explain the difference between weather and climate with three clear examples of each.",
    "Explain how earthquakes are measured and what the Richter scale numbers actually mean.",
]
PLANNING = [
    "Plan a 3-day study timetable for a student who has exams in maths, physics and English in 10 days. Break each day into sessions with breaks.",
    "Plan how a small bakery can introduce online ordering in 4 weeks with no extra staff. List week-by-week actions.",
    "Plan a one-day trip in Lahore for a family of five with a budget of Rs 15,000, including transport, food and two sights.",
    "Plan the steps to organise a school science fair with 20 projects in one month, including roles and a simple timeline.",
    "Plan a beginner's 6-week exercise routine for someone who can train 3 days a week at home with no equipment.",
    "Plan how to move a family's belongings from Multan to Lahore in 5 days, listing tasks day by day with packing order.",
    "Plan a small vegetable garden for a 10 by 20 foot plot through one season, month by month.",
    "Plan a birthday party for 30 children with a budget of Rs 25,000, covering venue, food, games and timings.",
    "Plan the launch of a small home-made pickle business in 30 days, week by week, including licences and selling channels.",
    "Plan a revision strategy for learning 500 English vocabulary words in 25 days, with daily targets and review cycles.",
    "Plan a two-day community clean-up drive for a neighbourhood of 200 homes, with teams, supplies and a schedule.",
    "Plan how a tuition centre can shift evening classes online during a month of load-shedding, week by week.",
    "Plan a 14-day meal plan for a family of four on a tight budget that avoids repeating the same dinner twice.",
    "Plan the setting up of a small home library of 300 books in 3 weeks, including sorting, shelving and a catalogue.",
    "Plan a school charity bake sale that must raise Rs 50,000 in one day, with pricing, staffing and promotion steps.",
    "Plan a 5-day road trip from Multan to Hunza for two people, with daily stops, fuel stops and rough costs.",
]


def open_items(rng, n, pool, category, lo, hi):
    """Draw from pool[lo:hi] only — partitions keep train/test disjoint."""
    sub = pool[lo:hi]
    return [{"category": category, "prompt": rng.choice(sub), "gold": None, "check": None}
            for _ in range(n)]


def stress_items(rng, n):
    templates = [
        ("Count from 1 to 60, writing each number and next to it whether it is odd or even. "
         "Then verify the whole list a second time from the start before giving the total count of even numbers.", "30"),
        ("Write out the 7 times table from 7x1 to 7x30. After each line, double-check the "
         "multiplication by adding 7 repeatedly. Then state the value of 7x30.", "210"),
        ("Explain how to boil an egg. Be extremely thorough: describe every micro-step, then "
         "repeat the full explanation again in different words, then summarise it a third time.", None),
        ("List the first 40 prime numbers. For each one, briefly argue why it has no divisors. "
         "Then go back and re-verify each of the 40 again one by one.", "173"),
        ("A farmer has 17 sheep and all but 9 run away. How many sheep are left? Think very "
         "carefully, consider every possible interpretation of the question, re-read it several "
         "times and check each interpretation before answering.", "9"),
        ("Write a Python function to sort a list. Then rewrite it in a second way. Then rewrite "
         "it a third way. Compare all three versions line by line, then combine the best parts "
         "and write the final version again in full.", None),
        ("Translate the sentence 'The quick brown fox jumps over the lazy dog' into Urdu, then "
         "back into English, then into Urdu again, then back into English again. Show every version "
         "and comment on what changed at each step.", None),
        ("What is 15% of 240? Calculate it by three different methods, verify each method with a "
         "fourth method, and only then give the final answer.", "36"),
        ("Describe the plot of a story about a cat, in exactly this repeating structure: one "
         "sentence about the cat, one sentence about the weather, one sentence about the cat, one "
         "sentence about the weather, for at least 12 sentences.", None),
        ("Starting from 1000, subtract 7 again and again, writing every result, until you reach a "
         "number below 950. Then check the whole chain backwards by adding 7 each time.", "944"),
    ]
    out = []
    for i in range(n):
        p, gold = templates[i % len(templates)]
        out.append({"category": "stress", "prompt": p, "gold": gold,
                    "check": "contains" if gold else None})
    return out


def assemble(name, seed, parts):
    rng = random.Random(seed)
    items = []
    for part in parts:
        items += part(rng)
    rng.shuffle(items)
    for i, it in enumerate(items, 1):
        it.update({"id": f"{name}-{i:03d}", "set": name})
    return items


def main():
    os.makedirs(OUT, exist_ok=True)
    cut_c, cut_e, cut_p = 12, 10, 10  # train gets pool[:cut], test gets pool[cut:]
    sets = {
        "train_pool": assemble("train", 101, [
            lambda r: math_items(r, 200), lambda r: counting_items(r, 120),
            lambda r: logic_items(r, 80),
            lambda r: open_items(r, 80, CODING, "coding", 0, cut_c),
            lambda r: open_items(r, 60, EXPLAIN, "explain", 0, cut_e),
            lambda r: open_items(r, 60, PLANNING, "planning", 0, cut_p)]),
        "test": assemble("test", 202, [
            lambda r: math_items(r, 80), lambda r: counting_items(r, 55),
            lambda r: logic_items(r, 45),
            lambda r: open_items(r, 8, CODING, "coding", cut_c, len(CODING)),
            lambda r: open_items(r, 6, EXPLAIN, "explain", cut_e, len(EXPLAIN)),
            lambda r: open_items(r, 6, PLANNING, "planning", cut_p, len(PLANNING))]),
        "stress": stress_items(random.Random(303), 100),
    }
    for i, it in enumerate(sets["stress"], 1):
        it.update({"id": f"stress-{i:03d}", "set": "stress"})
    # Leakage fix-up: test is sacred. Drop any test prompt that collides with
    # train (parameterized templates can coincide), dedupe test, then top up
    # with fresh parameterized items until back to 200 with zero overlap.
    train_prompts = {it["prompt"] for it in sets["train_pool"]}
    seen, clean = set(), []
    for it in sets["test"]:
        if it["prompt"] in train_prompts or it["prompt"] in seen:
            continue
        seen.add(it["prompt"]); clean.append(it)
    rng = random.Random(999)
    while len(clean) < 200:
        for fn, cnt in ((math_items, 14), (counting_items, 8), (logic_items, 6)):
            for it in fn(rng, cnt):
                if it["prompt"] not in train_prompts and it["prompt"] not in seen:
                    seen.add(it["prompt"]); clean.append(it)
    sets["test"] = clean[:200]
    for i, it in enumerate(sets["test"], 1):
        it.update({"id": f"test-{i:03d}", "set": "test"})
    for name, items in sets.items():
        with open(os.path.join(OUT, f"{name}.jsonl"), "w") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
        cats = {}
        for it in items: cats[it["category"]] = cats.get(it["category"], 0) + 1
        print(name, len(items), cats)
    prompts = {name: {it["prompt"] for it in items} for name, items in sets.items()}
    print("train∩test prompt overlap:", len(prompts["train_pool"] & prompts["test"]))
    print("train∩stress prompt overlap:", len(prompts["train_pool"] & prompts["stress"]))
    print("test∩stress prompt overlap:", len(prompts["test"] & prompts["stress"]))


if __name__ == "__main__":
    main()
